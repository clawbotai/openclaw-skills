@isTest
public class DoctorValidationPermissionTest {
    
    @isTest
    static void testValidationAsDoctor() {
        // 1. Create Data for Doctor User (Account + Contact required for Portal User)
        Account doctorAcc = new Account(
            Name = 'Doctor Hospital',
            Patient_Email__c = 'doctor.hospital@example.com' // Trigger/Validation requires this
        );
        insert doctorAcc;
        
        Contact doctorCon = new Contact(
            FirstName = 'DrTest', 
            LastName = 'Permission', 
            AccountId = doctorAcc.Id,
            Email = 'drtest.perm@example.com'
        );
        insert doctorCon;
        
        // Create Doctor User
        Profile doctorProfile = [SELECT Id FROM Profile WHERE Name = 'Azoth Doctor Profile' LIMIT 1];
        User doctorUser = new User(
            FirstName = 'DrTest',
            LastName = 'Permission',
            Email = 'drtest.perm@example.com',
            Username = 'drtest.perm@example.com.' + System.currentTimeMillis(),
            Alias = 'drperm',
            ProfileId = doctorProfile.Id,
            ContactId = doctorCon.Id, // Link to Contact
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
        insert doctorUser;
        
        // 2. Create Patient Account owned by Doctor
        Account patientAcc = new Account(
            Name = 'Test Patient OwnedByDoc',
            Patient_Email__c = 'patient.owned@example.com',
            Validation_Status__c = 'Pending',
            OwnerId = doctorUser.Id
        );
        insert patientAcc;
        
        // Ensure Contact is created (Trigger usually does this, but we might need to query it)
        Contact c = [SELECT Id FROM Contact WHERE AccountId = :patientAcc.Id LIMIT 1];
        
        // 3. Run Validation as Doctor
        System.runAs(doctorUser) {
            Test.startTest();
            try {
                PatientValidationController.validatePatient(patientAcc.Id);
            } catch (Exception e) {
                System.debug('EXCEPTION AS DOCTOR: ' + e.getMessage());
                // Don't fail the test yet, let's verify if updates happened
            }
            Test.stopTest();
        }
        
        // 4. Verify Results
        Account updatedAcc = [SELECT Owner.Profile.Name, Validation_Status__c FROM Account WHERE Id = :patientAcc.Id];
        
        System.debug('Final Owner Profile: ' + updatedAcc.Owner.Profile.Name);
        System.debug('Final Validation Status: ' + updatedAcc.Validation_Status__c);
        
        // Assertions for correctness
        System.assertEquals('Validated', updatedAcc.Validation_Status__c, 'Validation Status should be Validated');
        System.assertEquals('System Administrator', updatedAcc.Owner.Profile.Name, 'Owner should be reassigned to System Admin');
    }
}