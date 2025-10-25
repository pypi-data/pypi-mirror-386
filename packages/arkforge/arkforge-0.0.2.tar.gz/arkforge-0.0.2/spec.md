# ArkForge SDK Design Specification

**Version**: 1.0.0
**Last Updated**: October 23, 2025
**Target Languages**: Python, JavaScript/TypeScript, Java, Go, Rust, Ruby

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Surface](#api-surface)
4. [Core Components](#core-components)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Authentication](#authentication)
8. [Rate Limiting](#rate-limiting)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Checklist](#implementation-checklist)
11. [Language-Specific Considerations](#language-specific-considerations)
12. [Examples](#examples)

---

## 1. Overview

### Purpose

The ArkForge SDK provides a language-native interface to the ArkForge DeFi portfolio management service, abstracting away HTTP details and providing type-safe, idiomatic access to portfolio optimization and management capabilities.

### Core Value Propositions

1. **Type Safety**: Language-native type systems for all API interactions
2. **Error Handling**: Idiomatic error handling per language conventions
3. **Retry Logic**: Built-in retry with exponential backoff for transient errors
4. **Authentication**: Secure API key management with rotation support
5. **Rate Limiting**: Client-side rate limiting awareness and backoff
6. **Testability**: Mock-friendly design for unit testing

### Service Endpoints

**Base URL**: `http://localhost:3001` (configurable)

**Primary Endpoints**:

- `GET /health` - Service health check
- `POST /api/v1/portfolio/optimize` - Portfolio optimization
- `POST /api/v1/portfolio/analyze` - Portfolio analysis (not yet implemented)
- `GET /api/v1/portfolio/risk-profiles` - Get available risk profiles
- `POST /api/v1/keys` - Create API key
- `GET /api/v1/keys` - List API keys
- `GET /api/v1/keys/:keyId` - Get API key details
- `DELETE /api/v1/keys/:keyId` - Revoke API key
- `POST /api/v1/keys/:keyId/rotate` - Rotate API key
- `PATCH /api/v1/keys/:keyId/scopes` - Update API key scopes

---

## 2. Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────┐
│              User Application                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│            ArkForge SDK (Your Repo)                  │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────┐     │
│  │  ArkForgeClient │  │  KeyManagementClient │     │
│  └────────┬────────┘  └──────────┬───────────┘     │
│           │                       │                  │
│  ┌────────▼───────────────────────▼────────┐        │
│  │        HTTP Transport Layer              │        │
│  │   (Retry, Timeout, Rate Limit Logic)    │        │
│  └──────────────────┬───────────────────────┘        │
└─────────────────────┼──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│          ArkForge REST API Service                   │
│               (This Service)                         │
└─────────────────────────────────────────────────────┘
```

### Component Layers

#### 1. Client Layer

- **ArkForgeClient**: Main portfolio optimization client
- **KeyManagementClient**: API key lifecycle management
- **Configuration**: SDK configuration and defaults

#### 2. Transport Layer

- **HTTPClient**: HTTP request/response handling
- **RetryPolicy**: Exponential backoff and retry logic
- **RateLimiter**: Client-side rate limiting awareness
- **RequestBuilder**: Constructs HTTP requests
- **ResponseParser**: Parses and validates responses

#### 3. Model Layer

- **Request Models**: Input data structures
- **Response Models**: Output data structures
- **Error Models**: Structured error representations

---

## 3. API Surface

### 3.1 Main Client: ArkForgeClient

```typescript
class ArkForgeClient {
  constructor(config: ArkForgeConfig);

  // Portfolio Operations
  async optimizePortfolio(
    request: OptimizePortfolioRequest
  ): Promise<PortfolioRecommendation>;
  async analyzePortfolio(
    request: AnalyzePortfolioRequest
  ): Promise<PortfolioAnalysis>;
  async getRiskProfiles(): Promise<RiskProfile[]>;

  // Health Check
  async getHealth(): Promise<HealthStatus>;

  // Configuration
  getConfig(): ArkForgeConfig;
  setApiKey(apiKey: string): void;
  setBaseUrl(baseUrl: string): void;
}
```

### 3.2 Key Management Client: KeyManagementClient

```typescript
class KeyManagementClient {
  constructor(config: ArkForgeConfig);

  // Key Lifecycle
  async createKey(request: CreateKeyRequest): Promise<CreateKeyResponse>;
  async listKeys(): Promise<ApiKeyInfo[]>;
  async getKeyDetails(keyId: number): Promise<ApiKeyDetails>;
  async revokeKey(keyId: number, reason?: string): Promise<void>;
  async rotateKey(keyId: number, name?: string): Promise<CreateKeyResponse>;
  async updateScopes(keyId: number, scopes: string[]): Promise<void>;
}
```

### 3.3 Configuration

```typescript
interface ArkForgeConfig {
  apiKey: string;
  baseUrl?: string; // Default: http://localhost:3001
  timeout?: number; // Default: 60000ms (60s)
  retryAttempts?: number; // Default: 3
  retryDelay?: number; // Default: 1000ms
  userAgent?: string;
  debug?: boolean;
}
```

---

## 4. Core Components

### 4.1 HTTP Client

**Responsibilities**:

- Execute HTTP requests with proper headers
- Handle timeouts
- Parse responses
- Convert HTTP errors to SDK exceptions

**Required Headers**:

```
Authorization: Bearer <api_key>
Content-Type: application/json
User-Agent: <sdk_name>/<version> <language>/<version>
X-Client-Version: <sdk_version>
```

**HTTP Methods Required**:

- GET - Health checks, list operations
- POST - Create operations, optimizations
- DELETE - Revoke operations
- PATCH - Update operations

### 4.2 Retry Policy

**Retry Strategy**:

- Exponential backoff: `delay = base_delay * (2 ^ attempt)`
- Maximum attempts: 3 (configurable)
- Retry on:
  - HTTP 429 (Rate Limit) - respect Retry-After header
  - HTTP 5xx (Server Errors)
  - Network timeouts
  - Connection errors

**Do NOT Retry On**:

- HTTP 400 (Bad Request)
- HTTP 401 (Unauthorized)
- HTTP 404 (Not Found)
- Application-level validation errors

**Exponential Backoff Example**:

```
Attempt 1: Immediate
Attempt 2: Wait 1s  (1000ms * 2^0)
Attempt 3: Wait 2s  (1000ms * 2^1)
Attempt 4: Wait 4s  (1000ms * 2^2)
```

### 4.3 Rate Limiting

**Client-Side Awareness**:

- Track rate limit headers from responses
- Implement token bucket or sliding window
- Respect `Retry-After` header on 429 responses

**Rate Limit Headers** (from API):

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1729789200
Retry-After: 60
```

**Implementation Pattern**:

```typescript
class RateLimiter {
  private tokens: number;
  private lastRefill: Date;

  async acquire(): Promise<void> {
    // Wait if no tokens available
    if (this.tokens < 1) {
      await this.waitForToken();
    }
    this.tokens--;
  }

  handleRateLimitResponse(headers: Headers): void {
    // Update internal state from response headers
  }
}
```

### 4.4 Error Handling

**Error Hierarchy**:

```
ArkForgeError (Base Exception)
├── ValidationError (400)
│   ├── InvalidParametersError
│   ├── InvalidRiskProfileError
│   └── InvalidAssetsError
├── AuthenticationError (401)
│   ├── InvalidApiKeyError
│   └── ExpiredApiKeyError
├── RateLimitError (429)
├── TimeoutError (504)
├── ServiceError (5xx)
│   ├── ForecastFailedError
│   ├── SentimentFailedError
│   └── SynthesisFailedError
└── NetworkError
    ├── ConnectionError
    └── DNSError
```

**Error Model**:

```typescript
interface ArkForgeError {
  code: string; // E_INVALID_PARAMETERS, E_RATE_LIMIT, etc.
  message: string; // Human-readable message
  statusCode: number; // HTTP status code
  details?: any; // Additional error details
  requestId?: string; // Request ID for support
  retryable: boolean; // Can this error be retried?
}
```

---

## 5. Data Models

### 5.1 Portfolio Optimization

#### Request Model

```typescript
interface OptimizePortfolioRequest {
  // Required fields
  assets: string[]; // ["BTC", "ETH", "SOL"]
  riskProfile: RiskProfile; // "conservative" | "moderate" | "aggressive"

  // Optional fields
  currentPortfolio?: Record<string, number>; // { "BTC": 50, "ETH": 30, "SOL": 20 }
  budget?: number; // Investment budget
  horizonDays?: number; // Default: 7
  sentimentTimeframeHours?: number; // Default: 168 (7 days)

  // Constraints
  constraints?: {
    maxPositionSize?: number; // Max % per asset
    minDiversification?: number; // Min number of assets
    excludedAssets?: string[]; // Assets to exclude
  };

  // Optimization targets
  optimization?: {
    targetSharpeRatio?: number; // Target Sharpe ratio
    maxVolatility?: number; // Max acceptable volatility (0-1)
    minExpectedReturn?: number; // Min expected return (0-1)
    goal?: "sharpe" | "return" | "risk";
    sentimentWeight?: number; // 0-1, default: 1.0
    ignoreSentiment?: boolean; // Default: false
    optimisticBias?: boolean; // Default: false
  };

  // Options
  options?: {
    parallel?: boolean; // Enable parallel processing
    llmProvider?: "openai" | "anthropic" | "xai" | "mistral";
    llmModel?: string;
    includeRationale?: boolean; // Default: true
  };
}
```

#### Response Model

```typescript
interface PortfolioRecommendation {
  // Allocation
  allocation: Record<string, number>; // { "BTC": 40, "ETH": 35, "SOL": 25 }

  // Metrics
  expectedReturn: number; // Annualized expected return (0.15 = 15%)
  expectedVolatility: number; // Annualized volatility (0.25 = 25%)
  sharpeRatio: number; // Risk-adjusted return (1.5)
  confidence: number; // Confidence in recommendation (0-1)

  // Actions
  actions: Action[];
  swaps?: SwapInstruction[];

  // Rationale (optional)
  rationale?: {
    drivers: string[];
    risks: string[];
    marketContext: string;
    forecastInsights: string;
    sentimentInsights: string;
  };

  // Metadata
  metadata: {
    workflowId: string;
    timestamp: string;
    processingTime: number;
    llmProvider: string;
    llmModel: string;
    requestId: string;
  };
}

interface Action {
  action: "buy" | "sell" | "hold";
  symbol: string;
  targetPercentage: number;
  currentPercentage: number;
  change: number;
}

interface SwapInstruction {
  type: "swap";
  fromToken: string;
  fromAmount: number;
  toToken: string;
  toAmount: number;
  reason: string;
}
```

### 5.2 Risk Profiles

```typescript
interface RiskProfile {
  name: "conservative" | "moderate" | "aggressive";
  description: string;
  characteristics: {
    targetVolatility: string;
    maxDrawdown: string;
    expectedReturn: string;
    assetPreferences: string[];
  };
}
```

### 5.3 API Key Management

#### Create Key Request

```typescript
interface CreateKeyRequest {
  name: string; // "Production Key"
  expiresInDays?: number; // Default: 365, Range: 1-365
  scopes?: string[]; // ["read", "write", "admin"]
}
```

#### Create Key Response

```typescript
interface CreateKeyResponse {
  apiKey: string; // Full key (ONLY shown once!)
  keyId: number;
  prefix: string; // First 16 chars
  warning: string; // "This API key will only be shown once..."
}
```

#### API Key Info

```typescript
interface ApiKeyInfo {
  id: number;
  prefix: string; // sk-arkforge-a1b2
  name: string;
  scopes: string[]; // ["read", "write", "admin"]
  createdAt: string; // ISO 8601
  lastUsedAt: string | null; // ISO 8601
  expiresAt: string; // ISO 8601
  isActive: boolean;
}
```

#### API Key Details

```typescript
interface ApiKeyDetails extends ApiKeyInfo {
  usage: {
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    lastRequestAt: string | null;
    averageDuration: number;
  };
}
```

### 5.4 Health Check

```typescript
interface HealthStatus {
  status: "ok" | "degraded" | "down";
  timestamp: string;
  uptime: number; // Seconds
  services: {
    timegpt: "ok" | "degraded" | "unknown";
    cryptobert: "ok" | "degraded" | "unknown";
    finbert: "ok" | "degraded" | "unknown";
    grok: "ok" | "degraded" | "unknown";
    claude: "ok" | "degraded" | "unknown";
    gpt4: "ok" | "degraded" | "unknown";
  };
}
```

---

## 6. Error Handling

### Error Response Format

All errors from the API follow this structure:

```json
{
  "status": "error",
  "error": {
    "code": "E_INVALID_PARAMETERS",
    "message": "Invalid or missing riskProfile",
    "details": {
      /* optional */
    }
  },
  "metadata": {
    "requestId": "req_1729789200_abc123",
    "timestamp": "2025-10-23T17:30:00.000Z"
  }
}
```

### Error Code Mapping

| Error Code            | HTTP Status | Retryable | SDK Exception       |
| --------------------- | ----------- | --------- | ------------------- |
| E_INVALID_PARAMETERS  | 400         | No        | ValidationError     |
| E_INVALID_VAULT       | 400         | No        | ValidationError     |
| E_INVALID_RISK        | 400         | No        | ValidationError     |
| E_UNAUTHORIZED        | 401         | No        | AuthenticationError |
| E_INVALID_API_KEY     | 401         | No        | InvalidApiKeyError  |
| E_RATE_LIMIT          | 429         | Yes       | RateLimitError      |
| E_RATE_LIMIT_EXCEEDED | 429         | Yes       | RateLimitError      |
| E_TIMEGPT_TIMEOUT     | 502         | Yes       | TimeGPTError        |
| E_TIMEGPT_API_ERROR   | 502         | Yes       | TimeGPTError        |
| E_SENTIMENT_FAILED    | 503         | Yes       | SentimentError      |
| E_WORKFLOW_ERROR      | 500         | Yes       | WorkflowError       |
| E_TIMEOUT             | 504         | Yes       | TimeoutError        |
| E_INTERNAL_ERROR      | 500         | Yes       | InternalServerError |

### Retry Logic Decision Tree

```
HTTP Error Received
├─ Is 429 (Rate Limit)?
│  └─ Yes → Wait for Retry-After → Retry (max 3 times)
├─ Is 5xx (Server Error)?
│  └─ Yes → Exponential backoff → Retry (max 3 times)
├─ Is Network/Timeout?
│  └─ Yes → Exponential backoff → Retry (max 3 times)
└─ Is 4xx (Client Error)?
   └─ Yes → Do NOT retry → Throw exception immediately
```

---

## 7. Authentication

### API Key Format

```
sk-arkforge-[64 hex characters]
```

Example: `sk-arkforge-6cd7e5aa461c98b451197beff98931cd878a7ce59ad804a8c08afe49dd8dc00d`

### Authentication Methods

#### 1. Constructor Injection (Recommended)

```typescript
const client = new ArkForgeClient({
  apiKey: process.env.ARKFORGE_API_KEY,
});
```

#### 2. Environment Variable (Fallback)

SDK should check for `ARKFORGE_API_KEY` environment variable if not provided in config.

#### 3. Configuration File (Optional)

```json
// ~/.arkforge/config.json
{
  "apiKey": "sk-arkforge-...",
  "baseUrl": "http://localhost:3001"
}
```

### Security Best Practices

1. **Never log API keys** - Mask in logs (show only prefix)
2. **Secure storage** - Use platform-specific secure storage (keychain, etc.)
3. **Rotation support** - Make API key updates easy
4. **Validation** - Check API key format before sending requests

### Key Rotation Pattern

```typescript
// Rotation workflow
const keyMgmt = new KeyManagementClient(config);

// Create new key
const newKey = await keyMgmt.rotateKey(oldKeyId, "Rotated Key");

// Update client
client.setApiKey(newKey.apiKey);

// Old key is automatically revoked
```

---

## 8. Rate Limiting

### Rate Limit Tiers

| Tier       | Requests/Hour | Notes               |
| ---------- | ------------- | ------------------- |
| Free       | 100           | Development/testing |
| Pro        | 1,000         | Small production    |
| Enterprise | 5,000         | Large scale         |

### Client-Side Rate Limiting

**Implementation Strategy**:

1. **Token Bucket Algorithm**:

   ```typescript
   class TokenBucket {
     private tokens: number;
     private capacity: number;
     private refillRate: number;
     private lastRefill: Date;

     async consume(tokens = 1): Promise<void> {
       this.refill();
       if (this.tokens < tokens) {
         throw new RateLimitError("Rate limit exceeded");
       }
       this.tokens -= tokens;
     }

     private refill(): void {
       const now = new Date();
       const elapsed = (now.getTime() - this.lastRefill.getTime()) / 1000;
       const newTokens = elapsed * this.refillRate;
       this.tokens = Math.min(this.capacity, this.tokens + newTokens);
       this.lastRefill = now;
     }
   }
   ```

2. **Sliding Window**:
   Track requests over a rolling time window (last hour).

3. **Server-Guided**:
   Use response headers to adjust client behavior:
   ```typescript
   X-RateLimit-Limit: 1000
   X-RateLimit-Remaining: 995
   X-RateLimit-Reset: 1729792800
   ```

### Rate Limit Error Handling

```typescript
try {
  const result = await client.optimizePortfolio(request);
} catch (error) {
  if (error instanceof RateLimitError) {
    const retryAfter = error.retryAfter; // seconds
    console.log(`Rate limited. Retry after ${retryAfter}s`);
    await sleep(retryAfter * 1000);
    // Retry logic...
  }
}
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Coverage Goals**: >85%

**Test Categories**:

1. **Request Builder Tests**

   - Valid request construction
   - Required field validation
   - Optional field handling
   - Default value application

2. **Response Parser Tests**

   - Valid response parsing
   - Invalid JSON handling
   - Missing field detection
   - Type conversion

3. **Error Handling Tests**

   - Each error code mapping
   - Retry logic for retryable errors
   - No retry for client errors
   - Exponential backoff calculation

4. **Rate Limiter Tests**
   - Token consumption
   - Token refill
   - Rate limit detection
   - Backoff behavior

### 9.2 Integration Tests

**Test Against Real Service**:

```typescript
describe("ArkForgeClient Integration", () => {
  let client: ArkForgeClient;

  beforeAll(() => {
    client = new ArkForgeClient({
      apiKey: process.env.TEST_API_KEY,
      baseUrl: "http://localhost:3001",
    });
  });

  test("optimizePortfolio returns valid recommendation", async () => {
    const result = await client.optimizePortfolio({
      assets: ["BTC", "ETH", "SOL"],
      riskProfile: "moderate",
    });

    expect(result.allocation).toBeDefined();
    expect(result.expectedReturn).toBeGreaterThan(0);
    expect(result.confidence).toBeGreaterThan(0);
    expect(result.confidence).toBeLessThanOrEqual(1);
  });

  test("handles rate limiting gracefully", async () => {
    // Make requests until rate limited
    // Verify exponential backoff
    // Verify eventual success
  });
});
```

### 9.3 Mock Testing

**Provide Mock Implementation**:

```typescript
class MockArkForgeClient extends ArkForgeClient {
  async optimizePortfolio(
    request: OptimizePortfolioRequest
  ): Promise<PortfolioRecommendation> {
    return {
      allocation: { BTC: 40, ETH: 35, SOL: 25 },
      expectedReturn: 0.15,
      expectedVolatility: 0.25,
      sharpeRatio: 1.5,
      confidence: 0.85,
      actions: [],
      metadata: {
        /* mock metadata */
      },
    };
  }
}
```

---

## 10. Implementation Checklist

### Phase 1: Core Infrastructure (Week 1)

- [ ] Set up project structure
- [ ] HTTP client implementation
- [ ] Request builder
- [ ] Response parser
- [ ] Error handling framework
- [ ] Configuration management
- [ ] Unit tests for above

### Phase 2: Portfolio API (Week 2)

- [ ] OptimizePortfolio endpoint
- [ ] GetRiskProfiles endpoint
- [ ] AnalyzePortfolio endpoint (prepare for future)
- [ ] Request/response models
- [ ] Validation logic
- [ ] Integration tests

### Phase 3: Key Management API (Week 2)

- [ ] CreateKey endpoint
- [ ] ListKeys endpoint
- [ ] GetKeyDetails endpoint
- [ ] RevokeKey endpoint
- [ ] RotateKey endpoint
- [ ] UpdateScopes endpoint
- [ ] Integration tests

### Phase 4: Advanced Features (Week 3)

- [ ] Retry logic with exponential backoff
- [ ] Rate limiting (client-side)
- [ ] Timeout handling
- [ ] Request ID tracking
- [ ] Logging and debugging
- [ ] Performance testing

### Phase 5: Polish & Release (Week 4)

- [ ] Documentation (README, API docs)
- [ ] Code examples
- [ ] CI/CD pipeline
- [ ] Package publishing
- [ ] Changelog
- [ ] Semantic versioning

---

## 11. Language-Specific Considerations

### 11.1 Python

**Package Structure**:

```
arkforge-python/
├── arkforge/
│   ├── __init__.py
│   ├── client.py
│   ├── key_management.py
│   ├── models.py
│   ├── errors.py
│   ├── http.py
│   └── retry.py
├── tests/
├── setup.py
└── README.md
```

**Naming Conventions**:

- snake_case for functions/variables
- PascalCase for classes
- Use type hints (Python 3.7+)

**HTTP Library**: `requests` or `httpx` (async support)

**Example**:

```python
from arkforge import ArkForgeClient

client = ArkForgeClient(api_key="sk-arkforge-...")
result = client.optimize_portfolio(
    assets=["BTC", "ETH", "SOL"],
    risk_profile="moderate"
)
```

### 11.2 JavaScript/TypeScript

**Package Structure**:

```
arkforge-js/
├── src/
│   ├── index.ts
│   ├── client.ts
│   ├── key-management.ts
│   ├── models.ts
│   ├── errors.ts
│   ├── http.ts
│   └── retry.ts
├── tests/
├── package.json
└── README.md
```

**Naming Conventions**:

- camelCase for functions/variables
- PascalCase for classes/interfaces
- Use TypeScript for type safety

**HTTP Library**: `axios` or `fetch` (native)

**Example**:

```typescript
import { ArkForgeClient } from "arkforge";

const client = new ArkForgeClient({
  apiKey: "sk-arkforge-...",
});

const result = await client.optimizePortfolio({
  assets: ["BTC", "ETH", "SOL"],
  riskProfile: "moderate",
});
```

### 11.3 Java

**Package Structure**:

```
arkforge-java/
└── src/main/java/com/arkforge/
    ├── ArkForgeClient.java
    ├── KeyManagementClient.java
    ├── models/
    ├── exceptions/
    ├── http/
    └── retry/
```

**Naming Conventions**:

- camelCase for methods/variables
- PascalCase for classes
- Use generics for type safety

**HTTP Library**: `OkHttp` or `Apache HttpClient`

**Example**:

```java
ArkForgeClient client = new ArkForgeClient.Builder()
    .apiKey("sk-arkforge-...")
    .build();

OptimizePortfolioRequest request = OptimizePortfolioRequest.builder()
    .assets(Arrays.asList("BTC", "ETH", "SOL"))
    .riskProfile(RiskProfile.MODERATE)
    .build();

PortfolioRecommendation result = client.optimizePortfolio(request);
```

### 11.4 Go

**Package Structure**:

```
arkforge-go/
├── arkforge.go
├── client.go
├── key_management.go
├── models.go
├── errors.go
├── http.go
└── retry.go
```

**Naming Conventions**:

- camelCase for unexported
- PascalCase for exported
- Use struct tags for JSON marshaling

**HTTP Library**: `net/http` (standard library)

**Example**:

```go
client := arkforge.NewClient(arkforge.Config{
    APIKey: "sk-arkforge-...",
})

result, err := client.OptimizePortfolio(context.Background(), &arkforge.OptimizePortfolioRequest{
    Assets:      []string{"BTC", "ETH", "SOL"},
    RiskProfile: arkforge.RiskProfileModerate,
})
if err != nil {
    log.Fatal(err)
}
```

### 11.5 Rust

**Package Structure**:

```
arkforge-rust/
├── src/
│   ├── lib.rs
│   ├── client.rs
│   ├── key_management.rs
│   ├── models.rs
│   ├── errors.rs
│   ├── http.rs
│   └── retry.rs
├── tests/
└── Cargo.toml
```

**Naming Conventions**:

- snake_case for functions/variables
- PascalCase for types/traits
- Use Result<T, E> for error handling

**HTTP Library**: `reqwest`

**Example**:

```rust
let client = ArkForgeClient::new(ArkForgeConfig {
    api_key: "sk-arkforge-...".to_string(),
    ..Default::default()
});

let result = client.optimize_portfolio(OptimizePortfolioRequest {
    assets: vec!["BTC".to_string(), "ETH".to_string(), "SOL".to_string()],
    risk_profile: RiskProfile::Moderate,
    ..Default::default()
}).await?;
```

### 11.6 Ruby

**Package Structure**:

```
arkforge-ruby/
├── lib/
│   ├── arkforge.rb
│   ├── arkforge/
│   │   ├── client.rb
│   │   ├── key_management.rb
│   │   ├── models.rb
│   │   ├── errors.rb
│   │   ├── http.rb
│   │   └── retry.rb
├── spec/
└── arkforge.gemspec
```

**Naming Conventions**:

- snake_case for methods/variables
- PascalCase for classes/modules
- Use symbols for constants

**HTTP Library**: `faraday` or `httparty`

**Example**:

```ruby
client = Arkforge::Client.new(
  api_key: 'sk-arkforge-...'
)

result = client.optimize_portfolio(
  assets: ['BTC', 'ETH', 'SOL'],
  risk_profile: :moderate
)
```

---

## 12. Examples

### Example 1: Basic Portfolio Optimization

```typescript
import { ArkForgeClient } from "arkforge";

const client = new ArkForgeClient({
  apiKey: process.env.ARKFORGE_API_KEY,
});

async function optimizeMyPortfolio() {
  try {
    const result = await client.optimizePortfolio({
      assets: ["BTC", "ETH", "SOL", "AVAX"],
      riskProfile: "moderate",
      horizonDays: 30,
    });

    console.log("Recommended Allocation:");
    Object.entries(result.allocation).forEach(([symbol, percentage]) => {
      console.log(`  ${symbol}: ${percentage}%`);
    });

    console.log(
      `\nExpected Return: ${(result.expectedReturn * 100).toFixed(2)}%`
    );
    console.log(
      `Expected Volatility: ${(result.expectedVolatility * 100).toFixed(2)}%`
    );
    console.log(`Sharpe Ratio: ${result.sharpeRatio.toFixed(2)}`);
    console.log(`Confidence: ${(result.confidence * 100).toFixed(0)}%`);
  } catch (error) {
    if (error instanceof RateLimitError) {
      console.error(`Rate limited. Retry after ${error.retryAfter}s`);
    } else if (error instanceof ValidationError) {
      console.error(`Invalid request: ${error.message}`);
    } else {
      console.error(`Unexpected error: ${error.message}`);
    }
  }
}

optimizeMyPortfolio();
```

### Example 2: Rebalancing Existing Portfolio

```typescript
async function rebalancePortfolio() {
  const client = new ArkForgeClient({
    apiKey: process.env.ARKFORGE_API_KEY,
  });

  const result = await client.optimizePortfolio({
    assets: ["BTC", "ETH", "SOL"],
    riskProfile: "aggressive",
    currentPortfolio: {
      BTC: 60,
      ETH: 30,
      SOL: 10,
    },
    horizonDays: 7,
  });

  console.log("Rebalancing Actions:");
  result.actions.forEach((action) => {
    console.log(
      `${action.action.toUpperCase()} ${action.symbol}: ` +
        `${action.currentPercentage}% → ${action.targetPercentage}% ` +
        `(${action.change > 0 ? "+" : ""}${action.change}%)`
    );
  });

  if (result.swaps) {
    console.log("\nSwap Instructions:");
    result.swaps.forEach((swap) => {
      console.log(
        `  Swap ${swap.fromAmount} ${swap.fromToken} → ${swap.toAmount} ${swap.toToken}`
      );
      console.log(`  Reason: ${swap.reason}`);
    });
  }
}
```

### Example 3: API Key Management

```typescript
import { KeyManagementClient } from "arkforge";

async function manageApiKeys() {
  const keyMgmt = new KeyManagementClient({
    apiKey: process.env.ARKFORGE_ADMIN_KEY,
  });

  // Create a new key
  const newKey = await keyMgmt.createKey({
    name: "Production Key",
    expiresInDays: 90,
    scopes: ["read", "write"],
  });

  console.log("New API Key Created:");
  console.log(`  Key: ${newKey.apiKey}`); // SAVE THIS!
  console.log(`  ID: ${newKey.keyId}`);
  console.log(`  Prefix: ${newKey.prefix}`);

  // List all keys
  const keys = await keyMgmt.listKeys();
  console.log(`\nTotal Keys: ${keys.length}`);
  keys.forEach((key) => {
    console.log(
      `  [${key.id}] ${key.name} - ${key.prefix} (${key.scopes.join(", ")})`
    );
  });

  // Get key details with usage stats
  const details = await keyMgmt.getKeyDetails(newKey.keyId);
  console.log(`\nKey Usage:`);
  console.log(`  Total Requests: ${details.usage.totalRequests}`);
  console.log(
    `  Success Rate: ${(
      (details.usage.successfulRequests / details.usage.totalRequests) *
      100
    ).toFixed(1)}%`
  );

  // Rotate key after 90 days
  const rotatedKey = await keyMgmt.rotateKey(
    newKey.keyId,
    "Rotated Production Key"
  );
  console.log(`\nKey Rotated:`);
  console.log(`  New Key: ${rotatedKey.apiKey}`); // SAVE THIS!
  console.log(`  Old Key ID: ${newKey.keyId} (revoked)`);
  console.log(`  New Key ID: ${rotatedKey.keyId}`);
}
```

### Example 4: Error Handling with Retry

```typescript
async function optimizeWithRetry() {
  const client = new ArkForgeClient({
    apiKey: process.env.ARKFORGE_API_KEY,
    retryAttempts: 3,
    retryDelay: 1000,
  });

  const maxAttempts = 3;
  let attempt = 0;

  while (attempt < maxAttempts) {
    try {
      const result = await client.optimizePortfolio({
        assets: ["BTC", "ETH", "SOL"],
        riskProfile: "moderate",
      });

      console.log("Optimization successful!");
      return result;
    } catch (error) {
      attempt++;

      if (error instanceof RateLimitError) {
        console.log(`Rate limited. Waiting ${error.retryAfter}s...`);
        await sleep(error.retryAfter * 1000);
        continue;
      }

      if (error instanceof TimeoutError && attempt < maxAttempts) {
        console.log(`Timeout. Retrying (${attempt}/${maxAttempts})...`);
        await sleep(Math.pow(2, attempt) * 1000);
        continue;
      }

      // Non-retryable error or max attempts reached
      console.error(`Failed after ${attempt} attempts: ${error.message}`);
      throw error;
    }
  }
}
```

### Example 5: Advanced Optimization with Constraints

```typescript
async function advancedOptimization() {
  const client = new ArkForgeClient({
    apiKey: process.env.ARKFORGE_API_KEY,
  });

  const result = await client.optimizePortfolio({
    // Assets
    assets: ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK"],
    riskProfile: "moderate",

    // Current portfolio (optional)
    currentPortfolio: {
      BTC: 40,
      ETH: 30,
      SOL: 15,
      AVAX: 10,
      MATIC: 3,
      LINK: 2,
    },

    // Budget for rebalancing
    budget: 10000, // $10k available

    // Time horizons
    horizonDays: 30, // 30-day forecast
    sentimentTimeframeHours: 168, // 7-day sentiment

    // Constraints
    constraints: {
      maxPositionSize: 35, // Max 35% in any single asset
      minDiversification: 4, // At least 4 different assets
      excludedAssets: [], // No exclusions
    },

    // Optimization targets
    optimization: {
      targetSharpeRatio: 1.5, // Target Sharpe > 1.5
      maxVolatility: 0.3, // Max 30% volatility
      minExpectedReturn: 0.12, // Min 12% expected return
      goal: "sharpe", // Optimize for risk-adjusted returns
      sentimentWeight: 0.8, // 80% weight on sentiment
      ignoreSentiment: false,
      optimisticBias: false,
    },

    // Options
    options: {
      parallel: true, // Enable parallel processing
      llmProvider: "anthropic", // Use Claude
      llmModel: "claude-3-5-sonnet-20241022",
      includeRationale: true, // Get detailed reasoning
    },
  });

  console.log("Optimization Complete!");
  console.log(`Confidence: ${(result.confidence * 100).toFixed(0)}%`);
  console.log(`Processing Time: ${result.metadata.processingTime}ms`);

  if (result.rationale) {
    console.log("\nKey Drivers:");
    result.rationale.drivers.forEach((driver) => console.log(`  • ${driver}`));

    console.log("\nRisk Considerations:");
    result.rationale.risks.forEach((risk) => console.log(`  ⚠️  ${risk}`));
  }

  return result;
}
```

---

## Appendix A: API Reference Quick Links

**Service Documentation**:

- [Main README](../README.md)
- [API Documentation](./API.md)
- [API Key Guide](./API_KEY_GUIDE.md)
- [Docker Deployment](./DOCKER_DEPLOYMENT.md)
- [Production Readiness](./PRODUCTION_READINESS.md)

**API Endpoints**:

- Base URL: `http://localhost:3001`
- Health: `GET /health`
- Portfolio: `POST /api/v1/portfolio/optimize`
- Risk Profiles: `GET /api/v1/portfolio/risk-profiles`
- API Keys: `/api/v1/keys/*`

---

## Appendix B: Version History

### v1.0.0 (October 23, 2025)

- Initial SDK design specification
- Complete API surface documentation
- Error handling and retry logic specifications
- Multi-language implementation guidelines

---

## Appendix C: Support & Resources

**Questions?**

- Service Health: `curl http://localhost:3001/health`
- API Documentation: See [docs/](../docs/)
- Issues: GitHub Issues (TBD)

**Contributing**:

- Follow language-specific style guides
- Write tests for all features
- Maintain >85% code coverage
- Update documentation with changes

---

**End of Specification**

This document provides everything needed to implement a production-ready SDK for the ArkForge service in any programming language. Follow the patterns, handle errors properly, implement retry logic, and your users will have a great experience!
