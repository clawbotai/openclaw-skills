trigger OrderTrigger on Order (after update) {
    if (Trigger.isAfter && Trigger.isUpdate) {
        OrderTriggerHandler.onAfterUpdate(Trigger.new, Trigger.oldMap);
    }
}