trigger OrderItemTrigger on OrderItem (before insert, before update) {
    if (Trigger.isBefore) {
        if (Trigger.isInsert) {
            OrderItemTriggerHandler.onBeforeInsert(Trigger.new);
        } else if (Trigger.isUpdate) {
            OrderItemTriggerHandler.onBeforeUpdate(Trigger.new, Trigger.oldMap);
        }
    }
}