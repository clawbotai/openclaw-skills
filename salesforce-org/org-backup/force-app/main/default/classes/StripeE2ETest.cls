@isTest
private class StripeE2ETest {

    @TestSetup
    static void makeData(){
        Account acc = new Account(Name='Test Patient', Patient_Email__c='test@example.com');
        insert acc;
        
        Product2 prod = new Product2(Name='Consultation', IsActive=true, Unit_Standard__c = null);
        insert prod;
        
        PricebookEntry pbe = new PricebookEntry(
            Pricebook2Id = Test.getStandardPricebookId(),
            Product2Id = prod.Id,
            UnitPrice = 100,
            IsActive = true
        );
        insert pbe;

        Inventory__c inv = new Inventory__c(
            Product__c = prod.Id,
            Amount__c = 1000,
            Expiration_Date__c = Date.today().addDays(365),
            Batch_Number__c = 'BATCH-TEST-001'
        );
        insert inv;
    }

    // Mock for Stripe API Calls
    public class StripeHttpMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setHeader('Content-Type', 'application/json');
            res.setStatusCode(200);
            
            String endpoint = req.getEndpoint();
            
            if (endpoint.contains('/v1/customers')) {
                res.setBody('{"id": "cus_test123", "email": "test@example.com"}');
            } else if (endpoint.contains('/v1/payment_links')) {
                // Return a mock Payment Link response
                res.setBody('{"url": "https://buy.stripe.com/test_link_123", "id": "plink_123"}');
            } else {
                res.setBody('{}');
            }
            return res;
        }
    }

    @isTest
    static void testOutboundOrderLinkGeneration() {
        // user story: When Order is 'Waiting for Payment', create Stripe Link
        
        Test.setMock(HttpCalloutMock.class, new StripeHttpMock());
        
        Account acc = [SELECT Id FROM Account LIMIT 1];
        Product2 prod = [SELECT Id FROM Product2 LIMIT 1];
        PricebookEntry pbe = [SELECT Id, Pricebook2Id FROM PricebookEntry LIMIT 1];
        
        Order ord = new Order(
            AccountId = acc.Id, 
            Status = 'Draft', 
            EffectiveDate = Date.today(), 
            Pricebook2Id = pbe.Pricebook2Id
        );
        insert ord;
        
        OrderItem oi = new OrderItem(
            OrderId = ord.Id,
            PricebookEntryId = pbe.Id,
            Quantity = 1,
            UnitPrice = 100
        );
        insert oi;
        
        // ACT
        Test.startTest();
        ord.Status = 'Waiting for Payment';
        update ord;
        Test.stopTest(); // Forces async future methods to run
        
        // ASSERT
        Order updatedOrd = [SELECT Id, Stripe_Payment_Link__c FROM Order WHERE Id = :ord.Id];
        System.assertNotEquals(null, updatedOrd.Stripe_Payment_Link__c, 'Payment Link should be generated');
        System.assert(updatedOrd.Stripe_Payment_Link__c.contains('client_reference_id=' + ord.Id), 'Link must contain client_reference_id');
    }

    @isTest
    static void testInboundWebhookSuccess() {
        // user story: Webhook with valid client_reference_id marks Order as Paid
        
        Account acc = [SELECT Id FROM Account LIMIT 1];
        Order ord = new Order(
            AccountId = acc.Id, 
            Status = 'Waiting for Payment', 
            EffectiveDate = Date.today(),
            Pricebook2Id = Test.getStandardPricebookId()
        );
        insert ord;

        // Add OrderItem to allow Activation
        PricebookEntry pbe = [SELECT Id FROM PricebookEntry LIMIT 1];
        OrderItem oi = new OrderItem(
            OrderId = ord.Id,
            PricebookEntryId = pbe.Id,
            Quantity = 1,
            UnitPrice = 100
        );
        insert oi;
        
        String payload = '{' +
            '"type": "checkout.session.completed",' +
            '"data": {' +
                '"object": {' +
                    '"client_reference_id": "' + ord.Id + '",' +
                    '"payment_intent": "pi_test123",' +
                    '"payment_status": "paid"' +
                '}' +
            '}' +
        '}';
        
        RestRequest req = new RestRequest();
        req.requestURI = '/services/apexrest/stripe/webhooks/';
        req.httpMethod = 'POST';
        req.requestBody = Blob.valueOf(payload);
        RestContext.request = req;
        RestContext.response = new RestResponse();
        
        // ACT
        Test.startTest();
        StripeWebhookHandler.handleIncomingWebhook();
        Test.stopTest();
        
        // ASSERT
        Order updatedOrd = [SELECT Id, Status, Stripe_Payment_Intent__c FROM Order WHERE Id = :ord.Id];
        System.assertEquals('Activated', updatedOrd.Status, 'Order status should be Activated');
        System.assertEquals('pi_test123', updatedOrd.Stripe_Payment_Intent__c, 'Payment Intent should be saved');
    }

    @isTest
    static void testInboundWebhookInvalidId() {
        // Edge Case: client_reference_id is "garbage"
        
        String payload = '{' +
            '"type": "checkout.session.completed",' +
            '"data": {' +
                '"object": {' +
                    '"client_reference_id": "NOT_AN_ID",' +
                    '"payment_intent": "pi_test123"' +
                '}' +
            '}' +
        '}';
        
        RestRequest req = new RestRequest();
        req.requestURI = '/services/apexrest/stripe/webhooks/';
        req.httpMethod = 'POST';
        req.requestBody = Blob.valueOf(payload);
        RestContext.request = req;
        RestContext.response = new RestResponse();
        
        Test.startTest();
        StripeWebhookHandler.handleIncomingWebhook();
        Test.stopTest();
        
        // Should return 200 (acknowledged) but log error debug internally
        // We assert it didn't crash
        System.assertEquals(200, RestContext.response.statusCode);
    }
    
    @isTest
    static void testInboundWebhookOrphanedId() {
        // Edge Case: client_reference_id is a valid ID but order deleted/missing
         
        // Create dummy ID (using Account simply to get a valid ID format, purely as a mock)
        // Or better, create order and delete it
        Account acc = [SELECT Id FROM Account LIMIT 1];
        Order ord = new Order(AccountId=acc.Id, EffectiveDate=Date.today(), Status='Draft', Pricebook2Id=Test.getStandardPricebookId());
        insert ord;
        Id deletedId = ord.Id;
        delete ord;

        String payload = '{' +
            '"type": "checkout.session.completed",' +
            '"data": {' +
                '"object": {' +
                    '"client_reference_id": "' + deletedId + '"' +
                '}' +
            '}' +
        '}';
        
        RestRequest req = new RestRequest();
        req.requestBody = Blob.valueOf(payload);
        RestContext.request = req;
        RestContext.response = new RestResponse();
        
        Test.startTest();
        StripeWebhookHandler.handleIncomingWebhook();
        Test.stopTest();
        
        System.assertEquals(200, RestContext.response.statusCode);
    }
}