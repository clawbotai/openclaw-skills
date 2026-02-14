@isTest
private class PeptideSafetyServiceTest {

    @isTest
    static void testBeTitanScenario_Pass() {
        // Setup Product: "be. titan"
        Product2 p = new Product2(
            Name = 'be. titan',
            Unit_Standard__c = 'MASS_MG',
            Mg_Per_Vial__c = 5.00,
            Dilution_Liquid_Volume_ml__c = 2.00, // 2.5mg/ml
            Hard_Deck_Limit_Mass__c = 15.00
        );
        
        // Setup Order Item: 500mcg (0.5mg) -> 0.2ml -> 20 Units
        // Added valid Schedule: Fixed Days
        OrderItem item = new OrderItem(
            Daily_Dosage_mg__c = 0.500,
            Doctor_Prescribed_Units__c = 20,
            Quantity = 2,
            Frequency_Type__c = 'Fixed',
            Schedule_Mode__c = 'FIXED_DAYS',
            Day_Mask_JSON__c = '["MON", "WED", "FRI"]',
            Anchor_Type__c = 'BIO_EVENT',
            Bio_Trigger__c = 'PRE_BED'
        );

        Test.startTest();
        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        Test.stopTest();

        System.assert(result.isValid, 'Order should PASS: ' + result.message);
        System.assertEquals(20, result.calculatedUnits, 'Calculated units should be 20');
        System.assertEquals('PASS', result.status, 'Status should be PASS');
    }

    @isTest
    static void testBeTitanScenario_Fail_Units() {
        // Setup Product
        Product2 p = new Product2(
            Name = 'be. titan',
            Unit_Standard__c = 'MASS_MG',
            Mg_Per_Vial__c = 5.00,
            Dilution_Liquid_Volume_ml__c = 2.00
        );
        
        // Setup Order Item: 500mcg -> 20 Units. Doctor inputs 15.
        // Valid Schedule for this test
        OrderItem item = new OrderItem(
            Daily_Dosage_mg__c = 0.500,
            Doctor_Prescribed_Units__c = 15,
            Quantity = 2,
            Schedule_Mode__c = 'FIXED_DAYS',
            Day_Mask_JSON__c = '["MON"]'
        );

        Test.startTest();
        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        Test.stopTest();

        System.assertEquals(false, result.isValid, 'Should be Invalid due to unit mismatch');
        System.assertEquals('FLAGGED', result.status, 'Status should be FLAGGED');
        System.assert(result.message.contains('Units, not 15'), 'Message should mention mismatch');
    }

    @isTest
    static void testHardDeckLimit() {
        Product2 p = new Product2(Name='Strong Stuff', Unit_Standard__c='MASS_MG', Mg_Per_Vial__c=10, Dilution_Liquid_Volume_ml__c=1, Hard_Deck_Limit_Mass__c=15);
        // Order 2 vials = 20mg Total Load. Limit is 15.
        OrderItem item = new OrderItem(
            Quantity=2, Daily_Dosage_mg__c=1, Doctor_Prescribed_Units__c=10, 
            Schedule_Mode__c='ROLLING_INTERVAL', Interval_Gap_Days__c=2
        );

        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        
        System.assertEquals(false, result.isValid);
        System.assertEquals('FAIL', result.status);
        System.assert(result.message.contains('exceeds Hard Deck'), 'Should fail hard deck');
    }

    @isTest
    static void testTitrationLogic() {
        Product2 p = new Product2(
            Name='be. lucid', Mg_Per_Vial__c=10, Dilution_Liquid_Volume_ml__c=2, Unit_Standard__c='MASS_MG'
        );
        // Concentration = 5 mg/ml.
        
        // Titration: Day 1: 100mcg (0.1mg).
        // 0.1mg / 5 = 0.02ml = 2 Units.
        String jsonPlan = '[{"days":1, "dose_mcg":100, "units":2}]';
        
        OrderItem item = new OrderItem(
            Frequency_Type__c = 'Titration',
            Schedule_Mode__c = 'TITRATION',
            Titration_Plan_JSON__c = jsonPlan,
            Quantity = 1
        );

        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        
        System.assert(result.isValid, 'Titration should valid: ' + result.message);
    }
    
    @isTest
    static void testLiquidStandard() {
        Product2 p = new Product2(
            Name='Semax', Unit_Standard__c='FIXED_LIQUID', Spray_Volume_ml__c=0.1, Volume_Per_Vial_ml__c=10
        );
        OrderItem item = new OrderItem(
            Daily_Dosage_Puffs__c=2, Quantity=1,
            Schedule_Mode__c='FIXED_DAYS', Day_Mask_JSON__c='["MON"]'
        );
        
        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        
        System.assert(result.isValid);
        System.assert(result.message.contains('Volume Usage'), 'Should calc volume');
    }

    // --- NEW DOSING ARCHITECTURE TESTS ---

    @isTest
    static void testFixedDaysValidation() {
        Product2 p = new Product2(
            Name='be. essential', Unit_Standard__c='MASS_MG', Mg_Per_Vial__c=5, Dilution_Liquid_Volume_ml__c=2
        );
        
        // 1. Missing Day Mask -> FAIL
        OrderItem itemFail = new OrderItem(
            Daily_Dosage_mg__c=0.5, Doctor_Prescribed_Units__c=20,
            Schedule_Mode__c = 'FIXED_DAYS',
            Day_Mask_JSON__c = ''
        );
        PeptideSafetyService.ValidationResult resFail = PeptideSafetyService.validateLineItem(itemFail, p);
        System.assertEquals(false, resFail.isValid);
        System.assert(resFail.message.contains('Fixed Days mode requires a Day Mask'), 'Msg: ' + resFail.message);
        
        // 2. Valid Day Mask -> PASS
        OrderItem itemPass = new OrderItem(
            Daily_Dosage_mg__c=0.5, Doctor_Prescribed_Units__c=20,
            Schedule_Mode__c = 'FIXED_DAYS',
            Day_Mask_JSON__c = '["MON", "WED"]'
        );
        PeptideSafetyService.ValidationResult resPass = PeptideSafetyService.validateLineItem(itemPass, p);
        System.assert(resPass.isValid, 'Should be valid with mask');
    }

    @isTest
    static void testRollingIntervalValidation() {
        Product2 p = new Product2(
            Name='be. rolling', Unit_Standard__c='MASS_MG', Mg_Per_Vial__c=5, Dilution_Liquid_Volume_ml__c=2
        );
        
        // 1. Missing Gap -> FAIL
        OrderItem itemFail = new OrderItem(
            Daily_Dosage_mg__c=0.5, Doctor_Prescribed_Units__c=20,
            Schedule_Mode__c = 'ROLLING_INTERVAL',
            Interval_Gap_Days__c = null
        );
        PeptideSafetyService.ValidationResult resFail = PeptideSafetyService.validateLineItem(itemFail, p);
        System.assertEquals(false, resFail.isValid);
        System.assert(resFail.message.contains('Rolling Interval requires a positive Gap'), 'Msg: ' + resFail.message);
        
        // 2. Valid Gap -> PASS
        OrderItem itemPass = new OrderItem(
            Daily_Dosage_mg__c=0.5, Doctor_Prescribed_Units__c=20,
            Schedule_Mode__c = 'ROLLING_INTERVAL',
            Interval_Gap_Days__c = 2
        );
        PeptideSafetyService.ValidationResult resPass = PeptideSafetyService.validateLineItem(itemPass, p);
        System.assert(resPass.isValid);
    }
    
    @isTest
    static void testAnchors() {
        Product2 p = new Product2(
            Name='be. anchored', Unit_Standard__c='MASS_MG', Mg_Per_Vial__c=5, Dilution_Liquid_Volume_ml__c=2
        );
        
        // 1. Clock Time check (Flagged if missing)
        OrderItem itemClock = new OrderItem(
            Daily_Dosage_mg__c=0.5, Doctor_Prescribed_Units__c=20,
            Schedule_Mode__c = 'FIXED_DAYS', Day_Mask_JSON__c = '["MON"]',
            Anchor_Type__c = 'CLOCK_TIME', Target_Time_UTC__c = null
        );
        PeptideSafetyService.ValidationResult resClock = PeptideSafetyService.validateLineItem(itemClock, p);
        System.assertEquals('FLAGGED', resClock.status, 'Should flag missing time ' + resClock.message);
        
        // 2. Bio Event check (Fail if missing)
        OrderItem itemBio = new OrderItem(
            Daily_Dosage_mg__c=0.5, Doctor_Prescribed_Units__c=20,
            Schedule_Mode__c = 'FIXED_DAYS', Day_Mask_JSON__c = '["MON"]',
            Anchor_Type__c = 'BIO_EVENT', Bio_Trigger__c = ''
        );
        PeptideSafetyService.ValidationResult resBio = PeptideSafetyService.validateLineItem(itemBio, p);
        System.assertEquals(false, resBio.isValid);
        System.assert(resBio.message.contains('Bio Trigger provided'), 'Msg: ' + resBio.message);
    }

    @isTest
    static void testGoldStandardCase_Compliance() {
        // SCENARIO: GSC Phantom Order (Flow created)
        // Now fully compliant with Dosing Architecture (No Exemption Needed).
        // Flow maps these fields from the GSC Template.
        
        Product2 p = new Product2(Name='P', Unit_Standard__c='MASS_MG', Mg_Per_Vial__c=5, Dilution_Liquid_Volume_ml__c=2);
        insert p; 
        
        Account a = new Account(Name='Test Doc', Patient_Email__c='test@example.com');
        insert a;
        
        Order o = new Order(
            AccountId=a.Id, 
            EffectiveDate=Date.today(), 
            Status='Draft', 
            Is_Gold_Standard_Case__c=true
        );
        insert o;
        
        OrderItem item = new OrderItem(
            OrderId = o.Id,
            Quantity = 1,
            Daily_Dosage_mg__c = 0.5,
            Doctor_Prescribed_Units__c = 20, // 0.5mg of 5mg/2ml (2.5mg/ml) = 0.2ml = 20 Units
            // Compliance Fields (Simulating Flow Mapping)
            Schedule_Mode__c = 'FIXED_DAYS',
            Day_Mask_JSON__c = '["MON", "WED", "FRI"]',
            Anchor_Type__c = 'BIO_EVENT',
            Bio_Trigger__c = 'UPON_WAKING'
        );
        
        Test.startTest();
        PeptideSafetyService.ValidationResult result = PeptideSafetyService.validateLineItem(item, p);
        Test.stopTest();
        
        System.assert(result.isValid, 'GSC Order should PASS as a valid compliant order: ' + result.message);
    }
}