# Master API Skill

Comprehensive skill for designing, documenting, and managing APIs across all paradigms (REST, GraphQL, gRPC, AsyncAPI). Covers the full API lifecycle from design to deprecation.

---

## Capabilities

### 1. API-First Design

- **Design before code**: Start with contract/spec, generate server stubs and clients
- **Domain modeling**: Identify resources, relationships, and operations from business requirements
- **API style selection**: Choose REST / GraphQL / gRPC / event-driven based on use case

### 2. REST API Design

#### Resource Modeling
- Noun-based URLs: `/users/{id}/orders`
- Richardson Maturity Model (Level 0→3): plain HTTP → resources → HTTP verbs → HATEOAS
- Sub-resources for ownership: `GET /teams/{teamId}/members`

#### HATEOAS
```json
{
  "id": 42,
  "status": "shipped",
  "_links": {
    "self": { "href": "/orders/42" },
    "cancel": { "href": "/orders/42/cancel", "method": "POST" },
    "track": { "href": "/shipments/99" }
  }
}
```

#### HTTP Methods & Status Codes
| Method | Idempotent | Safe | Typical Codes |
|--------|-----------|------|---------------|
| GET | ✅ | ✅ | 200, 304 |
| POST | ❌ | ❌ | 201, 202, 409 |
| PUT | ✅ | ❌ | 200, 204 |
| PATCH | ❌ | ❌ | 200, 409 |
| DELETE | ✅ | ❌ | 204, 404 |

#### Pagination
- **Cursor-based** (preferred for real-time data, infinite scroll):
  ```
  GET /items?cursor=eyJpZCI6MTAwfQ&limit=25
  → { "data": [...], "next_cursor": "eyJpZCI6MTI1fQ" }
  ```
- **Offset-based** (simpler, good for static data):
  ```
  GET /items?offset=50&limit=25
  → { "data": [...], "total": 200 }
  ```

#### Filtering, Sorting, Sparse Fields
```
GET /products?filter[category]=electronics&sort=-price,name&fields=id,name,price
```

#### Error Format (RFC 9457 - Problem Details)
```json
{
  "type": "https://api.example.com/errors/insufficient-funds",
  "title": "Insufficient Funds",
  "status": 422,
  "detail": "Account balance $10.00 is less than withdrawal $50.00",
  "instance": "/transactions/abc123"
}
```

### 3. API Versioning

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| URL path | `/v2/users` | Simple, cacheable | URL pollution |
| Header | `API-Version: 2` | Clean URLs | Hidden |
| Content negotiation | `Accept: application/vnd.api.v2+json` | RESTful | Complex |
| Query param | `?version=2` | Easy testing | Pollutes caching |

**Recommendation**: URL path for public APIs, header for internal. Always support N-1 version. Sunset header for deprecation: `Sunset: Sat, 01 Mar 2026 00:00:00 GMT`.

### 4. OpenAPI 3.1 Specification

```yaml
openapi: "3.1.0"
info:
  title: Example API
  version: 1.0.0
  description: |
    Full API description with **markdown**.
  contact:
    name: API Team
    email: api@example.com
  license:
    name: MIT
servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

paths:
  /resources:
    get:
      operationId: listResources
      summary: List resources
      tags: [Resources]
      parameters:
        - $ref: '#/components/parameters/CursorParam'
        - $ref: '#/components/parameters/LimitParam'
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceList'
        '401':
          $ref: '#/components/responses/Unauthorized'

components:
  schemas:
    Resource:
      type: object
      required: [id, name]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          maxLength: 255
        created_at:
          type: string
          format: date-time

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKey:
      type: apiKey
      in: header
      name: X-API-Key

  parameters:
    CursorParam:
      name: cursor
      in: query
      schema:
        type: string
    LimitParam:
      name: limit
      in: query
      schema:
        type: integer
        default: 25
        maximum: 100

  responses:
    Unauthorized:
      description: Authentication required
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetail'

security:
  - BearerAuth: []
```

### 5. AsyncAPI (Event-Driven APIs)

```yaml
asyncapi: '3.0.0'
info:
  title: Order Events
  version: 1.0.0
channels:
  orderCreated:
    address: orders.created
    messages:
      OrderCreated:
        payload:
          type: object
          properties:
            orderId:
              type: string
              format: uuid
            total:
              type: number
operations:
  onOrderCreated:
    action: receive
    channel:
      $ref: '#/channels/orderCreated'
```

Use for: webhooks, message queues (Kafka, RabbitMQ, NATS), SSE, WebSockets.

### 6. GraphQL Design

#### Schema Best Practices
```graphql
type Query {
  user(id: ID!): User
  users(first: Int!, after: String): UserConnection!  # Relay-style pagination
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  endCursor: String
}

type User @key(fields: "id") {  # Federation
  id: ID!
  name: String!
  email: String! @deprecated(reason: "Use contactEmail")
  contactEmail: String!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
}

input CreateUserInput {
  name: String!
  contactEmail: String!
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!
}
```

- **Federation**: Split schema across services with `@key` directives
- **Persisted queries**: Hash queries client-side, send hash instead of full query string
- **Depth limiting**: Prevent deeply nested queries (max depth 7-10)
- **Cost analysis**: Assign complexity scores to fields, reject expensive queries

### 7. gRPC / Protocol Buffers

```protobuf
syntax = "proto3";
package example.v1;

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (stream User);  // Server streaming
  rpc CreateUser(CreateUserRequest) returns (User);
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
  google.protobuf.Timestamp created_at = 4;
}

message GetUserRequest {
  string id = 1;
}

message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
}
```

Use for: internal microservice communication, high-throughput, bidirectional streaming.

### 8. API Security

#### Authentication Methods
| Method | Use Case | Notes |
|--------|----------|-------|
| OAuth 2.1 | Third-party access, user delegation | Use PKCE for all clients |
| API Keys | Server-to-server, simple auth | Rotate regularly, scope narrowly |
| JWT | Stateless auth tokens | Short-lived (15m), use refresh tokens |
| mTLS | Service mesh, zero-trust | Both client and server present certs |

#### Security Checklist
- [ ] HTTPS everywhere (HSTS header)
- [ ] Rate limiting per client/IP
- [ ] Input validation (reject unknown fields)
- [ ] Output encoding (prevent injection)
- [ ] CORS configured restrictively
- [ ] No sensitive data in URLs/logs
- [ ] Auth tokens in `Authorization` header, not query params
- [ ] Webhook signature verification (HMAC-SHA256)
- [ ] Request size limits
- [ ] SQL injection / NoSQL injection prevention

### 9. Rate Limiting

#### Algorithms
- **Token bucket**: Smooth burst handling, refill tokens over time
- **Sliding window**: Count requests in rolling time window, most accurate
- **Fixed window**: Simple but allows burst at window boundaries

#### Headers (draft-ietf-httpapi-ratelimit)
```
RateLimit-Limit: 100
RateLimit-Remaining: 42
RateLimit-Reset: 30
Retry-After: 30  (on 429)
```

### 10. API Gateway Patterns

- **Request routing**: Path-based routing to microservices
- **Authentication offload**: Verify tokens at gateway
- **Rate limiting**: Centralized throttling
- **Request/response transformation**: Header injection, body mapping
- **Circuit breaker**: Fail fast on unhealthy backends
- **Caching**: Response caching at edge
- **Load balancing**: Round-robin, least connections, weighted
- Tools: Kong, AWS API Gateway, Envoy, Traefik, APISIX

### 11. Documentation-as-Code

#### Tools
| Tool | Best For |
|------|----------|
| **Redoc** | Beautiful single-page reference docs |
| **Swagger UI** | Interactive try-it-out experience |
| **Stoplight** | Visual API design + docs |
| **Slate/Docusaurus** | Guides + reference combined |

#### Documentation Checklist
- [ ] Getting started / quickstart guide
- [ ] Authentication walkthrough
- [ ] Every endpoint with request/response examples
- [ ] Error code reference table
- [ ] Rate limit documentation
- [ ] Changelog / migration guides
- [ ] SDKs and code samples (curl, Python, JS, Go)
- [ ] Webhooks: payload schema, retry policy, signature verification
- [ ] Sandbox / test environment details

### 12. SDK Generation

- **OpenAPI Generator**: Generate clients in 50+ languages from OpenAPI spec
- **Speakeasy**: Type-safe, idiomatic SDKs with retries and pagination built-in
- **Stainless**: Used by OpenAI, Stripe — high-quality generated SDKs
- **gRPC codegen**: `protoc` generates clients natively
- **GraphQL codegen**: `graphql-codegen` for typed clients

### 13. Contract Testing

- **Consumer-driven**: Pact — consumers define expected interactions, providers verify
- **Provider-driven**: Schemathesis — fuzz test against OpenAPI spec
- **Schema validation**: Spectral (lint OpenAPI), `openapi-diff` (breaking change detection)
- **CI pipeline**: Validate spec → run contract tests → generate SDK → deploy docs

### 14. Backward Compatibility & Deprecation

#### Safe Changes (Non-Breaking)
- Adding optional fields to responses
- Adding new endpoints
- Adding optional query parameters
- Adding new enum values (if clients handle unknown)

#### Breaking Changes (Require New Version)
- Removing or renaming fields
- Changing field types
- Removing endpoints
- Making optional fields required

#### Deprecation Policy
1. Announce deprecation (changelog, `Deprecated` header, docs)
2. Set `Sunset` header with date
3. Monitor usage of deprecated endpoints
4. Minimum deprecation period: 6-12 months for public APIs
5. Provide migration guide

### 15. API Analytics & Observability

- **Metrics**: Request count, latency (p50/p95/p99), error rate, payload size
- **Logging**: Structured JSON logs with correlation IDs
- **Tracing**: OpenTelemetry distributed tracing across services
- **Consumer tracking**: Usage per API key/client, popular endpoints
- **Alerting**: Error rate spikes, latency degradation, quota exhaustion
- **Business metrics**: API calls → revenue, developer adoption, time-to-first-call

---

## Workflows

### Design a New API
1. Gather requirements and identify resources/operations
2. Choose API style (REST/GraphQL/gRPC/events)
3. Write spec first (OpenAPI/AsyncAPI/GraphQL SDL/proto)
4. Lint spec with Spectral or buf
5. Review with stakeholders (use mock server)
6. Implement against spec
7. Contract test
8. Generate docs and SDKs
9. Deploy with versioning strategy

### Review an Existing API
1. Import/read the current spec or implementation
2. Check against REST maturity model
3. Audit security (auth, rate limiting, input validation)
4. Review error handling consistency
5. Check pagination, filtering patterns
6. Verify documentation completeness
7. Assess backward compatibility of planned changes
8. Produce improvement report with prioritized recommendations

### Generate Documentation
1. Validate OpenAPI/AsyncAPI spec
2. Add descriptions, examples, and tags to all operations
3. Write getting-started guide
4. Generate SDK code samples
5. Deploy with Redoc/Swagger UI
6. Set up CI to regenerate on spec changes

---

## Prompt Patterns

When asked to design an API, follow this structure:
1. Clarify scope and consumers
2. Define resource model
3. Write spec (OpenAPI 3.1 by default)
4. Include auth, pagination, errors, rate limiting
5. Provide example requests/responses
6. Note versioning and deprecation strategy

When asked to review an API:
1. Identify issues by category (design, security, docs, compatibility)
2. Rate severity (critical/warning/info)
3. Provide specific fix with code example
4. Reference relevant standards (RFC 9457, Richardson model, etc.)
