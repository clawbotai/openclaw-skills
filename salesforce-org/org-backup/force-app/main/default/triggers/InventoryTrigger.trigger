trigger InventoryTrigger on Inventory__c (after insert, after update, after delete, after undelete) {
    if (Trigger.isAfter) {
        if (Trigger.isInsert) {
            InventoryTriggerHandler.onAfterInsert(Trigger.new);
        } else if (Trigger.isUpdate) {
            InventoryTriggerHandler.onAfterUpdate(Trigger.new, Trigger.oldMap);
        } else if (Trigger.isDelete) {
            InventoryTriggerHandler.onAfterDelete(Trigger.old);
        } else if (Trigger.isUndelete) {
            InventoryTriggerHandler.onAfterUndelete(Trigger.new);
        }
    }
}