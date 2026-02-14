public with sharing class InventoryFlowController {
    
    @InvocableMethod(label='Get Unique Inventory Options' description='Returns a list of unique Inventory records for a Product, prioritized by Expiration Date.')
    public static List<List<Inventory__c>> getUniqueInventoryOptions(List<Id> productIds) {
        List<List<Inventory__c>> results = new List<List<Inventory__c>>();
        
        for (Id productId : productIds) {
            // Map to store unique Mass -> Best Inventory Record
            Map<Decimal, Inventory__c> uniqueMap = new Map<Decimal, Inventory__c>();
            
            // Query Inventory for this Product
            // Ordered by Expiration Date (ASC) and Created Date (ASC) to prioritize earliest expiry/oldest stock
            List<Inventory__c> inventoryList = [
                SELECT Id, Name, Mass__c, Expiration_Date__c, CreatedDate, Batch_Number__c 
                FROM Inventory__c 
                WHERE Product__c = :productId 
                AND Mass__c != null 
                AND Amount__c > 0
                ORDER BY Expiration_Date__c ASC NULLS LAST, CreatedDate ASC
            ];
            
            for (Inventory__c inv : inventoryList) {
                // If we haven't seen this Mass yet, add it. 
                // Because of the ORDER BY, the first one we see is the "best" one.
                if (!uniqueMap.containsKey(inv.Mass__c)) {
                    uniqueMap.put(inv.Mass__c, inv);
                }
            }
            
            // Add the values (unique inventory records) to the result list
            // Optionally sort by Mass for display purposes if needed, but Map values come out in insertion order (mostly)
            // To be safe and nice for UI, let's sort by Mass
            List<Inventory__c> uniqueList = uniqueMap.values();
            uniqueList.sort(new InventoryMassComparator());
            
            results.add(uniqueList);
        }
        
        return results;
    }
    
    // Comparator to sort Inventory by Mass ASC for the UI dropdown
    public class InventoryMassComparator implements Comparator<Inventory__c> {
        public Integer compare(Inventory__c a, Inventory__c b) {
            if (a.Mass__c < b.Mass__c) return -1;
            if (a.Mass__c > b.Mass__c) return 1;
            return 0;
        }
    }
}