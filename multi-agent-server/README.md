# 🤖 Lak Chemicals Multi-Agent AI Server

The **Lak Chemicals Multi-Agent AI Server** is an intelligent microservice built on **FastAPI**, **LangGraph**, and **`langchain_google_genai`** configured directly for **Google Cloud Vertex AI**. It powers both real-time customer conversational commerce and autonomous administrative business intelligence.

---

## 🌟 Key Capabilities & Architecture

### 1. Pure `langchain_google_genai` with GCP Vertex AI
- Exclusively uses `langchain_google_genai` (`ChatGoogleGenerativeAI`) with `vertexai=True`, target project, location (`asia-south1`), and your Vertex AI API key.
- Eliminates unnecessary third-party wrapper SDKs for clean, native LangChain integration.
- Dual-model strategy:
  - **`gemini-2.5-flash`**: High-velocity conversational customer responses, tool calling, and streaming token generation.
  - **`gemini-2.5-pro`**: Deep analytical reasoning, trend forecasting, and executive business analysis.

### 2. Streamlined Customer Conversation Flow (LangGraph)
- Resilient 5-node state graph focused strictly on customer service:
  - **Customer Router**: Determines customer intent and queries.
  - **Product Search & Discovery**: Locates chemical formulations, industrial hardware, and inventory specs.
  - **Quotation Generator**: Helps customers assemble quotation requests.
  - **Order & Cart Integration**: Directly invokes business-server tool APIs to modify shopping carts.
- Streams live Server-Sent Events (SSE) directly to the Next.js client chat interface.

### 3. Autonomous AI Report Analysis Engine
- Autonomous endpoint: `POST /api/v1/reports/analyze`.
- Takes raw metrics from the Spring Boot business server and utilizes `gemini-2.5-pro` via Vertex AI to synthesize structured executive insights:
  - **Executive Summary**: High-level operational and financial health.
  - **Key Insights & Trends**: SKU velocities, category performance, volume leaders.
  - **Actionable Recommendations**: Clear procurement, pricing, and operational steps.
  - **Risk Alerts**: Imminent stockouts, deteriorating sales velocity, supply delays.
- Authenticated via inter-service `x-api-key` header verification.

---

## 📁 Architecture & Directory Structure

```
multi-agent-server/
├── app/
│   ├── api.py                            # FastAPI application & route registration
│   ├── configs/                          # Logging, config loaders, Langfuse tracking
│   ├── core/
│   │   ├── agents/                       # Customer agents and tools (cart, inventory, products)
│   │   ├── graph/                        # LangGraph workflow builder and executor
│   │   └── llm/                          # ChatGoogleGenerativeAI (Vertex AI: flash & pro)
│   ├── routers/
│   │   ├── chat_router.py                # POST /chat (streaming customer dialogue)
│   │   └── report_analysis_router.py     # POST /api/v1/reports/analyze
│   ├── schemas/                          # Pydantic models for chat and report analysis
│   ├── security/                         # Inter-service x-api-key authentication
│   └── services/
│       └── report_analysis_service.py    # Autonomous Gemini 2.5 Pro reasoning service
├── tests/                                # Pytest test suites (unit & integration)
├── config.json                           # Vertex AI settings, model names, and keys
├── pyproject.toml                        # Poetry dependencies (langchain-google-genai)
└── Dockerfile                            # Production container image
```

---

## ⚙️ Configuration (`config.json`)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8001,
    "reload": false
  },
  "business_server": {
    "api_key": "YOUR_INTER_SERVICE_API_KEY",
    "api_key_name": "x-api-key",
    "base_url": "http://127.0.0.1:8000"
  },
  "vertex_ai": {
    "project": "lak-chemicals",
    "location": "asia-south1",
    "vertexai": true
  },
  "genai": {
    "api_key": "YOUR_VERTEX_AI_API_KEY"
  },
  "genai_normal": {
    "model_name": "gemini-2.5-flash",
    "temperature": 0.0
  },
  "genai_reasoning": {
    "model_name": "gemini-2.5-pro",
    "temperature": 0.5
  },
  "langfuse": {
    "public_key": "pk-lf-...",
    "secret_key": "sk-lf-...",
    "host": "https://cloud.langfuse.com"
  }
}
```

---

## 🌐 API Reference

### 1. Customer Chat (Streaming SSE)
- **Endpoint**: `POST /chat`
- **Payload**:
  ```json
  {
    "message": "Do you have solvent cement in stock?",
    "user_id": "user_123",
    "thread_id": "session_abc"
  }
  ```
- **Response**: Server-Sent Events stream yielding text chunks and tool invocations.

### 2. Autonomous Report Analysis (JSON)
- **Endpoint**: `POST /api/v1/reports/analyze`
- **Headers**: `x-api-key: <INTER_SERVICE_API_KEY>`
- **Payload**:
  ```json
  {
    "report_type": "SALES",
    "data": { "total_revenue": 450000.0, "total_orders": 38 },
    "metadata": { "period": "last_30_days" }
  }
  ```
- **Response**:
  ```json
  {
    "report_type": "SALES",
    "summary": "Revenue grew by 18% over the period driven by industrial adhesives...",
    "insights": ["Chemical solvents constituted 42% of volume..."],
    "recommendations": ["Reorder 200L epoxy resin prior to seasonal price adjustments..."],
    "risk_alerts": ["Fastener supply stock depleted to 12%..."]
  }
  ```

---

## 🛠️ Local Development & Testing

### Installation with Poetry
```bash
cd multi-agent-server
poetry install
```

### Run Unit Tests
```bash
poetry run pytest tests/test_report_analysis.py
```

### Start Local Server
```bash
poetry run python server.py
# Server listening on http://127.0.0.1:8001
```

---

## 🐳 Docker Deployment

### Build Container
```bash
docker build -t lak-chemicals-multi-agent .
```

### Run Container
```bash
docker run -d -p 8001:8001 \
  -e AI_SERVICE_API_KEY="YOUR_KEY" \
  -e VERTEX_API_KEY="YOUR_VERTEX_KEY" \
  -e GCP_PROJECT_ID="lak-chemicals" \
  -e GCP_REGION="asia-south1" \
  --name multi-agent-server \
  lak-chemicals-multi-agent
```
