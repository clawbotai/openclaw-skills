@isTest
private class AzothDoctorControllerTest {

    @testSetup
    static void setup() {
        // Create Users
        Profile p = [SELECT Id FROM Profile WHERE Name='Standard User']; 
        User u1 = new User(Alias = 'doc1', Email='doc1@testorg.com', 
            EmailEncodingKey='UTF-8', LastName='Testing', LanguageLocaleKey='en_US', 
            LocaleSidKey='en_US', ProfileId = p.Id, 
            TimeZoneSidKey='America/Los_Angeles', UserName='doc1@testorg.com');
        insert u1;

        User u2 = new User(Alias = 'doc2', Email='doc2@testorg.com', 
            EmailEncodingKey='UTF-8', LastName='Testing', LanguageLocaleKey='en_US', 
            LocaleSidKey='en_US', ProfileId = p.Id, 
            TimeZoneSidKey='America/Los_Angeles', UserName='doc2@testorg.com');
        insert u2;

        // Create Accounts
        Account acc = new Account(Name='Test Patient');
        insert acc;

        // Create Doctors linked to Users
        Doctor__c doc1 = new Doctor__c(Name='Doctor One', User__c=u1.Id, Medical_License__c='LIC-001');
        insert doc1;
        
        Doctor__c doc2 = new Doctor__c(Name='Doctor Two', User__c=u2.Id, Medical_License__c='LIC-002');
        insert doc2;

        // Create Orders
        Order o1 = new Order(AccountId=acc.Id, Doctor__c=doc1.Id, Status='Draft', EffectiveDate=Date.today());
        insert o1;
        
        Order o2 = new Order(AccountId=acc.Id, Doctor__c=doc2.Id, Status='Draft', EffectiveDate=Date.today());
        insert o2;

        // Create Peer Reviews
        // Assuming Peer_Review__c has a required Order__c lookup based on previous queries
        // And Reviewer__c lookup
        Peer_Review__c pr1 = new Peer_Review__c(Name='Review 1', Status__c='Pending', Reviewer__c=doc1.Id, Order__c=o1.Id);
        insert pr1;

        Peer_Review__c pr2 = new Peer_Review__c(Name='Review 2', Status__c='Pending', Reviewer__c=doc2.Id, Order__c=o2.Id);
        insert pr2;
    }

    @isTest
    static void testGetPendingReviews() {
        User u1 = [SELECT Id FROM User WHERE UserName='doc1@testorg.com'];
        
        System.runAs(u1) {
            List<Peer_Review__c> reviews = AzothDoctorController.getPendingReviews();
            System.assertEquals(1, reviews.size(), 'Should restrict to own reviews');
            System.assertEquals('Review 1', reviews[0].Name, 'Should get correct review');
        }
    }

    @isTest
    static void testGetRecentOrders() {
        User u1 = [SELECT Id FROM User WHERE UserName='doc1@testorg.com'];
        
        System.runAs(u1) {
            List<Order> orders = AzothDoctorController.getRecentOrders();
            System.assertEquals(1, orders.size(), 'Should restrict to own orders');
        }
    }

    @isTest
    static void testGetPendingReviews_Expired() {
        User u1 = [SELECT Id FROM User WHERE UserName='doc1@testorg.com'];
        Doctor__c doc1 = [SELECT Id FROM Doctor__c WHERE User__c = :u1.Id LIMIT 1];
        Order o1 = [SELECT Id FROM Order WHERE Doctor__c = :doc1.Id LIMIT 1];

        // Create expired reviews
        Peer_Review__c expiredStatusPr = new Peer_Review__c(Name='Expired Status', Status__c='Expired', Reviewer__c=doc1.Id, Order__c=o1.Id);
        insert expiredStatusPr;

        Peer_Review__c expiredDatePr = new Peer_Review__c(Name='Expired Date', Status__c='Pending', Reviewer__c=doc1.Id, Order__c=o1.Id, Expiration_Date__c=Date.today().addDays(-1));
        insert expiredDatePr;

        System.runAs(u1) {
            List<Peer_Review__c> reviews = AzothDoctorController.getPendingReviews();
            
            // Should only have the initial 'Review 1' from setup, preventing the 2 new expired ones
            System.assertEquals(1, reviews.size(), 'Should filter out expired reviews');
            for(Peer_Review__c pr : reviews) {
                System.assertNotEquals('Expired Status', pr.Name);
                System.assertNotEquals('Expired Date', pr.Name);
            }
        }
    }

    @isTest
    static void testNoDoctor() {
        // Create user with no doctor
        Profile p = [SELECT Id FROM Profile WHERE Name='Standard User']; 
        User u3 = new User(Alias = 'nodoc', Email='nodoc@testorg.com', 
            EmailEncodingKey='UTF-8', LastName='Testing', LanguageLocaleKey='en_US', 
            LocaleSidKey='en_US', ProfileId = p.Id, 
            TimeZoneSidKey='America/Los_Angeles', UserName='nodoc@testorg.com');
        insert u3;

        System.runAs(u3) {
            List<Peer_Review__c> reviews = AzothDoctorController.getPendingReviews();
            System.assertEquals(0, reviews.size(), 'Should return empty list for user without doctor record');
            
            List<Order> orders = AzothDoctorController.getRecentOrders();
            System.assertEquals(0, orders.size(), 'Should return empty list for user without doctor record');
        }
    }
}