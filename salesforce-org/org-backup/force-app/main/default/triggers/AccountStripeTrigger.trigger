trigger AccountStripeTrigger on Account (after insert, after update) {
    StripeSyncHandler.handleAccountChange(Trigger.new, Trigger.oldMap);
}