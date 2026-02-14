public without sharing class AzothDoctorIntakeController {

    @AuraEnabled
    public static String submitDoctorApplication(Map<String, Object> doctorData) {
        Savepoint sp = Database.setSavepoint();
        try {
            System.debug('Received Doctor Data: ' + doctorData);

            String firstName = (String) doctorData.get('firstName');
            String lastName = (String) doctorData.get('lastName');
            String email = (String) doctorData.get('email');
            String phone = (String) doctorData.get('phone');
            String license = (String) doctorData.get('medicalLicense');

            if (String.isBlank(email) || String.isBlank(lastName) || String.isBlank(license)) {
                AuraHandledException e = new AuraHandledException('Missing required fields.');
                e.setMessage('Missing required fields.');
                throw e;
            }

            // 1. Check for Existing User
            List<User> existingUsers = [SELECT Id FROM User WHERE Username = :email OR Email = :email LIMIT 1];
            if (!existingUsers.isEmpty()) {
                AuraHandledException e = new AuraHandledException('A user with this email already exists.');
                e.setMessage('A user with this email already exists.');
                throw e;
            }

            // 2. Account Creation (Practice Account)
            Account practiceAcct = new Account();
            practiceAcct.Name = 'Dr. ' + lastName + ' Practice';
            practiceAcct.Patient_Email__c = email; // Required Custom Field
            
            // Assign Doctor_Practice RecordType if available
            List<RecordType> rts = [SELECT Id FROM RecordType WHERE SObjectType = 'Account' AND DeveloperName = 'Doctor_Practice' LIMIT 1];
            if (!rts.isEmpty()) {
                practiceAcct.RecordTypeId = rts[0].Id;
            }
            
            insert practiceAcct;

            // 3. Contact Handling (Reuse Auto-Created Contact)
            // The AccountContactCreation trigger is expected to create a Contact; defensively handle if it didn't.
            Contact doctorContact;
            List<Contact> contacts = [SELECT Id, FirstName, LastName, Email, Phone FROM Contact WHERE AccountId = :practiceAcct.Id LIMIT 1];
            if (!contacts.isEmpty()) {
                doctorContact = contacts[0];
            } else {
                // Create a primary contact if the trigger did not run
                doctorContact = new Contact(
                    AccountId = practiceAcct.Id,
                    FirstName = firstName,
                    LastName = lastName,
                    Email = email,
                    Phone = phone
                );
                insert doctorContact;
            }
            // Update details to ensure correctness
            doctorContact.FirstName = firstName;
            doctorContact.LastName = lastName;
            doctorContact.Email = email; // Should match Account.Patient_Email__c
            doctorContact.Phone = phone;
            update doctorContact;

            // 4. Doctor__c Creation (Pending User)
            Doctor__c newDoc = new Doctor__c();
            newDoc.Name = 'Dr. ' + lastName;
            newDoc.Medical_License__c = license;
            newDoc.Status__c = 'Inactive'; // Pending Admin Verification 
            newDoc.Applicant_Email__c = email; // For Trigger to find Contact later
            insert newDoc;

            // 5. Notify Admin (Approval Process)
            sendAdminNotification(newDoc.Id, firstName, lastName, email);

            return newDoc.Id;

        } catch (Exception e) {
            Database.rollback(sp);
            System.debug('Error in submitDoctorApplication: ' + e.getMessage());
            AuraHandledException ahe = new AuraHandledException('Registration failed: ' + e.getMessage());
            ahe.setMessage('Registration failed: ' + e.getMessage());
            throw ahe;
        }
    }

    private static void sendAdminNotification(Id doctorId, String fName, String lName, String email) {
        try {
            // Reverted Method: Custom Metadata does not exist in this org.
            // Using the verified "Manuel velez" logic.
            String adminEmail = 'nadmin@azoth.is'; // Fallback & Default
            try {
                User admin = [SELECT Email FROM User WHERE Name = 'Manuel velez' LIMIT 1];
                adminEmail = admin.Email;
            } catch (Exception e) {
                System.debug('Guest User unable to query specific Admin User. Using fallback: ' + adminEmail);
            }

            Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
            mail.setToAddresses(new List<String>{adminEmail});
            mail.setSubject('New Doctor Application: Dr. ' + lName);

            String body = 'A new doctor has applied and requires verification.\n\n';
            body += 'Name: ' + fName + ' ' + lName + '\n';
            body += 'Email: ' + email + '\n\n';
            body += 'Click below to review and Activate:\n';
            body += URL.getOrgDomainUrl().toExternalForm() + '/' + doctorId;

            mail.setPlainTextBody(body);
            
            // OrgWideEmailAddress check (optional but robust)
            try {
                List<OrgWideEmailAddress> owe = [SELECT Id FROM OrgWideEmailAddress WHERE Address LIKE '%@%' LIMIT 1];
                if (!owe.isEmpty()) {
                    mail.setOrgWideEmailAddressId(owe[0].Id);
                }
            } catch (Exception ignore) {}
            
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{mail});

        } catch(Exception e) {
            System.debug('Failed to send admin notification: ' + e.getMessage());
        }
    }
}