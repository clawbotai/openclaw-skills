public with sharing class DoctorPortalController {
    
    public class HubInfo {
        @AuraEnabled public String recordId;
        @AuraEnabled public String recordType; // 'Doctor' or 'Patient'
    }
    
    @AuraEnabled(cacheable=true)
    public static HubInfo getHubRecord() {
        try {
            Id userId = UserInfo.getUserId();
            HubInfo hub = new HubInfo();
            
            // 1. Check if user is a Doctor (Wrap in try-catch for Profile Access)
            try {
                List<Doctor__c> doctors = [
                    SELECT Id 
                    FROM Doctor__c 
                    WHERE User__c = :userId 
                    LIMIT 1
                ];
                
                if (!doctors.isEmpty()) {
                    hub.recordId = doctors[0].Id;
                    hub.recordType = 'Doctor';
                    return hub;
                }
            } catch (Exception ignore) {
                // User likely lacks access to Doctor__c object; proceed to check Patient.
            }
            
            // 2. Check if user is a Patient (Community User linked to Account via Contact)
            List<User> userContacts = [
                SELECT ContactId, Contact.AccountId 
                FROM User 
                WHERE Id = :userId 
                AND ContactId != null
                LIMIT 1
            ];
            
            if (!userContacts.isEmpty() && userContacts[0].Contact.AccountId != null) {
                hub.recordId = userContacts[0].Contact.AccountId;
                hub.recordType = 'Patient';
                return hub;
            }
            
            return null;
        } catch (Exception e) {
            String debugInfo = e.getTypeName() + ' - ' + e.getMessage() + ' - ' + e.getStackTraceString();
            throw new AuraHandledException('DEBUG: ' + debugInfo);
        }
    }

    @AuraEnabled
    public static void submitVote(String recordId, String vote) {
        try {
            if (String.isBlank(recordId)) {
                throw new AuraHandledException('Error: Record ID is missing (null or empty).');
            }

            // SECURITY CHECK 1: Get Current Doctor ID
            List<Doctor__c> doctors = [SELECT Id FROM Doctor__c WHERE User__c = :UserInfo.getUserId() LIMIT 1];
            if (doctors.isEmpty()) {
                throw new AuraHandledException('Access Denied: You are not a registered Doctor.');
            }
            Id currentDocId = doctors[0].Id;

            // Normalize Vote Value based on User Feedback
            String finalVote = vote;
            if (vote == '1') finalVote = '+1';
            
            // Query with Reviewer field to validate ownership
            List<Peer_Review__c> reviews = [SELECT Id, Status__c, Vote__c, Reviewer__c, Expiration_Date__c FROM Peer_Review__c WHERE Id = :recordId LIMIT 1];
            
            if (reviews.isEmpty()) {
                throw new AuraHandledException('Error: Peer Review Record not found for ID: ' + recordId);
            }

            Peer_Review__c review = reviews[0];

            // SECURITY CHECK 2: Row-Level Security
            if (review.Reviewer__c != currentDocId) {
                throw new SecurityException('Unauthorized access: You are not the assigned reviewer for this record.');
            }

            if (review.Status__c == 'Completed') {
                return; // Already voted
            }
            
            if (review.Status__c == 'Expired' || (review.Expiration_Date__c != null && review.Expiration_Date__c < Date.today())) {
                 throw new AuraHandledException('Error: This peer review request has expired.');
            }

            review.Vote__c = finalVote;
            review.Status__c = 'Completed';
            update review;
        } catch (SecurityException se) {
             // Log the security attempt if needed
             throw new AuraHandledException(se.getMessage());
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
}