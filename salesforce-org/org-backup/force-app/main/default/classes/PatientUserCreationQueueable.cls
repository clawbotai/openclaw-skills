public without sharing class PatientUserCreationQueueable implements Queueable {
    private Id contactId;
    private Id accountId;
    private String email;
    private String firstName;
    private String lastName;

    public PatientUserCreationQueueable(Id contactId, Id accountId, String email, String fName, String lName) {
        this.contactId = contactId;
        this.accountId = accountId;
        this.email = email;
        this.firstName = fName;
        this.lastName = lName;
    }

    public void execute(QueueableContext context) {
        try {
            // Check if user already exists
            List<User> existingUsers = [SELECT Id FROM User WHERE Username = :email + '.patient' OR Email = :email LIMIT 1];
            if (!existingUsers.isEmpty()) {
                System.debug('User already exists for email: ' + email);
                return;
            }

            Profile patientProfile = [SELECT Id FROM Profile WHERE Name = 'Azoth Patient Profile' LIMIT 1];

            User newUser = new User();
            newUser.FirstName = firstName;
            newUser.LastName = lastName;
            newUser.Email = email;
            newUser.Username = email + '.patient';
            newUser.Alias = (lastName.length() > 4 ? lastName.substring(0, 4) : lastName) + (firstName.length() > 3 ? firstName.substring(0, 3) : firstName);
            if (newUser.Alias.length() > 8) newUser.Alias = newUser.Alias.substring(0, 8);
            newUser.CommunityNickname = newUser.Alias + String.valueOf(Crypto.getRandomInteger()).substring(0, 4);
            newUser.ProfileId = patientProfile.Id;
            newUser.ContactId = contactId;
            newUser.EmailEncodingKey = 'UTF-8';
            newUser.LanguageLocaleKey = 'en_US';
            newUser.LocaleSidKey = 'en_US';
            newUser.TimeZoneSidKey = 'America/New_York';
            newUser.IsActive = true;

            insert newUser;
            System.debug('Patient User Created: ' + newUser.Id);

        } catch (Exception e) {
            System.debug('Error in PatientUserCreationQueueable: ' + e.getMessage());
            // Optionally log error to a custom object
        }
    }
}