@isTest(SeeAllData=true)
public class DebugPortalAccessTest {
    @isTest
    static void reproduceError() {
        try {
            User u = [SELECT Id FROM User WHERE Name = 'Manuel stripe' LIMIT 1];
            System.runAs(u) {
                System.debug('Running as: ' + u.Id);
                try {
                    DoctorPortalController.HubInfo hub = DoctorPortalController.getHubRecord();
                    System.debug('Result: ' + hub);
                } catch (Exception e) {
                    System.debug('CAPTURED EXCEPTION: ' + e.getMessage());
                    System.debug('STACK TRACE: ' + e.getStackTraceString());
                }
            }
        } catch (Exception e) {
            System.debug('SETUP ERROR: ' + e.getMessage());
        }
    }
}