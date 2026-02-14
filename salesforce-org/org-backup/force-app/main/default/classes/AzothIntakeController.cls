public without sharing class AzothIntakeController {

    @AuraEnabled
    public static String submitIntake(Map<String, Object> intakeData, String doctorSlug) {
        System.debug('===== INTAKE SUBMISSION START =====');
        System.debug('Received doctorSlug: ' + doctorSlug);
        
        Id assignedOwnerId = null;
        Id assignedDoctorId = null; // To store the Doctor__c record ID

        try {
            // --- 1. RESOLVE DOCTOR & OWNER ---
            // Logic: Determine valid User ID (Owner) AND valid Doctor ID (Custom Object)
            if (String.isNotBlank(doctorSlug)) {
                // A. Case: Slug is Doctor__c ID (a01...)
                if (doctorSlug.startsWith('a01') || (doctorSlug instanceof Id && ((Id)doctorSlug).getSobjectType().getDescribe().getName() == 'Doctor__c')) {
                    assignedDoctorId = doctorSlug;
                    // Fetch the User linked to this Doctor
                    List<Doctor__c> docs = [SELECT User__c FROM Doctor__c WHERE Id = :assignedDoctorId LIMIT 1];
                    if (!docs.isEmpty()) {
                         assignedOwnerId = docs[0].User__c;
                         System.debug('Resolved via Doctor ID. Doctor: ' + assignedDoctorId + ', User: ' + assignedOwnerId);
                    }
                }
                // B. Case: Slug is User Alias/Name or User ID
                else {
                    assignedOwnerId = getOwnerFromSlug(doctorSlug);
                    if (assignedOwnerId != null) {
                         // Attempt to find the Doctor record for this User
                         List<Doctor__c> docs = [SELECT Id FROM Doctor__c WHERE User__c = :assignedOwnerId LIMIT 1];
                         if (!docs.isEmpty()) {
                             assignedDoctorId = docs[0].Id;
                             System.debug('Resolved via User Alias. User: ' + assignedOwnerId + ', Found Doctor: ' + assignedDoctorId);
                         } else {
                             System.debug('Resolved via User Alias. User: ' + assignedOwnerId + ', BUT NO DOCTOR RECORD FOUND.');
                         }
                    }
                }
            }

            // --- 2. VALIDATE INPUTS ---
            String email = (String) intakeData.get('email');
            if (String.isBlank(email)) throw new AuraHandledException('Email is required.');

            // --- 3. DUPLICATE CHECK ---
            List<Account> dupes = [SELECT Id FROM Account WHERE Patient_Email__c = :email LIMIT 1];
            if (!dupes.isEmpty()) throw new AuraHandledException('A patient with this email already exists.');

            // --- 4. CREATE ACCOUNT ---
            Account newPatient = new Account();
            String firstName = (String) intakeData.get('firstName');
            String lastName = (String) intakeData.get('lastName');
            newPatient.Name = firstName + ' ' + lastName;
            newPatient.Patient_Email__c = email;
            newPatient.Patient_Phone__c = (String) intakeData.get('phone');
            newPatient.ID_Type__c = (String) intakeData.get('idType');
            newPatient.ID_Number__c = (String) intakeData.get('idNumber');
            
            // Biometrics
            String weightStr = (String)intakeData.get('weight');
            String heightStr = (String)intakeData.get('height');
            if (!String.isBlank(weightStr)) newPatient.Weight_kg_Temp__c = Decimal.valueOf(weightStr);
            if (!String.isBlank(heightStr)) newPatient.Height_cm_Temp__c = Decimal.valueOf(heightStr);
            
            // Safety Flags
            newPatient.Safety_Pregnancy__c = (Boolean) intakeData.get('isPregnancy');
            newPatient.Safety_Active_Malignancy__c = (Boolean) intakeData.get('isCancer');
            newPatient.Safety_Insulin_Use__c = (Boolean) intakeData.get('isInsulin');
            newPatient.Risk_Flag__c = (Boolean) intakeData.get('isHighRisk');

            // Set Links
            if (assignedOwnerId != null) newPatient.OwnerId = assignedOwnerId;
            if (assignedDoctorId != null) {
                newPatient.put('Doctor__c', assignedDoctorId); // Using put to be safe if field dependency is tricky, but explicit is better.
                // Note: If Doctor__c is not the API name, this will fail. Assuming Doctor__c based on previous checks.
            }

            insert newPatient;
            System.debug('Account Created: ' + newPatient.Id);

            // --- 5. AUTOMATED RECORD CREATION (Removed per User Request) ---
            // User requested ONLY Account creation linked to Doctor for now.
            // Future logic for Order/Review creation can be added here if needed.

            return newPatient.Id;

        } catch (Exception e) {
            System.debug('ERROR in submitIntake: ' + e.getMessage());
            throw new AuraHandledException('Submission failed: ' + e.getMessage());
        }
    }

    private static Id getOwnerFromSlug(String slug) {
        if (String.isBlank(slug)) return null;
        // 1. Check for Standard User ID
        if (slug instanceof Id && ((Id)slug).getSobjectType() == User.SObjectType) return (Id)slug;
        // 2. Try finding by User Alias or Last Name
        List<User> doctors = [SELECT Id FROM User WHERE Alias = :slug OR LastName = :slug LIMIT 1];
        if (!doctors.isEmpty()) return doctors[0].Id;
        return null; // Fallback
    }
}