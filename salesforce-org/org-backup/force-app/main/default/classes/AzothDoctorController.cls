public with sharing class AzothDoctorController {

    private static Id getDoctorId() {
        List<Doctor__c> docs = [SELECT Id FROM Doctor__c WHERE User__c = :UserInfo.getUserId() LIMIT 1];
        if (!docs.isEmpty()) {
            return docs[0].Id;
        }
        // SIMULATION FALLBACK: Return first available doctor for preview
        List<Doctor__c> fallback = [SELECT Id FROM Doctor__c LIMIT 1];
        return fallback.isEmpty() ? null : fallback[0].Id;
    }

    @AuraEnabled(cacheable=true)
    public static Doctor__c getDoctorProfile() {
        Id docId = getDoctorId();
        if (docId == null) return null;
        
        return [
            SELECT Id, Name, Trust_Score__c, Tier_Formula__c, Status__c, 
                   Medical_License__c, CreatedDate, Total_Seals__c
            FROM Doctor__c
            WHERE Id = :docId
            LIMIT 1
        ];
    }

    @AuraEnabled(cacheable=true)
    public static List<Peer_Review__c> getPendingReviews() {
        Id docId = getDoctorId();
        if (docId == null) return new List<Peer_Review__c>();

        return [
            SELECT Id, Name, Status__c, Order__r.OrderNumber, CreatedDate
            FROM Peer_Review__c 
            WHERE Status__c NOT IN ('Completed', 'Expired')
            AND (Expiration_Date__c = NULL OR Expiration_Date__c >= TODAY)
            AND Reviewer__c = :docId
            ORDER BY CreatedDate ASC
            LIMIT 5
        ];
    }

    @AuraEnabled(cacheable=true)
    public static List<Order> getRecentOrders() {
        Id docId = getDoctorId();
        if (docId == null) return new List<Order>();
        
        return [
            SELECT Id, OrderNumber, Account.Name, Status, TotalAmount, EffectiveDate
            FROM Order
            WHERE Doctor__c = :docId
            ORDER BY EffectiveDate DESC
            LIMIT 5
        ];
    }
    @AuraEnabled(cacheable=true)
    public static List<Account> getMyPatients() {
        Id docId = getDoctorId();
        if (docId == null) return new List<Account>();

        return [
            SELECT Id, Name, Phone, BillingCity, CreatedDate
            FROM Account
            WHERE Doctor__c = :docId
            ORDER BY Name ASC
            LIMIT 50
        ];
    }

    @AuraEnabled(cacheable=true)
    public static List<Wellness_Assessment__c> getWellnessAssessments() {
        Id docId = getDoctorId();
        if (docId == null) return new List<Wellness_Assessment__c>();

        return [
            SELECT Id, Name, Patient__r.Name, Type__c, CreatedDate
            FROM Wellness_Assessment__c
            WHERE Doctor__c = :docId
            ORDER BY CreatedDate DESC
            LIMIT 50
        ];
    }
    @AuraEnabled(cacheable=true)
    public static List<Event> getUpcomingAppointments(String doctorId) {
        // 1. Resolve Doctor ID (param or context)
        Id targetDocId = (doctorId != null && doctorId instanceof Id) ? (Id)doctorId : getDoctorId();
        if (targetDocId == null) return new List<Event>();

        // 2. Resolve User ID from Doctor
        List<Doctor__c> docRecords = [SELECT User__c FROM Doctor__c WHERE Id = :targetDocId LIMIT 1];
        if (docRecords.isEmpty() || docRecords[0].User__c == null) {
            return new List<Event>(); 
        }
        Id targetUserId = docRecords[0].User__c;

        // 3. Query Events owned by that User
        return [
            SELECT Id, Subject, StartDateTime, EndDateTime, What.Name, Who.Name
            FROM Event
            WHERE OwnerId = :targetUserId
            AND StartDateTime >= TODAY
            ORDER BY StartDateTime ASC
            LIMIT 20
        ];
    }


    @AuraEnabled
    public static void activateOrder(String orderId) {
        try {
            if (String.isBlank(orderId)) {
                throw new AuraHandledException('Error: Order ID is missing.');
            }

            Order ord = [SELECT Id, Status FROM Order WHERE Id = :orderId LIMIT 1];
            if (ord.Status != 'Draft') {
                throw new AuraHandledException('Error: Only Draft orders can be activated.');
            }

            ord.Status = 'Activated';
            update ord;
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }

    @AuraEnabled(cacheable=true)
    public static List<Map<String, Object>> getRelatedTasks() {
        Id userId = UserInfo.getUserId();
        
        List<Task> tasks = [
            SELECT Id, Subject, Priority, Status, ActivityDate, WhatId, What.Name, Who.Name, CreatedDate
            FROM Task
            WHERE OwnerId = :userId
            AND IsClosed = FALSE
            ORDER BY Priority DESC, CreatedDate DESC
            LIMIT 20
        ];

        Set<Id> accountIds = new Set<Id>();
        for(Task t : tasks) {
            if(t.WhatId != null && t.WhatId.getSobjectType() == Account.SObjectType) {
                accountIds.add(t.WhatId);
            }
        }

        Map<Id, Id> accToAssessmentMap = new Map<Id, Id>();
        if(!accountIds.isEmpty()) {
            // Get latest assessment for these accounts
            for(Wellness_Assessment__c wa : [
                SELECT Id, Patient__c 
                FROM Wellness_Assessment__c 
                WHERE Patient__c IN :accountIds 
                ORDER BY CreatedDate DESC
            ]) {
                if(!accToAssessmentMap.containsKey(wa.Patient__c)) {
                    accToAssessmentMap.put(wa.Patient__c, wa.Id);
                }
            }
        }

        List<Map<String, Object>> results = new List<Map<String, Object>>();
        for(Task t : tasks) {
            Map<String, Object> row = new Map<String, Object>();
            row.put('Id', t.Id);
            row.put('Subject', t.Subject);
            row.put('Priority', t.Priority);
            row.put('Status', t.Status);
            row.put('ActivityDate', t.ActivityDate);
            row.put('WhatName', t.What != null ? t.What.Name : '');
            row.put('WhoName', t.Who != null ? t.Who.Name : '');
            row.put('CreatedDate', t.CreatedDate);
            
            if(accToAssessmentMap.containsKey(t.WhatId)) {
                row.put('AssessmentId', accToAssessmentMap.get(t.WhatId));
            }
            results.add(row);
        }
        return results;
    }
}