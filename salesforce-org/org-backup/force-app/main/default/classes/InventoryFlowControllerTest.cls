@isTest
public class InventoryFlowControllerTest {
    
    @isTest
    static void testDeduplicationLogic() {
        // Setup Data
        Product2 p = new Product2(Name = 'Test Product', IsActive = true);
        insert p;
        
        // Create Inventory Records
        List<Inventory__c> invList = new List<Inventory__c>();
        
        // Item 1: Mass 20, Expires later
        invList.add(new Inventory__c(
            Product__c = p.Id,
            Mass__c = 20,
            Expiration_Date__c = Date.today().addDays(30),
            Amount__c = 10,
            Batch_Number__c = 'LOT-A'
        ));
        
        // Item 2: Mass 20, Expires sooner (Should be picked)
        invList.add(new Inventory__c(
            Product__c = p.Id,
            Mass__c = 20,
            Expiration_Date__c = Date.today().addDays(10),
            Amount__c = 10,
            Batch_Number__c = 'LOT-B'
        ));
        
        // Item 3: Mass 10 (Unique)
        invList.add(new Inventory__c(
            Product__c = p.Id,
            Mass__c = 10,
            Expiration_Date__c = Date.today().addDays(20),
            Amount__c = 10,
            Batch_Number__c = 'LOT-C'
        ));
        
        insert invList;
        
        Test.startTest();
        List<List<Inventory__c>> results = InventoryFlowController.getUniqueInventoryOptions(new List<Id>{p.Id});
        Test.stopTest();
        
        System.assertEquals(1, results.size(), 'Should return 1 list of results');
        List<Inventory__c> options = results[0];
        
        System.assertEquals(2, options.size(), 'Should have 2 unique options (Mass 10 and 20)');
        
        // Verify Sorting by Mass (10 then 20)
        System.assertEquals(10, options[0].Mass__c);
        System.assertEquals(20, options[1].Mass__c);
        
        // Verify "Best" Record Selection for Mass 20
        // LOT-B expires in 10 days, LOT-A in 30. LOT-B should be selected.
        System.assertEquals('LOT-B', options[1].Batch_Number__c, 'Should pick the inventory with earliest expiration date');
    }
}