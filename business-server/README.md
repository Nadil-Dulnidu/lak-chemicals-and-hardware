# Lak Chemicals Business Server (Spring Boot 3.4 & Java 21)

Production-grade enterprise backend service for **Lak Chemicals and Hardware**, migrated from FastAPI to **Spring Boot 3.4** and **Java 21 LTS**.

---

## 🚀 Key Highlights & Tech Stack

- **Runtime**: Java 21 LTS (`OpenJDK 21`)
- **Framework**: Spring Boot `3.4.3`
- **Data Persistence**: Spring Data JPA with Hibernate ORM 6
- **Database Support**: PostgreSQL (Production Cloud SQL / Supabase) / H2 In-Memory (Test & Local Dev)
- **Database Migrations**: Flyway `10.x` (`V1__init_schema.sql` covering 12 relational tables)
- **Security & Identity**: Spring Security 6 with Clerk JWKS verification and `x-api-key` header verification for inter-service communication (AI multi-agent server & API Gateway)
- **Autonomous AI Reports Orchestration**: Inter-service `RestClient` calling the `multi-agent-server` to augment raw SQL metrics with **Gemini 2.5 Pro** reasoning
- **Payments**: Stripe Java SDK (`stripe-java:28.4.0`)
- **Cloud Storage**: Google Cloud Storage (`google-cloud-storage:2.48.0`)
- **API Documentation**: SpringDoc OpenAPI 3 (`/swagger-ui.html`, `/v3/api-docs`)
- **Observability**: Spring Boot Actuator (`/actuator/health`, `/actuator/info`)
- **API Spec & Testing**: JUnit 5, Mockito, Spring Test MockMvc (100% test pass rate)

---

## 📁 Architecture & Package Structure

```
business-server/
├── pom.xml                               # Maven project definition
├── Dockerfile                            # Multi-stage Eclipse Temurin 21 JRE image
├── mvnw / mvnw.cmd                       # Maven wrapper executables
└── src/
    ├── main/
    │   ├── java/com/lakchemicals/business/
    │   │   ├── BusinessServerApplication.java
    │   │   ├── config/                   # WebMvc, Security, Clerk, Stripe configs
    │   │   ├── constants/                # Enums: ProductCategory, MovementType, etc.
    │   │   ├── controller/               # REST Controllers (/api/v1/* and root paths)
    │   │   ├── dto/                      # Strongly-typed request/response models
    │   │   │   └── report/               # AI & standard report DTOs
    │   │   ├── entity/                   # JPA Entity definitions (Product, Order, etc.)
    │   │   ├── exception/                # GlobalExceptionHandler & custom exceptions
    │   │   ├── repository/               # Spring Data JPA Repositories
    │   │   ├── security/                 # Clerk JWT & ApiKey filters and verifiers
    │   │   └── service/                  # Business logic & AiServiceClient
    │   └── resources/
    │       ├── application.yml           # Application configuration
    │       └── db/migration/
    │           └── V1__init_schema.sql   # Flyway initial schema migration
    └── test/
        ├── java/com/lakchemicals/business/
        │   ├── ApiControllerSecurityTest.java
        │   ├── CartServiceTest.java
        │   ├── OrderServiceTest.java
        │   ├── ProductServiceTest.java
        │   ├── QuotationServiceTest.java
        │   └── ReportServiceTest.java
        └── resources/
            └── application-test.yml      # Test profile (H2, disabled Flyway, mock keys)
```

---

## 🔒 Authentication & Authorization

The server supports dual authentication mechanisms:

1. **User Authentication (Clerk JWT)**:
   - Request Header: `Authorization: Bearer <clerk_session_jwt>`
   - Validated against Clerk's JWKS endpoint (`https://<CLERK_INSTANCE>/.well-known/jwks.json`).
   - Populates user ID, email, and roles into Spring's `SecurityContextHolder`.

2. **Inter-Service Communication (`x-api-key`)**:
   - Request Header: `x-api-key: <BUSINESS_SERVER_API_KEY>`
   - Authenticates the **Multi-Agent AI Server** and **API Gateway** to invoke inventory, quotation, sales reporting, and agent tool endpoints.

---

## 🌐 API Endpoints

All endpoints support both `/api/v1/<path>` and `/<path>` paths for seamless backwards compatibility with frontend clients and microservice gateways.

### 🤖 Autonomous AI Reports (`/api/v1/reports/generate/ai`)
- `POST /api/v1/reports/generate/ai/sales` - Sales audit with Gemini 2.5 Pro revenue velocity reasoning.
- `POST /api/v1/reports/generate/ai/inventory` - Inventory asset valuation and holding cost audit.
- `POST /api/v1/reports/generate/ai/product-performance` - SKU profitability, sales consistency, and top movers.
- `POST /api/v1/reports/generate/ai/low-stock` - Stockout risk analysis and recommended reorder quantities.
- `POST /api/v1/reports/generate/ai/sales-prediction` - 60-day historical trajectory synthesizing a 30-day demand forecast.
*(Guarded by `@PreAuthorize("hasAuthority('ROLE_ADMIN')")`)*

### Products (`/api/v1/products`)
- `GET /api/v1/products` - List products with pagination, category filter, active filter, search query.
- `GET /api/v1/products/{id}` - Get product by ID.
- `POST /api/v1/products` - Create product (Admin only).
- `PUT /api/v1/products/{id}` - Update product (Admin only).
- `DELETE /api/v1/products/{id}` - Soft-delete product (Admin only).

### Cart (`/api/v1/cart`)
- `GET /api/v1/cart` - Get user cart and line items.
- `POST /api/v1/cart/items` - Add item to cart.
- `PUT /api/v1/cart/items/{itemId}` - Update item quantity.
- `DELETE /api/v1/cart/items/{itemId}` - Remove item from cart.
- `DELETE /api/v1/cart` - Clear entire cart.

### Quotations (`/api/v1/quotations`)
- `POST /api/v1/quotations` - Create quotation request.
- `POST /api/v1/quotations/from-cart` - Generate quotation directly from cart items.
- `GET /api/v1/quotations` - List user quotations (or all if admin).
- `GET /api/v1/quotations/{id}` - Get quotation by ID.
- `PATCH /api/v1/quotations/{id}/status` - Approve / Reject quotation with discount (Admin only).
- `DELETE /api/v1/quotations/{id}` - Delete quotation.

### Orders (`/api/v1/orders`)
- `POST /api/v1/orders/from-cart` - Create order directly from cart items.
- `POST /api/v1/orders/from-quotation` - Convert approved quotation to order.
- `GET /api/v1/orders` - List orders with status and date filters.
- `GET /api/v1/orders/{id}` - Get order by ID.
- `PATCH /api/v1/orders/{id}/status` - Update order status (triggers sales record upon delivery).

### Inventory & Stock Movements (`/api/v1/inventory`)
- `GET /api/v1/inventory/movements` - View inventory audit trail.
- `POST /api/v1/inventory/adjust` - Adjust stock levels with audit reason.
- `GET /api/v1/inventory/low-stock` - Retrieve items below reorder threshold.

### Standard Reports & Configurations (`/api/v1/reports`)
- `GET /api/v1/reports` - List saved report configurations.
- `POST /api/v1/reports` - Create saved report configuration.
- `GET /api/v1/reports/{id}` - Get report configuration.
- `PUT /api/v1/reports/{id}` - Update report configuration.
- `DELETE /api/v1/reports/{id}` - Delete report configuration.
- `POST /api/v1/reports/{id}/run` - Execute a saved report configuration.
- `POST /api/v1/reports/sales` - Generate raw sales report.
- `POST /api/v1/reports/inventory` - Generate raw inventory report.
- `POST /api/v1/reports/product-performance` - Generate raw product performance report.
- `POST /api/v1/reports/low-stock` - Generate raw low stock report.

### Payments (`/api/v1/stripe`)
- `POST /api/v1/stripe/checkout-session` - Create Stripe Checkout session for an order.
- `POST /api/v1/stripe/confirm-payment` - Confirm checkout session payment completion.

### Agent Tools (`/api/v1/tools`)
- Dedicated endpoints optimized for AI tool invocations by the `multi-agent-server` (product searches, quote requests, stock checks, and sales aggregation).

---

## 📖 OpenAPI / Swagger Documentation

When running locally, interactive OpenAPI documentation is accessible at:
- **Swagger UI**: [http://localhost:8080/swagger-ui/index.html](http://localhost:8080/swagger-ui/index.html)
- **OpenAPI JSON Spec**: [http://localhost:8080/v3/api-docs](http://localhost:8080/v3/api-docs)

---

## 🛠️ Build and Execution Instructions

### Prerequisites
- **JDK 21** installed and configured (`java -version`).
- Local environment configuration:
  ```bash
  cp .env.example .env
  # Adjust database and API key values in .env as needed
  ```
  *(Loaded automatically via `springboot3-dotenv` and Spring Boot `spring.config.import`)*
- PostgreSQL or Docker (optional for local in-memory H2 development).

### Run Test Suite
```bash
./mvnw clean test
```
*(On Windows: `.\mvnw.cmd clean test`)*

### Run Locally (Development Profile)
```bash
./mvnw spring-boot:run
```
*(On Windows: `.\mvnw.cmd spring-boot:run`)*

### Build Executable JAR
```bash
./mvnw clean package -DskipTests
java -jar target/business-server-1.0.0.jar
```

---

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t lak-business-server:latest -f business-server/Dockerfile business-server/
```

### Run in Docker
```bash
docker run -d -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=prod \
  -e SPRING_DATASOURCE_URL="jdbc:postgresql://postgres:5432/lak_chemicals" \
  -e SPRING_DATASOURCE_USERNAME="postgres" \
  -e SPRING_DATASOURCE_PASSWORD="password" \
  -e AI_SERVICE_BASE_URL="http://multi-agent-server:8001" \
  -e AI_SERVICE_API_KEY="YOUR_KEY" \
  --name business-server \
  lak-business-server:latest
```
