@isTest
private class InventoryManagerTest {
    
    @testSetup
    static void setupData() {
        // Create Product
        Product2 p = new Product2(Name = 'Test Peptide', IsActive = true);
        insert p;
        
        // Create PricebookEntry for Order
        Id pricebookId = Test.getStandardPricebookId();
        PricebookEntry pbe = new PricebookEntry(
            Pricebook2Id = pricebookId, 
            Product2Id = p.Id, 
            UnitPrice = 100, 
            IsActive = true
        );
        insert pbe;
        
        // Create Inventory Batches (FEFO setup)
        List<Inventory__c> inventories = new List<Inventory__c>();
        
        // Batch 1: Expires SOON (Should be used first)
        inventories.add(new Inventory__c(
            Product__c = p.Id,
            Amount__c = 10,
            Expiration_Date__c = Date.today().addDays(10),
            Batch_Number__c = 'BATCH-SOON'
        ));
        
        // Batch 2: Expires LATER (Should be used second)
        inventories.add(new Inventory__c(
            Product__c = p.Id,
            Amount__c = 20,
            Expiration_Date__c = Date.today().addDays(100),
            Batch_Number__c = 'BATCH-LATER'
        ));
        
        insert inventories;
    }
    
    @isTest
    static void testSingleBatchDecrement() {
        Product2 p = [SELECT Id FROM Product2 LIMIT 1];
        PricebookEntry pbe = [SELECT Id FROM PricebookEntry WHERE Product2Id = :p.Id LIMIT 1];
        
        // Create Order
        Order o = new Order(
            AccountId = Test.getStandardPricebookId() != null ? null : null, // Skipping Account as it's not strictly needed if we mock right, but let's create one if needed usually
            EffectiveDate = Date.today(),
            Status = 'Draft',
            Pricebook2Id = Test.getStandardPricebookId()
        );
        // We need an Account for an Order usually
        Account a = new Account(Name = 'Test Account', Patient_Email__c='test@example.com');
        insert a;
        o.AccountId = a.Id;
        insert o;
        
        // Order 5 units
        OrderItem oi = new OrderItem(
            OrderId = o.Id,
            PricebookEntryId = pbe.Id,
            Product2Id = p.Id,
            Quantity = 5,
            UnitPrice = 100
        );
        insert oi;
        
        // ACT
        Test.startTest();
        o.Status = 'Activated';
        update o;
        Test.stopTest();
        
        // ASSERT
        Inventory__c batchSoon = [SELECT Amount__c FROM Inventory__c WHERE Batch_Number__c = 'BATCH-SOON'];
        Inventory__c batchLater = [SELECT Amount__c FROM Inventory__c WHERE Batch_Number__c = 'BATCH-LATER'];
        
        // Should have taken 5 from "SOON" (10 -> 5)
        System.assertEquals(5, batchSoon.Amount__c, 'Batch SOON should be decremented by 5');
        // Should have NOT touched "LATER" (20 -> 20)
        System.assertEquals(20, batchLater.Amount__c, 'Batch LATER should be untouched');
    }
    
    @isTest
    static void testMultiBatchDecrement() {
        Product2 p = [SELECT Id FROM Product2 LIMIT 1];
        PricebookEntry pbe = [SELECT Id FROM PricebookEntry WHERE Product2Id = :p.Id LIMIT 1];
        Account a = [SELECT Id FROM Account LIMIT 1]; // Assume one from setup or re-create
        if(a == null) { a = new Account(Name='Test', Patient_Email__c='test@example.com'); insert a; }
        
        Order o = new Order(AccountId = a.Id, EffectiveDate = Date.today(), Status = 'Draft', Pricebook2Id = Test.getStandardPricebookId());
        insert o;
        
        // Order 15 units (Takes all 10 from SOON, and 5 from LATER)
        OrderItem oi = new OrderItem(OrderId = o.Id, PricebookEntryId = pbe.Id, Product2Id = p.Id, Quantity = 15, UnitPrice = 100);
        insert oi;
        
        Test.startTest();
        o.Status = 'Activated';
        update o;
        Test.stopTest();
        
        Inventory__c batchSoon = [SELECT Amount__c FROM Inventory__c WHERE Batch_Number__c = 'BATCH-SOON'];
        Inventory__c batchLater = [SELECT Amount__c FROM Inventory__c WHERE Batch_Number__c = 'BATCH-LATER'];
        
        System.assertEquals(0, batchSoon.Amount__c, 'Batch SOON should be empty');
        System.assertEquals(15, batchLater.Amount__c, 'Batch LATER should have 15 remaining (20 - 5)');
    }
    
    @isTest
    static void testInsufficientInventory() {
        Product2 p = [SELECT Id FROM Product2 LIMIT 1];
        PricebookEntry pbe = [SELECT Id FROM PricebookEntry WHERE Product2Id = :p.Id LIMIT 1];
        Account a = new Account(Name='Test', Patient_Email__c='test@example.com'); insert a;
        
        Order o = new Order(AccountId = a.Id, EffectiveDate = Date.today(), Status = 'Draft', Pricebook2Id = Test.getStandardPricebookId());
        insert o;
        
        // Order 100 units (Only 30 available)
        OrderItem oi = new OrderItem(OrderId = o.Id, PricebookEntryId = pbe.Id, Product2Id = p.Id, Quantity = 100, UnitPrice = 100);
        insert oi;
        
        Test.startTest();
        try {
            o.Status = 'Activated';
            update o;
            System.assert(false, 'Should have thrown exception');
        } catch (Exception e) {
            System.assert(e.getMessage().contains('Insufficient inventory'), 'Expected insufficient inventory error: ' + e.getMessage());
        }
        Test.stopTest();
    }
    
    @isTest
    static void testStockRollup() {
        Product2 p = new Product2(Name = 'Rollup Test', IsActive = true);
        insert p;
        
        Test.startTest();
        
        // 1. Insert Inventory (10)
        Inventory__c i1 = new Inventory__c(Product__c = p.Id, Amount__c = 10, Batch_Number__c = 'A1');
        insert i1;
        
        Product2 pCheck = [SELECT Total_Stock__c FROM Product2 WHERE Id = :p.Id];
        System.assertEquals(10, pCheck.Total_Stock__c, 'Total Stock should be 10 after insert');
        
        // 2. Insert Another (20) -> Total 30
        Inventory__c i2 = new Inventory__c(Product__c = p.Id, Amount__c = 20, Batch_Number__c = 'A2');
        insert i2;
        
        pCheck = [SELECT Total_Stock__c FROM Product2 WHERE Id = :p.Id];
        System.assertEquals(30, pCheck.Total_Stock__c, 'Total Stock should be 30 after second insert');
        
        // 3. Update Amount (20 -> 5) -> Total 15
        i2.Amount__c = 5;
        update i2;
        
        pCheck = [SELECT Total_Stock__c FROM Product2 WHERE Id = :p.Id];
        System.assertEquals(15, pCheck.Total_Stock__c, 'Total Stock should be 15 after update');
        
        // 4. Delete One -> Total 10
        delete i2;
        
        pCheck = [SELECT Total_Stock__c FROM Product2 WHERE Id = :p.Id];
        System.assertEquals(10, pCheck.Total_Stock__c, 'Total Stock should be 10 after delete');
        
        Test.stopTest();
    }

    @isTest
    static void testSameDayExpiration() {
        Product2 p = [SELECT Id FROM Product2 LIMIT 1];
        PricebookEntry pbe = [SELECT Id FROM PricebookEntry WHERE Product2Id = :p.Id LIMIT 1];
        Account a = new Account(Name='Test', Patient_Email__c='test@example.com'); insert a;
        
        // 1. Create Two Batches with SAME Expiration Date
        Date expDate = Date.today().addDays(365);
        
        Inventory__c batchOld = new Inventory__c(
            Product__c = p.Id, Amount__c = 5, Expiration_Date__c = expDate, Batch_Number__c = 'OLD-BATCH'
        );
        insert batchOld;
        
        // Wait a bit to ensure CreatedDate is different (in real life this is automatic, in test we rely on execution order)
        Inventory__c batchNew = new Inventory__c(
            Product__c = p.Id, Amount__c = 5, Expiration_Date__c = expDate, Batch_Number__c = 'NEW-BATCH'
        );
        insert batchNew;
        
        // 2. Create Order for 3 Units
        Order o = new Order(AccountId = a.Id, EffectiveDate = Date.today(), Status = 'Draft', Pricebook2Id = Test.getStandardPricebookId());
        insert o;
        
        OrderItem oi = new OrderItem(OrderId = o.Id, PricebookEntryId = pbe.Id, Product2Id = p.Id, Quantity = 3, UnitPrice = 100);
        insert oi;
        
        Test.startTest();
        o.Status = 'Activated';
        update o;
        Test.stopTest();
        
        // 3. Verify: Should take from OLD-BATCH first (First In, First Out logic for same expiry)
        Inventory__c checkOld = [SELECT Amount__c FROM Inventory__c WHERE Id = :batchOld.Id];
        Inventory__c checkNew = [SELECT Amount__c FROM Inventory__c WHERE Id = :batchNew.Id];
        
        System.assertEquals(2, checkOld.Amount__c, 'Should take 3 from OLD batch (5-3=2)');
        System.assertEquals(5, checkNew.Amount__c, 'NEW batch should be untouched');
    }
}