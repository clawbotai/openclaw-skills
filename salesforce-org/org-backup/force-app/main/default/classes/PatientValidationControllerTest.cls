@isTest
private class PatientValidationControllerTest {

    @testSetup
    static void setup() {
        // Create Practice Account for Doctor
        Account practiceAcc = new Account(
            Name = 'Dr. Testing Practice',
            Patient_Email__c = 'doc@test.com'
        );
        insert practiceAcc;

        // Create Contact for Doctor
        Contact docContact = new Contact(
            FirstName = 'Testing',
            LastName = 'Doctor',
            Email = 'doc@test.com',
            AccountId = practiceAcc.Id
        );
        insert docContact;

        // Create Doctor Profile User
        Profile doctorProfile = [SELECT Id FROM Profile WHERE Name = 'Azoth Doctor Profile' LIMIT 1];
        User docUser = new User(
            Alias = 'docuser', 
            Email = 'doc@test.com',
            EmailEncodingKey='UTF-8', 
            LastName='Testing', 
            LanguageLocaleKey='en_US',
            LocaleSidKey='en_US', 
            ProfileId = doctorProfile.Id,
            ContactId = docContact.Id,
            TimeZoneSidKey='America/New_York', 
            UserName='doc@test.com.azoth'
        );
        insert docUser;

        // Create Doctor Record
        Doctor__c doc = new Doctor__c(
            Name = 'Dr. Testing',
            Status__c = 'Active',
            User__c = docUser.Id,
            Medical_License__c = '12345'
        );
        insert doc;
        
        // Create Patient Account (Simulating the one created by intake)
        Account patientAcc = new Account(
            Name = 'Patient Test',
            Patient_Email__c = 'patient@test.com',
            Validation_Status__c = 'Pending',
            Doctor__c = doc.Id
        );
        insert patientAcc;

        // Create Contact for Patient (Simulating auto-creation or manual creation)
        Contact patientContact = new Contact(
            FirstName = 'Patient',
            LastName = 'Test',
            Email = 'patient@test.com',
            AccountId = patientAcc.Id
        );
        insert patientContact;
    }

    @isTest
    static void testGetPatientData() {
        Account acc = [SELECT Id FROM Account WHERE Name = 'Patient Test' LIMIT 1];
        
        Test.startTest();
        String name = PatientValidationController.getPatientName(acc.Id);
        String status = PatientValidationController.getValidationStatus(acc.Id);
        Test.stopTest();

        System.assertEquals('Patient Test', name);
        System.assertEquals('Pending', status);
    }

    @isTest
    static void testValidatePatient() {
        Account acc = [SELECT Id FROM Account WHERE Name = 'Patient Test' LIMIT 1];
        
        Test.startTest();
        PatientValidationController.validatePatient(acc.Id);
        Test.stopTest();

        // Verify Status Update
        Account updatedAcc = [SELECT Validation_Status__c FROM Account WHERE Id = :acc.Id];
        System.assertEquals('Validated', updatedAcc.Validation_Status__c);

        // Verify Queueable Execution (User creation is async, difficult to query User in same test context without stopTest, but stopTest runs it)
        // Check for User
        // Note: Running user creation in test context might require standard user profile if 'Azoth Patient Profile' causes issues or Mixed DML.
        // Queueable should have run after stopTest.
    }

    @isTest
    static void testAlreadyValidated() {
        Account acc = [SELECT Id FROM Account WHERE Name = 'Patient Test' LIMIT 1];
        acc.Validation_Status__c = 'Validated';
        update acc;

        Test.startTest();
        PatientValidationController.validatePatient(acc.Id);
        Test.stopTest();

        // Should stay validated, no error
        Account updatedAcc = [SELECT Validation_Status__c FROM Account WHERE Id = :acc.Id];
        System.assertEquals('Validated', updatedAcc.Validation_Status__c);
    }
}