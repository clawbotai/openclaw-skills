public without sharing class PatientValidationController {

    @AuraEnabled
    public static void validatePatient(Id accountId) {
        try {
            Account patientAcc = [SELECT Id, Name, Validation_Status__c, Patient_Email__c, Phone, Doctor__c FROM Account WHERE Id = :accountId LIMIT 1];
            
            if (patientAcc.Validation_Status__c == 'Validated') {
                return; // Already validated
            }

            // Update Account Status
            // Reassign Account to System Admin to allow Community User creation
            // (Portal Users cannot own Accounts used for other Community Users)
            // Reassign Account to System Admin to allow Community User creation
            // (Portal Users cannot own Accounts used for other Community Users)
            // MUST ensure the Admin has a Role assigned, otherwise portal user creation fails
            User adminUser = [SELECT Id FROM User WHERE Profile.Name = 'System Administrator' AND IsActive = TRUE AND UserRoleId != NULL ORDER BY CreatedDate ASC LIMIT 1];
            
            patientAcc.OwnerId = adminUser.Id;
            patientAcc.Validation_Status__c = 'Validated';
            update patientAcc;

            // Get Contact to create User
            // Assuming Account is the parent of the Contact or PersonAccount
            // If Person Account: ContactId is queryable on Account, but let's query Contact explicitly to be safe or use PersonContactId
            
            Id contactId;
            String email = patientAcc.Patient_Email__c;
            String fName;
            String lName;

            // Handle Person Account or Regular Account linked Contact
            // For now, let's assume standard Model where we find the Contact linked to this Account
            // If it is a Person Account, we need to handle that, but let's assume standard contact for now based on previous context 
            // Actually, let's check if we can get the contact. 
            
            List<Contact> contacts = [SELECT Id, FirstName, LastName, Email FROM Contact WHERE AccountId = :accountId LIMIT 1];
            if (!contacts.isEmpty()) {
                contactId = contacts[0].Id;
                fName = contacts[0].FirstName;
                lName = contacts[0].LastName;
                if(String.isBlank(email)) email = contacts[0].Email;
            } else {
                 throw new AuraHandledException('No Contact found for this Patient Account.');
            }

            if (String.isBlank(email)) {
                throw new AuraHandledException('Patient does not have an email address.');
            }

            // Enqueue User Creation
            System.enqueueJob(new PatientUserCreationQueueable(contactId, accountId, email, fName, lName));

        } catch (Exception e) {
            System.debug('Error validating patient: ' + e.getMessage());
            throw new AuraHandledException('Error validating patient: ' + e.getMessage());
        }
    }
    
    @AuraEnabled(cacheable=true)
    public static String getPatientName(Id accountId) {
        try {
             Account acc = [SELECT Name FROM Account WHERE Id = :accountId LIMIT 1];
             return acc.Name;
        } catch (Exception e) {
            return null;
        }
    }

    @AuraEnabled(cacheable=true)
    public static String getValidationStatus(Id accountId) {
         try {
             Account acc = [SELECT Validation_Status__c FROM Account WHERE Id = :accountId LIMIT 1];
             return acc.Validation_Status__c;
        } catch (Exception e) {
            return null;
        }
    }
}