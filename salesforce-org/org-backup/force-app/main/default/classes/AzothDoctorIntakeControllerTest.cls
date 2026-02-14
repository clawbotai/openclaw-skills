@isTest
private class AzothDoctorIntakeControllerTest {
    
    @isTest
    static void testSubmitDoctorApplication_Success() {
        Map<String, Object> data = new Map<String, Object>();
        data.put('firstName', 'TestDr');
        data.put('lastName', 'UnitQueue');
        String testEmail = 'dr.queue' + System.currentTimeMillis() + '@example.com';
        data.put('email', testEmail); 
        data.put('phone', '555-0100');
        data.put('medicalLicense', 'LIC-QUEUE');
        
        String doctorId = AzothDoctorIntakeController.submitDoctorApplication(data);
        
        System.assertNotEquals(null, doctorId);
        
        // Verify Doctor Status is Inactive (Pending Approval)
        Doctor__c doc = [SELECT Id, User__c, Status__c, Applicant_Email__c FROM Doctor__c WHERE Id = :doctorId];
        System.assertEquals('Inactive', doc.Status__c, 'Status should be Inactive pending approval');
        System.assertEquals(null, doc.User__c, 'User should not be created immediately');
        System.assertEquals(testEmail, doc.Applicant_Email__c, 'Applicant Email should be stored');

        // Simulate Admin Approval (Trigger Fire)
        Test.startTest(); // Separate async context
        doc.Status__c = 'Active';
        update doc;
        Test.stopTest(); // Force Async Execution

        // Verify User Creation
        doc = [SELECT Id, User__c FROM Doctor__c WHERE Id = :doctorId];
        System.assertNotEquals(null, doc.User__c, 'User should be created after approval');
        
        // Verify Account RecordType
        User u = [SELECT Id, ContactId FROM User WHERE Id = :doc.User__c];
        Contact c = [SELECT Id, AccountId FROM Contact WHERE Id = :u.ContactId];
        Account a = [SELECT Id, RecordType.DeveloperName FROM Account WHERE Id = :c.AccountId];
        
        if (![SELECT Id FROM RecordType WHERE SObjectType='Account' AND DeveloperName='Doctor_Practice'].isEmpty()) {
             System.assertEquals('Doctor_Practice', a.RecordType.DeveloperName, 'Account should have Doctor Practice RecordType');
        }
        
        // Verify only 1 contact exists (Reuse Logic)
        Integer contactCount = [SELECT Count() FROM Contact WHERE AccountId = :c.AccountId];
        System.assertEquals(1, contactCount, 'Should reuse the auto-created contact, not create a duplicate.');
    }

    @isTest
    static void testSubmitDoctorApplication_DuplicateEmail() {
        // Create user with unique email
        String uniqueEmail = 'dup' + System.currentTimeMillis() + '@test.com';
        Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];
        User existingUser = new User(
            Alias = 'dupt', Email=uniqueEmail, 
            EmailEncodingKey='UTF-8', LastName='Testing', LanguageLocaleKey='en_US', 
            LocaleSidKey='en_US', ProfileId = p.Id, 
            TimeZoneSidKey='America/Los_Angeles', UserName=uniqueEmail
        );
        insert existingUser;

        Map<String, Object> data = new Map<String, Object>();
        data.put('firstName', 'New');
        data.put('lastName', 'Doc');
        data.put('email', uniqueEmail); // Should trigger duplicate check
        data.put('phone', '555-9999');
        data.put('medicalLicense', 'LIC-999');

        Test.startTest();
        try {
            AzothDoctorIntakeController.submitDoctorApplication(data);
            System.assert(false, 'Should have thrown exception');
        } catch (Exception e) {
            System.assert(e.getMessage().contains('already exists') || e.getMessage().contains('Registration failed'), 'Error: ' + e.getMessage());
        }
        Test.stopTest();
    }
}