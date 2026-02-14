public with sharing class InventoryTriggerHandler {
    
    public static void onAfterInsert(List<Inventory__c> newRecords) {
        processUpdates(newRecords, null);
    }
    
    public static void onAfterUpdate(List<Inventory__c> newRecords, Map<Id, Inventory__c> oldMap) {
        processUpdates(newRecords, oldMap);
    }
    
    public static void onAfterDelete(List<Inventory__c> oldRecords) {
        processUpdates(oldRecords, null);
    }
    
    public static void onAfterUndelete(List<Inventory__c> newRecords) {
        processUpdates(newRecords, null);
    }
    
    private static void processUpdates(List<Inventory__c> records, Map<Id, Inventory__c> oldMap) {
        Set<Id> productIds = new Set<Id>();
        
        for (Inventory__c inv : records) {
            if (inv.Product__c != null) {
                productIds.add(inv.Product__c);
            }
            // Handle reparenting (Product lookup changed)
            if (oldMap != null) {
                Inventory__c oldInv = oldMap.get(inv.Id);
                if (oldInv.Product__c != null && oldInv.Product__c != inv.Product__c) {
                    productIds.add(oldInv.Product__c);
                }
            }
        }
        
        if (!productIds.isEmpty()) {
            InventoryManager.recalculateProductStock(productIds);
        }
    }
}