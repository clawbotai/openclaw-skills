public class AzothDoctorUserProvisioning implements Queueable {
    private Id contactId;
    private Id doctorId;
    private String firstName;
    private String lastName;
    private String email;

    public AzothDoctorUserProvisioning(Id contactId, Id doctorId, String fName, String lName, String email) {
        this.contactId = contactId;
        this.doctorId = doctorId;
        this.firstName = fName;
        this.lastName = lName;
        this.email = email;
    }

    public void execute(QueueableContext context) {
        try {
            // 0. Ensure Contact Linkage (If not provided, find or create)
            if (this.contactId == null) {
                List<Contact> existingContacts = [SELECT Id FROM Contact WHERE Email = :email LIMIT 1];
                if (!existingContacts.isEmpty()) {
                    this.contactId = existingContacts[0].Id;
                } else {
                    // Create Account Implementation (Practice)
                    Account practiceAcct = new Account();
                    practiceAcct.Name = 'Dr. ' + lastName + ' Practice';
                    practiceAcct.Patient_Email__c = email; // Required
                    
                    List<RecordType> rts = [SELECT Id FROM RecordType WHERE SObjectType = 'Account' AND DeveloperName = 'Doctor_Practice' LIMIT 1];
                    if (!rts.isEmpty()) {
                        practiceAcct.RecordTypeId = rts[0].Id;
                    }
                    insert practiceAcct;

                    // CHECK: Did the trigger create a contact already?
                    List<Contact> triggerContacts = [SELECT Id FROM Contact WHERE AccountId = :practiceAcct.Id LIMIT 1];
                    if (!triggerContacts.isEmpty()) {
                        this.contactId = triggerContacts[0].Id;
                    } else {
                        // Create Contact manually if trigger didn't run
                        Contact newContact = new Contact(
                            AccountId = practiceAcct.Id,
                            FirstName = firstName,
                            LastName = lastName,
                            Email = email
                        );
                        insert newContact;
                        this.contactId = newContact.Id;
                    }
                }
            }

            Profile doctorProfile = [SELECT Id FROM Profile WHERE Name = 'Azoth Doctor Profile' LIMIT 1];
            
            User newUser = new User();
            newUser.FirstName = firstName;
            newUser.LastName = lastName;
            newUser.Email = email;
            newUser.Username = email + '.azoth.' + System.currentTimeMillis(); // Ensure uniqueness
            newUser.Alias = (lastName.length() > 4 ? lastName.substring(0, 4) : lastName) + (firstName.length() > 3 ? firstName.substring(0, 3) : firstName);
            if (newUser.Alias.length() > 8) newUser.Alias = newUser.Alias.substring(0, 8);
            newUser.CommunityNickname = newUser.Alias + String.valueOf(Crypto.getRandomInteger()).substring(0, 4);
            newUser.ProfileId = doctorProfile.Id;
            newUser.ContactId = this.contactId;
            newUser.EmailEncodingKey = 'UTF-8';
            newUser.LanguageLocaleKey = 'en_US';
            newUser.LocaleSidKey = 'en_US';
            newUser.TimeZoneSidKey = 'America/New_York';
            newUser.IsActive = true;
            
            // 1. DMLOption to trigger the standard Salesforce Welcome Email
            Database.DMLOptions dmo = new Database.DMLOptions();
            dmo.EmailHeader.triggerUserEmail = true;
            newUser.setOptions(dmo);
            
            insert newUser;

            // 2. Update Doctor Record with User Link
            Doctor__c docToUpdate = [SELECT Id FROM Doctor__c WHERE Id = :doctorId LIMIT 1];
            docToUpdate.User__c = newUser.Id;
            update docToUpdate;

        } catch (Exception e) {
            System.debug('Async User Creation Failed: ' + e.getMessage());
            // In a real scenario, we might log this to an Error_Log__c object
        }
    }
}