public with sharing class OrderTriggerHandler {
    
    public static void onAfterUpdate(List<Order> newOrders, Map<Id, Order> oldOrders) {
        Set<Id> activatedOrderIds = new Set<Id>();
        
        for (Order newOrd : newOrders) {
            Order oldOrd = oldOrders.get(newOrd.Id);
            // Check if status changed to Activated
            if (newOrd.Status == 'Activated' && oldOrd.Status != 'Activated') {
                activatedOrderIds.add(newOrd.Id);
            }
        }
        
        if (!activatedOrderIds.isEmpty()) {
            processInventoryDecrement(activatedOrderIds);
        }
    }
    
    private static void processInventoryDecrement(Set<Id> orderIds) {
        // Query OrderItems to identify what products need to be deducted
        List<OrderItem> orderItems = [
            SELECT Id, Product2Id, Quantity 
            FROM OrderItem 
            WHERE OrderId IN :orderIds
        ];
        
        if (!orderItems.isEmpty()) {
            InventoryManager.decrementInventory(orderItems);
        }
    }
}