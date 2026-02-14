trigger AccountContactCreation on Account (after insert) {
    List<Contact> contactsToInsert = new List<Contact>();
    
    for (Account acc : Trigger.new) {
        // Only create Contact if Account has an email (patient intake scenario)
        if (String.isNotBlank(acc.Patient_Email__c)) {
            Contact newContact = new Contact();
            
            // Parse the Account Name to get First/Last name
            String fullName = acc.Name;
            List<String> nameParts = fullName.split(' ', 2);
            
            newContact.FirstName = nameParts.size() > 0 ? nameParts[0] : 'Patient';
            newContact.LastName = nameParts.size() > 1 ? nameParts[1] : fullName;
            newContact.Email = acc.Patient_Email__c;
            newContact.Phone = acc.Patient_Phone__c;
            newContact.AccountId = acc.Id;
            
            contactsToInsert.add(newContact);
        }
    }
    
    if (!contactsToInsert.isEmpty()) {
        try {
            insert contactsToInsert;
        } catch (Exception e) {
            System.debug('Trigger failed to auto-create contact (likely Guest User visibility): ' + e.getMessage());
            // Swallow error to allow Controller to handle creation via "without sharing"
        }
    }
}