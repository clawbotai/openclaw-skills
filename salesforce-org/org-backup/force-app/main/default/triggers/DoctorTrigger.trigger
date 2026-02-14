trigger DoctorTrigger on Doctor__c (after update) {
    for (Doctor__c doc : Trigger.new) {
        Doctor__c oldDoc = Trigger.oldMap.get(doc.Id);

        // Check if Status changed to 'Active' AND User is not yet created
        if (doc.Status__c == 'Active' && oldDoc.Status__c != 'Active' && doc.User__c == null && String.isNotBlank(doc.Applicant_Email__c)) {
            
            // Parse First/Last Name from Doctor Name (stored as "First Last" by Intake)
            String fName = 'Dr.';
            String lName = doc.Name;
            
            // Attempt to split by space
            List<String> parts = doc.Name.split(' ');
            if (parts.size() >= 2) {
                fName = parts[0];
                // Join the rest as Last Name in case of "De la Cruz"
                parts.remove(0);
                lName = String.join(parts, ' ');
            } else {
                // Fallback if only one name provided
                fName = doc.Name;
                lName = doc.Name;
            }

            // Enqueue Provisioning Job - Passing NULL for ContactId to let the Job find/create it
            System.enqueueJob(new AzothDoctorUserProvisioning(null, doc.Id, fName, lName, doc.Applicant_Email__c));
            System.debug('Enqueued User Provisioning for Doctor: ' + doc.Name);
        }
    }
}