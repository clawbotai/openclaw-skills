@isTest
private class PeptideSafetyGapTest {

    @isTest
    static void testZombieOrder_NullSchedule() {
        // SCENARIO 1: The Zombie Order
        // Product is a Peptide (Mass Mg), but Doctor forgots to pick a Schedule Mode.
        // Current Logic: Validator doesn't check if Schedule Mode is null.
        // Expectation: Should FAIL (Missing Schedule).
        // Current Failure: Likely PASSES.
        
        Product2 p = new Product2(
            Name = 'be. titan',
            Unit_Standard__c = 'MASS_MG',
            Mg_Per_Vial__c = 5.00,
            Dilution_Liquid_Volume_ml__c = 2.00
        );
        
        OrderItem item = new OrderItem(
            Daily_Dosage_mg__c = 0.500,
            Doctor_Prescribed_Units__c = 20,
            Quantity = 2,
            Schedule_Mode__c = null // OOPS!
        );

        Test.startTest();
        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        Test.stopTest();

        // If this Assert fails, it means the system allowed the Zombie Order (Bad).
        System.assertEquals(false, result.isValid, 'Gap Found: System allowed an order with NO Schedule Mode!');
    }

    @isTest
    static void testMalformedJSON_FixedDays() {
        // SCENARIO 2: The Crashy JSON
        // Fixed Days Selected, but mask is garbage string.
        // Expectation: Should FAIL or handle safely.
        // Current Failure: Validator likely only checks String.isBlank().
        
        Product2 p = new Product2(Name='P', Unit_Standard__c='MASS_MG', Mg_Per_Vial__c=5, Dilution_Liquid_Volume_ml__c=2);
        
        OrderItem item = new OrderItem(
            Daily_Dosage_mg__c=0.5, Doctor_Prescribed_Units__c=20,
            Schedule_Mode__c = 'FIXED_DAYS',
            Day_Mask_JSON__c = 'THIS IS NOT JSON' // Malformed
        );
        
        Test.startTest();
        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        Test.stopTest();
        
        System.assertEquals(false, result.isValid, 'Gap Found: System accepted malformed JSON!');
    }
}