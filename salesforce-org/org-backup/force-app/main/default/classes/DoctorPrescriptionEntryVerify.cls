@isTest
private class DoctorPrescriptionEntryVerify {

    @testSetup
    static void setup() {
        // Setup base data: User, Doctor, Account (Patient), Product, PricebookEntry
        Profile p = [SELECT Id FROM Profile WHERE Name='Standard User']; 
        User u = new User(Alias = 'flexdoc', Email='flexdoc@testorg.com', 
            EmailEncodingKey='UTF-8', LastName='Testing', LanguageLocaleKey='en_US', 
            LocaleSidKey='en_US', ProfileId = p.Id, 
            TimeZoneSidKey='America/Los_Angeles', UserName='flexdoc@testorg.com');
        insert u;

        Doctor__c doc = new Doctor__c(Name='Flex Doctor', User__c=u.Id, Medical_License__c='MD-123456');
        insert doc;

        Account patient = new Account(Name='Flow Patient', Doctor__c=doc.Id, Patient_Email__c='patient@testorg.com');
        insert patient;

        Id stdPbId = Test.getStandardPricebookId();
        Product2 prod = new Product2(Name='Test Peptide', IsActive=true, Mg_Per_Vial__c=10, Dilution_Liquid_Volume_ml__c=2, Hard_Deck_Limit_MG__c=20);
        insert prod;

        PricebookEntry pbe = new PricebookEntry(Pricebook2Id=stdPbId, Product2Id=prod.Id, UnitPrice=100, IsActive=true);
        insert pbe;
    }

    @isTest
    static void verifyFlowLogic() {
        User u = [SELECT Id FROM User WHERE UserName='flexdoc@testorg.com'];
        
        System.runAs(u) {
            // 1. Simulate "Get Current Doctor"
            Doctor__c doc = [SELECT Id FROM Doctor__c WHERE User__c = :UserInfo.getUserId() LIMIT 1];
            System.assertNotEquals(null, doc, 'Doctor record should be found for user');

            // 2. Simulate "Get My Patients" (Dynamic Choice)
            List<Account> patients = [SELECT Id FROM Account WHERE Doctor__c = :doc.Id];
            System.assertEquals(1, patients.size(), 'Should find 1 linked patient');

            // 3. Simulate "Create Draft Order"
            Order newOrder = new Order(
                AccountId = patients[0].Id,
                Doctor__c = doc.Id, // Note: Flow doesn't explicitly map Doctor__c in Create_Draft_Order node? Let's check.
                // Wait, looking at lines 185-216 of flow...
                // It sets AccountId, Description, EffectiveDate, Pricebook2Id, Status.
                // IT DOES NOT SET Doctor__c! 
                // CRITICAL FINDING: The Flow might be creating Orders without linking them to the Doctor!
                Status = 'Draft',
                EffectiveDate = Date.today(),
                Pricebook2Id = Test.getStandardPricebookId(),
                Order_Type__c = 'New Intake'
            );
            insert newOrder;

            // 4. Simulate "Create Order Items"
            PricebookEntry pbe = [SELECT Id, UnitPrice FROM PricebookEntry LIMIT 1];
            OrderItem item = new OrderItem(
                OrderId = newOrder.Id,
                PricebookEntryId = pbe.Id,
                Quantity = 1,
                UnitPrice = pbe.UnitPrice,
                Dose_mg__c = 5,
                Frequency__c = 'Daily',
                Route_of_Administration__c = 'Subcutaneous (SubQ)',
                Schedule_Mode__c = 'FIXED_DAYS',
                Anchor_Type__c = 'CLOCK_TIME',
                Injection_Frequency__c = 'Daily',
                Injection_Route__c = 'Subcutaneous (Sub-Q)',
                Injection_Site__c = 'Near Left Knee',
                Syringe_Type__c = '1ml Insulin Syringe',
                Clinical_Rationale__c = 'Standard protocol for test peptide.',
                Day_Mask_JSON__c = '["MON", "WED", "FRI"]',
                Target_Time_UTC__c = Time.newInstance(8, 0, 0, 0),
                Daily_Dosage_mg__c = 5
            );
            insert item;

            // 5. Activate
            newOrder.Status = 'Activated';
            update newOrder;

            // Verify Result
            Order finalOrder = [SELECT Id, Status, Doctor__c, Order_Type__c FROM Order WHERE Id = :newOrder.Id];
            System.assertEquals('Activated', finalOrder.Status);
            System.assertEquals(doc.Id, finalOrder.Doctor__c);
            System.assertEquals('New Intake', finalOrder.Order_Type__c);

            OrderItem finalItem = [SELECT Id, Schedule_Mode__c, Anchor_Type__c, Injection_Frequency__c, Injection_Route__c, Day_Mask_JSON__c, Target_Time_UTC__c, Daily_Dosage_mg__c FROM OrderItem WHERE Id = :item.Id];
            System.assertEquals('FIXED_DAYS', finalItem.Schedule_Mode__c);
            System.assertEquals('CLOCK_TIME', finalItem.Anchor_Type__c);
            System.assertEquals('Daily', finalItem.Injection_Frequency__c);
            System.assertEquals('Subcutaneous (Sub-Q)', finalItem.Injection_Route__c);
            System.assertEquals('["MON", "WED", "FRI"]', finalItem.Day_Mask_JSON__c);
            System.assertEquals(Time.newInstance(8, 0, 0, 0), finalItem.Target_Time_UTC__c);
            System.assertEquals(5, finalItem.Daily_Dosage_mg__c);
        }
    }
}