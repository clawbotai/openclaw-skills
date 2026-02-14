public with sharing class AzothPatientController {
    
    // Helper to get Context (Real or Simulated)
    private static Map<String, Id> getPatientContext() {
        Map<String, Id> ctx = new Map<String, Id>();
        User u = [SELECT ContactId, Contact.AccountId FROM User WHERE Id = :UserInfo.getUserId()];
        
        if (u.ContactId != null) {
            ctx.put('ContactId', u.ContactId);
            ctx.put('AccountId', u.Contact.AccountId);
        } else {
            // SIMULATION FALLBACK: "TEs patient" (Has Orders)
            // Use specific record to ensure data visibility
            Id simulatedContactId = '003fn000005sc8fAAA'; 
            Id simulatedAccountId = '001fn00000FfGg5AAF';
            
            ctx.put('ContactId', simulatedContactId);
            ctx.put('AccountId', simulatedAccountId);
        }
        return ctx;
    }

    @AuraEnabled(cacheable=true)
    public static Contact getPatientProfile() {
        Map<String, Id> ctx = getPatientContext();
        if (!ctx.containsKey('ContactId')) return null;
        
        return [
            SELECT Id, Name, Email, Phone, MailingCity, 
                   Account.Name, Account.Type, CreatedDate,
                   Account.Doctor__r.Name, Account.Doctor__r.Medical_License__c
            FROM Contact
            WHERE Id = :ctx.get('ContactId')
            LIMIT 1
        ];
    }

    @AuraEnabled(cacheable=true)
    public static List<Order> getMyOrders() {
        try {
            Map<String, Id> ctx = getPatientContext();
            if (!ctx.containsKey('ContactId')) return new List<Order>();

            Id contactId = ctx.get('ContactId');
            Id accountId = ctx.get('AccountId');

            // 2. Query Orders
            return [
                SELECT Id, OrderNumber, Status, TotalAmount, EffectiveDate, Type
                FROM Order
                WHERE BillToContactId = :contactId 
                   OR ShipToContactId = :contactId
                   OR AccountId = :accountId
                ORDER BY EffectiveDate DESC
                LIMIT 20
            ];
        } catch (Exception e) {
            System.debug('Error in getMyOrders: ' + e.getMessage());
            return new List<Order>();
        }
    }

    @AuraEnabled(cacheable=true)
    public static List<Wellness_Assessment__c> getMyIntakes() {
        Map<String, Id> ctx = getPatientContext();
        if (!ctx.containsKey('AccountId')) return new List<Wellness_Assessment__c>();

        return [
            SELECT Id, Name, Type__c, CreatedDate
            FROM Wellness_Assessment__c
            WHERE Patient__c = :ctx.get('AccountId')
            ORDER BY CreatedDate DESC
            LIMIT 50
        ];
    }

    @AuraEnabled(cacheable=true)
    public static List<Event> getMyAppointments() {
        Map<String, Id> ctx = getPatientContext();
        if (!ctx.containsKey('AccountId')) return new List<Event>();

        Id accountId = ctx.get('AccountId');
        Id contactId = ctx.get('ContactId');

        return [
            SELECT Id, Subject, StartDateTime, Owner.Name
            FROM Event
            WHERE (WhatId = :accountId OR WhoId = :contactId)
            AND StartDateTime >= TODAY
            ORDER BY StartDateTime ASC
            LIMIT 20
        ];
    }
}