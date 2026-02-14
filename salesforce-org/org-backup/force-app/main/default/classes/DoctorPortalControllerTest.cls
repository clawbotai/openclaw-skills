@isTest
private class DoctorPortalControllerTest {

    @testSetup
    static void setup() {
        // Create Users
        Profile p = [SELECT Id FROM Profile WHERE Name='Standard User']; 
        
        // Doctor 1
        User u1 = new User(Alias = 'doc1', Email='doc1@testorg.com', 
            EmailEncodingKey='UTF-8', LastName='Testing', LanguageLocaleKey='en_US', 
            LocaleSidKey='en_US', ProfileId = p.Id, 
            TimeZoneSidKey='America/Los_Angeles', UserName='doc1@testorg.com');
        insert u1;

        // Doctor 2 (Attacker)
        User u2 = new User(Alias = 'doc2', Email='doc2@testorg.com', 
            EmailEncodingKey='UTF-8', LastName='Testing', LanguageLocaleKey='en_US', 
            LocaleSidKey='en_US', ProfileId = p.Id, 
            TimeZoneSidKey='America/Los_Angeles', UserName='doc2@testorg.com');
        insert u2;

        // Create Account
        Account acc = new Account(Name='Test Patient');
        insert acc;

        // Create Doctors linked to Users
        Doctor__c doc1 = new Doctor__c(Name='Doctor One', User__c=u1.Id, Medical_License__c='LIC-001');
        insert doc1;
        
        Doctor__c doc2 = new Doctor__c(Name='Doctor Two', User__c=u2.Id, Medical_License__c='LIC-002');
        insert doc2;

        // Create Models
        // Assuming Peer_Review__c needs Order__c
        Order o1 = new Order(AccountId=acc.Id, Doctor__c=doc1.Id, Status='Draft', EffectiveDate=Date.today());
        insert o1;

        // Create Peer Review assigned to Doc 1
        Peer_Review__c pr1 = new Peer_Review__c(Name='Review Target', Status__c='Pending', Reviewer__c=doc1.Id, Order__c=o1.Id);
        insert pr1;
    }

    @isTest
    static void testGetHubRecord_Doctor() {
        User u1 = [SELECT Id FROM User WHERE UserName='doc1@testorg.com'];
        
        System.runAs(u1) {
            DoctorPortalController.HubInfo hub = DoctorPortalController.getHubRecord();
            System.assertNotEquals(null, hub, 'Hub info should not be null for doctor');
            System.assertEquals('Doctor', hub.recordType, 'Should detect Doctor type');
        }
    }

    @isTest
    static void testSubmitVote_Success() {
        User u1 = [SELECT Id FROM User WHERE UserName='doc1@testorg.com'];
        Peer_Review__c pr = [SELECT Id FROM Peer_Review__c WHERE Name='Review Target' LIMIT 1];
        
        System.runAs(u1) {
            Test.startTest();
            DoctorPortalController.submitVote(pr.Id, '1');
            Test.stopTest();
            
            Peer_Review__c updatedPr = [SELECT Id, Status__c, Vote__c FROM Peer_Review__c WHERE Id = :pr.Id];
            System.assertEquals('Completed', updatedPr.Status__c, 'Status should be Completed');
            System.assertEquals('+1', updatedPr.Vote__c, 'Vote should be updated to +1');
        }
    }

    @isTest
    static void testSubmitVote_Expired() {
        User u1 = [SELECT Id FROM User WHERE UserName='doc1@testorg.com'];
        Doctor__c doc1 = [SELECT Id FROM Doctor__c WHERE User__c = :u1.Id LIMIT 1];
        Order o1 = [SELECT Id FROM Order WHERE Doctor__c = :doc1.Id LIMIT 1];

        // 1. Test Status = Expired
        Peer_Review__c expiredStatusPr = new Peer_Review__c(Name='Expired Status', Status__c='Expired', Reviewer__c=doc1.Id, Order__c=o1.Id);
        insert expiredStatusPr;

        System.runAs(u1) {
            Boolean caught = false;
            try {
                DoctorPortalController.submitVote(expiredStatusPr.Id, '1');
                System.assert(false, 'Should have thrown exception for Expired status');
            } catch (Exception e) {
                caught = true;
            }
            System.assert(caught, 'Should have caught exception for Expired status');
        }

        // 2. Test Expiration Date < Today
        Peer_Review__c expiredDatePr = new Peer_Review__c(Name='Expired Date', Status__c='Pending', Reviewer__c=doc1.Id, Order__c=o1.Id, Expiration_Date__c=Date.today().addDays(-1));
        insert expiredDatePr;

        System.runAs(u1) {
            Boolean caught = false;
            try {
                DoctorPortalController.submitVote(expiredDatePr.Id, '1');
                System.assert(false, 'Should have thrown exception for Past Expiration Date');
            } catch (Exception e) {
                caught = true;
            }
            System.assert(caught, 'Should have caught exception for Past Expiration Date');
        }
    }

    @isTest
    static void testSubmitVote_SecurityAttack() {
        // Doc 2 tries to vote on Doc 1's review
        User u2 = [SELECT Id FROM User WHERE UserName='doc2@testorg.com'];
        Peer_Review__c pr = [SELECT Id FROM Peer_Review__c WHERE Name='Review Target' LIMIT 1];
        
        System.runAs(u2) {
            Boolean exceptionCaught = false;
            try {
                Test.startTest();
                DoctorPortalController.submitVote(pr.Id, '-1'); // Malicious vote
                Test.stopTest();
            } catch (Exception e) {
                // Expected AuraHandledException wrapping SecurityException
                exceptionCaught = true;
                System.debug('Caught Exception: ' + e.getMessage());
                // In production it returns AuraHandledException with generic message or internal error, 
                // but unit tests see the exception thrown.
            }
            
            System.assert(exceptionCaught, 'Should have thrown exception for unauthorized access');
            
            // Verify DB wasn't touched
            Peer_Review__c distinctPr = [SELECT Id, Status__c, Vote__c FROM Peer_Review__c WHERE Id = :pr.Id];
            System.assertEquals('Pending', distinctPr.Status__c, 'Status should remain Pending');
            System.assertEquals(null, distinctPr.Vote__c, 'Vote should remain null');
        }
    }
}