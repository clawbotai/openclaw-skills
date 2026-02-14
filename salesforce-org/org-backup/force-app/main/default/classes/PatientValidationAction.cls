public without sharing class PatientValidationAction {

    @InvocableMethod(label='Validate Patient' description='Validates the Patient Account and triggers User creation.')
    public static void validatePatient(List<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) return;
        
        // We handle one at a time effectively or loop, but Controller takes single ID.
        // It's safer to loop in case of bulk, though Flow usually passes one.
        for (Id accId : accountIds) {
            try {
                PatientValidationController.validatePatient(accId);
            } catch (Exception e) {
                System.debug('Error in PatientValidationAction for Account ' + accId + ': ' + e.getMessage());
                // We assume the controller handles its own logging/exceptions, 
                // but for Invocable we generally don't want to crash the whole transaction if one fails 
                // unless we want to roll back. 
            }
        }
    }
}