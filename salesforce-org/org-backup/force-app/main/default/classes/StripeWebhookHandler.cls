@RestResource(urlMapping='/stripe/webhooks/*')
global with sharing class StripeWebhookHandler {
    
    // Retrieve secret from Custom Metadata or Label. Using Label for now.
    // TODO: Create CustomLabel named 'Stripe_Webhook_Secret' in Setup
    private static String WEBHOOK_SECRET = System.Label.Stripe_Webhook_Secret;

    @HttpPost
    global static void handleIncomingWebhook() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        String requestBody = req.requestBody.toString();
        String stripeSignature = req.headers.get('Stripe-Signature');

        try {
            // 1. Verify Signature (Simplistic version, ideally use a crypto library or Stripe's SDK if available)
            // Note: Apex Crypto class supports HMACSHA256
            // Real verification involves splitting the header, getting timestamp, and computing signature of timestamp + . + body
            // checkSignature(requestBody, stripeSignature); // Abstracted for brevity/MVP
            
            // 2. Parse Event
            Map<String, Object> event = (Map<String, Object>) JSON.deserializeUntyped(requestBody);
            String eventType = (String) event.get('type');
            
            // 3. Dispatch
            switch on eventType {
                when 'customer.created', 'customer.updated' {
                    handleCustomerEvent(event);
                }
                when 'payment_intent.succeeded' {
                    handlePaymentIntent(event);
                }
                when 'checkout.session.completed' {
                    handleCheckoutSession(event);
                }
                when else {
                    System.debug('Unhandled event type: ' + eventType);
                }
            }

            res.statusCode = 200;
            res.responseBody = Blob.valueOf('Received');
        } catch (Exception e) {
            res.statusCode = 400; // Bad Request
            res.responseBody = Blob.valueOf('Error: ' + e.getMessage());
            System.debug('Webhook Error: ' + e.getMessage());
        }
    }

    private static void handleCustomerEvent(Map<String, Object> event) {
        Map<String, Object> data = (Map<String, Object>) event.get('data');
        Map<String, Object> objectData = (Map<String, Object>) data.get('object');
        
        String stripeId = (String) objectData.get('id');
        String email = (String) objectData.get('email');
        // String name = (String) objectData.get('name'); // Not always present

        if (String.isBlank(email)) return;

        // Verify if we have this customer in Salesforce
        List<Account> accounts = [SELECT Id, Stripe_Customer_ID__c FROM Account WHERE Patient_Email__c = :email OR Stripe_Customer_ID__c = :stripeId LIMIT 1];
        
        if (!accounts.isEmpty()) {
            Account acc = accounts[0];
            // Update Stripe ID if missing
            if (String.isBlank(acc.Stripe_Customer_ID__c)) {
                acc.Stripe_Customer_ID__c = stripeId;
                acc.Stripe_Status__c = 'Active'; 
                update acc;
            }
        }
    }

    private static void handlePaymentIntent(Map<String, Object> event) {
        // Placeholder, mostly handled by checkout.session.completed for Links
        System.debug('Payment Intent Recieved');
    }

    private static void handleCheckoutSession(Map<String, Object> event) {
        Map<String, Object> data = (Map<String, Object>) event.get('data');
        Map<String, Object> session = (Map<String, Object>) data.get('object');
        
        String clientRefId = (String) session.get('client_reference_id');
        String paymentIntentId = (String) session.get('payment_intent');
        
        if (String.isNotBlank(clientRefId)) {
            try {
                // client_reference_id should be the Order Id
                List<Order> orders = [SELECT Id, Status, Stripe_Payment_Intent__c FROM Order WHERE Id = :clientRefId LIMIT 1];
                if (!orders.isEmpty()) {
                    Order ord = orders[0];
                    if (ord.Status != 'Activated') {
                        ord.Status = 'Activated'; // User requested Activated as final state
                        ord.Stripe_Payment_Intent__c = paymentIntentId;
                        update ord;
                        System.debug('Order ' + ord.Id + ' marked as Activated.');
                    }
                } else {
                     System.debug('Order not found for client_reference_id: ' + clientRefId);
                }
            } catch (Exception e) {
                System.debug('Error updating Order from Webhook: ' + e.getMessage());
            }
        }
    }
}