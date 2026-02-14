trigger ProductStripeTrigger on Product2 (after insert, after update) {
    StripeSyncHandler.handleProductChange(Trigger.new, Trigger.oldMap);
}