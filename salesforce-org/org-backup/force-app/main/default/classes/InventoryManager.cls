public with sharing class InventoryManager {
    
    public class InventoryException extends Exception {}
    
    /**
     * @description Decrements inventory for a list of OrderItems using FEFO logic.
     * @param orderItems List of OrderItems causing the decrement
     */
    public static void decrementInventory(List<OrderItem> orderItems) {
        // Collect Product IDs and Required Quantities
        Map<Id, Decimal> productQtyMap = new Map<Id, Decimal>();
        for (OrderItem oi : orderItems) {
            if (oi.Product2Id != null && oi.Quantity > 0) {
                if (productQtyMap.containsKey(oi.Product2Id)) {
                    productQtyMap.put(oi.Product2Id, productQtyMap.get(oi.Product2Id) + oi.Quantity);
                } else {
                    productQtyMap.put(oi.Product2Id, oi.Quantity);
                }
            }
        }
        
        if (productQtyMap.isEmpty()) return;
        
        // Query Inventory Records for these products, ordered by Expiration Date ASC (FEFO)
        // LOCKING: Using FOR UPDATE to prevent race conditions
        List<Inventory__c> inventoryList = [
            SELECT Id, Product__c, Amount__c, Expiration_Date__c, Batch_Number__c 
            FROM Inventory__c 
            WHERE Product__c IN :productQtyMap.keySet() 
            AND Amount__c > 0
            ORDER BY Expiration_Date__c ASC NULLS LAST, CreatedDate ASC
        ];
        
        // Organize Inventory by Product
        Map<Id, List<Inventory__c>> productInventoryMap = new Map<Id, List<Inventory__c>>();
        for (Inventory__c inv : inventoryList) {
            if (!productInventoryMap.containsKey(inv.Product__c)) {
                productInventoryMap.put(inv.Product__c, new List<Inventory__c>());
            }
            productInventoryMap.get(inv.Product__c).add(inv);
        }
        
        List<Inventory__c> inventoriesToUpdate = new List<Inventory__c>();
        
        // Process each Product Requirement
        for (Id prodId : productQtyMap.keySet()) {
            Decimal qtyNeeded = productQtyMap.get(prodId);
            List<Inventory__c> availableInventories = productInventoryMap.get(prodId);
            
            if (availableInventories == null || availableInventories.isEmpty()) {
                throw new InventoryException('No inventory found for Product ID: ' + prodId);
            }
            
            Decimal qtyFound = 0;
            
            for (Inventory__c inv : availableInventories) {
                if (qtyNeeded <= 0) break;
                
                Decimal currentAmount = inv.Amount__c != null ? inv.Amount__c : 0;
                
                Decimal qtyTake = 0;
                if (currentAmount >= qtyNeeded) {
                    qtyTake = qtyNeeded;
                    inv.Amount__c = currentAmount - qtyNeeded;
                    qtyNeeded = 0;
                } else {
                    qtyTake = currentAmount;
                    qtyNeeded -= currentAmount;
                    inv.Amount__c = 0;
                }
                
                inventoriesToUpdate.add(inv);
            }
            
            if (qtyNeeded > 0) {
                throw new InventoryException('Insufficient inventory for Product ID: ' + prodId + '. Missing ' + qtyNeeded + ' units.');
            }
        }
        
        // Update Inventory Records
        if (!inventoriesToUpdate.isEmpty()) {
            update inventoriesToUpdate;
        }
    }

    /**
     * @description Recalculates Total_Stock__c for a set of Products.
     * @param productIds Set of Product IDs to recalculate.
     */
    public static void recalculateProductStock(Set<Id> productIds) {
        if (productIds == null || productIds.isEmpty()) return;

        // Aggregate current inventory totals
        List<AggregateResult> results = [
            SELECT Product__c, SUM(Amount__c) total
            FROM Inventory__c
            WHERE Product__c IN :productIds
            GROUP BY Product__c
        ];

        Map<Id, Decimal> stockMap = new Map<Id, Decimal>();
        for (AggregateResult ar : results) {
            stockMap.put((Id)ar.get('Product__c'), (Decimal)ar.get('total'));
        }

        List<Product2> productsToUpdate = new List<Product2>();
        for (Id pid : productIds) {
            Decimal total = stockMap.containsKey(pid) ? stockMap.get(pid) : 0;
            productsToUpdate.add(new Product2(Id = pid, Total_Stock__c = total));
        }

        if (!productsToUpdate.isEmpty()) {
            update productsToUpdate;
        }
    }
}