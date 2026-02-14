trigger OrderStripeTrigger on Order (after update) {
    StripeSyncHandler.handleOrderChange(Trigger.new, Trigger.oldMap);
}