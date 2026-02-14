public with sharing class StripeService {
    
    // Use the Named Credential we defined in the setup guide
    private static final String NAMED_CREDENTIAL = 'callout:StripeConnect';

    /**
     * @description Tests the connection to Stripe by retrieving the account details.
     * Endpoint: GET https://api.stripe.com/v1/account
     */
    public String testConnection() {
        return makeApiCall('GET', '/v1/account', null);
    }

    /**
     * @description Creates a Customer in Stripe.
     * Endpoint: POST https://api.stripe.com/v1/customers
     */
    public String createCustomer(String name, String email) {
        String body = 'name=' + EncodingUtil.urlEncode(name, 'UTF-8') + 
                      '&email=' + EncodingUtil.urlEncode(email, 'UTF-8');
        return makeApiCall('POST', '/v1/customers', body);
    }

    /**
     * @description Updates a Customer in Stripe.
     * Endpoint: POST https://api.stripe.com/v1/customers/{id}
     */
    public String updateCustomer(String stripeId, String name, String email) {
        String body = 'name=' + EncodingUtil.urlEncode(name, 'UTF-8') + 
                      '&email=' + EncodingUtil.urlEncode(email, 'UTF-8');
        return makeApiCall('POST', '/v1/customers/' + stripeId, body);
    }

    /**
     * @description Retrieves a Product from Stripe.
     * Endpoint: GET https://api.stripe.com/v1/products/{id}
     */
    public String getProduct(String productId) {
        return makeApiCall('GET', '/v1/products/' + productId, null);
    }

    /**
     * @description Creates a Product in Stripe.
     * Endpoint: POST https://api.stripe.com/v1/products
     */
    public String createProduct(String name, String description) {
        String body = 'name=' + EncodingUtil.urlEncode(name, 'UTF-8');
        if (String.isNotBlank(description)) {
            body += '&description=' + EncodingUtil.urlEncode(description, 'UTF-8');
        }
        return makeApiCall('POST', '/v1/products', body);
    }

    /**
     * @description Creates a Payment Link with inline price data.
     * Endpoint: POST https://api.stripe.com/v1/payment_links
     */
    public String createPaymentLink(String orderNumber, Decimal amount, String currencyIso) {
        // Stripe expects amounts in cents (integers)
        Integer amountInCents = (Integer)(amount * 100);
        
        // Construct standard form-urlencoded body for nested objects is tricky in Apex
        // But Stripe accepts array syntax: line_items[0][price_data][...]=...
        String body = 'line_items[0][quantity]=1';
        body += '&line_items[0][price_data][currency]=' + (String.isBlank(currencyIso) ? 'usd' : currencyIso.toLowerCase());
        body += '&line_items[0][price_data][unit_amount]=' + amountInCents;
        body += '&line_items[0][price_data][product_data][name]=Order%20' + EncodingUtil.urlEncode(orderNumber, 'UTF-8');
        
        // Add metadata/reference
        // body += '&client_reference_id=' + orderNumber; 
        
        // Optional: Redirect behavior
        // body += '&after_completion[type]=redirect&after_completion[redirect][url]=https://your-site.com/success';

        return makeApiCall('POST', '/v1/payment_links', body);
    }

    /**
     * @description Helper to execute the callout
     */
    private String makeApiCall(String method, String path, String body) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(NAMED_CREDENTIAL + path);
        req.setMethod(method);
        // Ensure we accept JSON
        req.setHeader('Accept', 'application/json');
        
        if (method == 'POST') {
             // Standard for Stripe POST
            req.setHeader('Content-Type', 'application/x-www-form-urlencoded');
            if (String.isNotBlank(body)) {
                req.setBody(body);
            }
        } else {
             // GET requests might need cleanup if body was passed erroneously, but we leave it
        }

        Http http = new Http();
        try {
            HttpResponse res = http.send(req);
            handleResponse(res);
            return res.getBody();
        } catch (Exception e) {
            System.debug('Error calling Stripe: ' + e.getMessage());
            throw new CalloutException('Stripe Connection Failed: ' + e.getMessage());
        }
    }

    /**
     * @description Helper to log/handle response status
     */
    private void handleResponse(HttpResponse res) {
        if (res.getStatusCode() >= 200 && res.getStatusCode() < 300) {
            System.debug('Success: ' + res.getStatus());
        } else {
            System.debug('Error (' + res.getStatusCode() + '): ' + res.getBody());
            // Throw exception to allow caller to handle failure
            throw new CalloutException('Stripe API Error: ' + res.getBody());
        }
    }
}