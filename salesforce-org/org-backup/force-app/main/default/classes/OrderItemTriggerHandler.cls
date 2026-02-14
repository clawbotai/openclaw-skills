public with sharing class OrderItemTriggerHandler {
    
    public static void onBeforeInsert(List<OrderItem> newItems) {
        validateItems(newItems);
    }
    
    public static void onBeforeUpdate(List<OrderItem> newItems, Map<Id, OrderItem> oldItems) {
        validateItems(newItems);
    }
    
    private static void validateItems(List<OrderItem> items) {
        // Collect Product Ids
        Set<Id> productIds = new Set<Id>();
        for (OrderItem item : items) {
            if (item.Product2Id != null) {
                productIds.add(item.Product2Id);
            }
        }
        
        if (productIds.isEmpty()) return;
        
        // Query Product Details necessary for validation
        Map<Id, Product2> productsMap = new Map<Id, Product2>([
            SELECT Id, Name, Unit_Standard__c, Mg_Per_Vial__c, IU_Per_Vial__c, 
                   Dilution_Liquid_Volume_ml__c, Hard_Deck_Limit_Mass__c, Hard_Deck_Limit_IU__c,
                   Default_Syringe_Type__c, Spray_Volume_ml__c, Volume_Per_Vial_ml__c
            FROM Product2
            WHERE Id IN :productIds
        ]);
        
        // Validate each item
        for (OrderItem item : items) {
            if (productsMap.containsKey(item.Product2Id)) {
                Product2 p = productsMap.get(item.Product2Id);
                PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
                
                // Update System Fields
                item.Safety_Check_Status__c = result.status;
                if (result.calculatedUnits != null) {
                    item.Calculated_Syringe_Units__c = result.calculatedUnits;
                }
                
                // Handle Failures
                if (!result.isValid) {
                     // BLOCK the save if CRITICAL FAIL
                     // Requirement implies "The system Flags the Doctor... -> Doctor updates"
                     // Ideally we addError, but maybe for FLAGGED we just let it pass with status?
                     // "Strict Validation: The system will block orders... if ... varies" 
                     // Let's AddError for FAIL.
                     item.addError(result.message);
                } else if (result.status == 'FLAGGED') {
                    // For Warnings (like the unit mismatch 15 vs 20), we might want to allow save but mark it?
                    // The scenario says "System flags the doctor... Please confirm."
                    // In a Trigger context, addError stops execution. 
                    // To "Confirm", the doctor would change the value.
                    // So we addError even for FLAGS to force correction?
                    // "Correction: The system Flags the Doctor... Doctor updates to 20 Units."
                    // Yes, addError seems appropriate for the "Interactive" feeling in a trigger, 
                    // forcing the UI to show the message.
                    item.addError(result.message);
                }
            }
        }
    }
}