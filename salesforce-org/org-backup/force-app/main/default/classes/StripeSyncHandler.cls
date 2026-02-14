public with sharing class StripeSyncHandler {
    
    // Flag to prevent recursion
    public static Boolean isExecuting = false;

    /**
     * @description Handles Account Insert/Update to sync with Stripe.
     * Logic:
     * 1. Check if recursing.
     * 2. Identify Accounts that need sync.
     * 3. Call Future method to perform callout.
     */
    public static void handleAccountChange(List<Account> newAccounts, Map<Id, Account> oldAccountMap) {
        if (isExecuting) return;

        Set<Id> accountsToSync = new Set<Id>();

        for (Account acc : newAccounts) {
            // New Account (Insert) OR Updated Name/Email (Update)
            // Using Patient_Email__c as key field
            if (String.isNotBlank(acc.Patient_Email__c)) {
                 if (oldAccountMap == null) {
                    // Insert
                    accountsToSync.add(acc.Id);
                 } else {
                    // Update
                    Account oldAcc = oldAccountMap.get(acc.Id);
                    // Check if relevant fields changed
                    if (acc.Name != oldAcc.Name || 
                        acc.Patient_Email__c != oldAcc.Patient_Email__c) {
                        accountsToSync.add(acc.Id);
                    }
                 }
            }
        }

        if (!accountsToSync.isEmpty()) {
            syncAccountsFuture(accountsToSync);
        }
    }

    @future(callout=true)
    public static void syncAccountsFuture(Set<Id> accountIds) {
        // Prevent trigger recursion during the update back to Salesforce
        isExecuting = true; 
        
        List<Account> accounts = [SELECT Id, Name, Patient_Email__c, Stripe_Customer_ID__c FROM Account WHERE Id IN :accountIds];
        List<Account> updates = new List<Account>();
        StripeService service = new StripeService();

        for (Account acc : accounts) {
            String email = acc.Patient_Email__c;
            
            try {
                if (String.isBlank(acc.Stripe_Customer_ID__c)) {
                    // Create
                    String response = service.createCustomer(acc.Name, email);
                    // Parse response to get ID - Poor man's parsing for MVP
                    // Ideally use a wrapper class
                    String stripeId = parseIdFromResponse(response);
                    if (stripeId != null) {
                        acc.Stripe_Customer_ID__c = stripeId;
                        acc.Stripe_Status__c = 'Active';
                        updates.add(acc);
                    }
                } else {
                    // Update
                    service.updateCustomer(acc.Stripe_Customer_ID__c, acc.Name, email);
                    // No need to update field in SF unless we track sync time
                }
            } catch (Exception e) {
                System.debug('Failed to sync Account: ' + acc.Id + ' Error: ' + e.getMessage());
                // In production, log error to a custom object
            }
        }

        if (!updates.isEmpty()) {
            update updates;
        }
        
        isExecuting = false;
    }

    private static String parseIdFromResponse(String jsonResponse) {
        // Simple regex or JSON parsing
        // Response: { "id": "cus_...", ... }
        Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(jsonResponse);
        return (String) result.get('id');
    }

    // ---------------- PRODUCT SYNC ----------------

    public static void handleProductChange(List<Product2> newProducts, Map<Id, Product2> oldProductMap) {
        if (isExecuting) return;

        Set<Id> productsToSync = new Set<Id>();

        for (Product2 prod : newProducts) {
             if (oldProductMap == null) {
                // Insert
                productsToSync.add(prod.Id);
             } else {
                // Update
                Product2 oldProd = oldProductMap.get(prod.Id);
                if (prod.Name != oldProd.Name || prod.Description != oldProd.Description) {
                    productsToSync.add(prod.Id);
                }
             }
        }

        if (!productsToSync.isEmpty()) {
            syncProductsFuture(productsToSync);
        }
    }

    @future(callout=true)
    public static void syncProductsFuture(Set<Id> productIds) {
        isExecuting = true;
        
        List<Product2> products = [SELECT Id, Name, Description, Stripe_Product_ID__c FROM Product2 WHERE Id IN :productIds];
        List<Product2> updates = new List<Product2>();
        StripeService service = new StripeService();

        for (Product2 prod : products) {
            try {
                if (String.isBlank(prod.Stripe_Product_ID__c)) {
                    // Create
                    String response = service.createProduct(prod.Name, prod.Description);
                    String stripeId = parseIdFromResponse(response);
                    if (stripeId != null) {
                        prod.Stripe_Product_ID__c = stripeId;
                        updates.add(prod);
                    }
                } else {
                    // Update logic could go here (StripeService.updateProduct needed)
                    // Skipping for MVP
                }
            } catch (Exception e) {
                 System.debug('Failed to sync Product: ' + prod.Id + ' Error: ' + e.getMessage());
            }
        }

        if (!updates.isEmpty()) {
            update updates;
        }

        isExecuting = false;
    }

    // ---------------- ORDER SYNC ----------------

    public static void handleOrderChange(List<Order> newOrders, Map<Id, Order> oldOrderMap) {
        if (isExecuting) return;

        Set<Id> ordersToProcess = new Set<Id>();

        for (Order ord : newOrders) {
             if (oldOrderMap != null) {
                // Update
                Order oldOrd = oldOrderMap.get(ord.Id);
                // Trigger when moved to 'Waiting for Payment' and no link exists
                if (ord.Status != oldOrd.Status && 
                    ord.Status == 'Waiting for Payment' && 
                    String.isBlank(ord.Stripe_Payment_Link__c)) {
                    ordersToProcess.add(ord.Id);
                }
             }
        }

        if (!ordersToProcess.isEmpty()) {
            generatePaymentLinksFuture(ordersToProcess);
        }
    }

    @future(callout=true)
    public static void generatePaymentLinksFuture(Set<Id> orderIds) {
        isExecuting = true;
        
        List<Order> orders = [SELECT Id, OrderNumber, TotalAmount, Stripe_Payment_Link__c FROM Order WHERE Id IN :orderIds];
        List<Order> updates = new List<Order>();
        StripeService service = new StripeService();

        for (Order ord : orders) {
            try {
                if (ord.TotalAmount == null || ord.TotalAmount <= 0) continue;

                // Create Payment Link
                String response = service.createPaymentLink(ord.OrderNumber, ord.TotalAmount, 'usd'); // Assuming USD for now
                
                // Response: { "url": "https://buy.stripe.com/...", ... }
                Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(response);
                String paymentUrl = (String) result.get('url');
                String paymentIntent = (String) result.get('payment_intent'); // Might not be immediate in Link object? Link creates session?
                // Actually Payment Link object has 'url'. 
                
                if (String.isNotBlank(paymentUrl)) {
                    // Append client_reference_id to track the Order ID in the Checkout Session
                    // This is critical for matching the webhook back to this Order
                    if (paymentUrl.contains('?')) {
                        paymentUrl += '&client_reference_id=' + ord.Id;
                    } else {
                        paymentUrl += '?client_reference_id=' + ord.Id;
                    }

                    ord.Stripe_Payment_Link__c = paymentUrl;
                    updates.add(ord);
                }
            } catch (Exception e) {
                 System.debug('Failed to generate Link for Order: ' + ord.Id + ' Error: ' + e.getMessage());
            }
        }

        if (!updates.isEmpty()) {
            update updates;
        }

        isExecuting = false;
    }
}