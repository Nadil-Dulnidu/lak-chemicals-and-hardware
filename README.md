# 🛠️ Lak Chemicals and Hardware - AI Powered Hardware Store Management System

Lak Chemicals and Hardware is a modern, AI-powered store management system designed for hardware and chemical retailers. It integrates a Next.js frontend, a FastAPI business server, and a LangGraph-powered multi-agent AI system to streamline inventory, sales, quotations, and customer interactions.

## 🔗 Link to the Project Repository

- Repository: [Lak Chemicals and Hardware](https://github.com/Nadil-Dulnidu/lak-chemicals-and-hardware)

## 🤔 Problem Space
### Problems to Solve / Requirements to Create

Traditional hardware and chemical retail operations are often plagued by manual processes, inventory discrepancies, and slow customer service. Lak Chemicals and Hardware addresses these challenges by providing:

* A centralized platform for inventory and order management.
* An automated quotation system for quick pricing.
* AI-driven insights for sales and product performance.
* Secure role-based access control and payment processing.

### 👉 Problem: Manual & Fragmented Operations

#### Problem Statement:
Traditional hardware stores rely on manual inventory tracking and paper-based quotations, leading to stockouts, pricing inconsistencies, and delayed customer service.

#### Current Solution:
The platform provides a centralized digital environment for real-time stock tracking, automated reorder alerts, and digital quotation generation.

#### How do we know it is a problem?
* **User Feedback**: Customers experience long wait times for custom pricing and stock availability.
* **Metrics**: High variance in manual inventory audits vs. actual stock.

### 👉 Problem: Complex Data Analysis for Business Decisions

#### Problem Statement:
Store owners lack accessible tools to analyze sales trends, predict demand, and identify underperforming products.

#### Current Solution:
A LangGraph-powered multi-agent system provides natural language access to complex data analytics (e.g., product performance, sales trends).

#### How do we know it is a problem?
* **Evidence**: Overstocking of perishable chemical items leading to waste.
* **Metrics**: Inability to quickly generate actionable sales reports.

### 👉 Problem: Secure Role-Based Access & Payments

#### Problem Statement:
Managing distinct roles (Admin, Staff, Customer) and handling financial transactions securely is a critical requirement.

#### Current Solution:
Integration with Clerk for identity management and Stripe for secure, compliant payment processing.

### ⭐ Why Solve These Problems?

* *Reason 1*: Automation reduces human error in inventory tracking, preventing costly stockouts or overstocking.
* *Reason 2*: Empowering managers with AI-driven insights allows for data-backed business decisions, improving profitability.

## 🎯 Project Goals
#### Company Objective

Modernize the retail experience for hardware and chemical supplies through digitalization and artificial intelligence.

#### Project Goals

* Develop a high-performance, responsive web frontend.
* Implement a robust backend capable of handling complex business logic.
* Integrate multi-agent AI workflows to assist users and staff.
* Ensure secure and seamless payment integrations.

## 👥 User Stories
### User Type: Customer

**Goals:**
* Browse products, request quotations, and place orders.
  **Needs:**
* Easy search, transparent pricing, and secure checkout.
  **Characteristics:**
* Contractors, DIY enthusiasts, or industrial buyers.

### User Type: Store Staff / Manager

**Goals:**
* Manage inventory levels, process orders, and update supplier info.
  **Needs:**
* Intuitive dashboards, quick access to data, and reorder tools.

### User Type: Administrator

**Goals:**
* Oversee business operations and analyze financial performance.
  **Needs:**
* Advanced reporting tools and full system access.

## 🌟 Design Space
### UI Design
The interface is designed to be sleek, efficient, and accessible.
* **Modern Dashboard**: Role-specific views for staff and admins.
* **Smart Search**: AI-assisted product discovery.

### Design System 🎨

#### ShadCN UI & Tailwind CSS 4

The frontend leverages **ShadCN UI** built on top of **Tailwind CSS 4**, ensuring:
* Consistency across all interactive components.
* Optimized build times and modern CSS capabilities.
* Fully responsive layouts tailored for both mobile and desktop users.

## 🏗️ Development Phase

### Technology Stack Selection

#### Frontend - Next.js (React 19)
* **Server-Side Rendering**: Fast initial load times and SEO benefits.
* **Vercel AI SDK**: Seamless integration with the AI multi-agent backend.

#### Backend - FastAPI
* **High Performance**: Asynchronous request handling.
* **Type Safety**: Pydantic models for request/response validation.

#### Multi-Agent Orchestration - LangGraph
* **Stateful Workflows**: Manages complex interactions between multiple specialized agents.
* **LangChain Integration**: Leverages Google GenAI (Gemini) for natural language processing.

### Development Workflow

#### Frontend (`/client`)
Built with Next.js, utilizing TypeScript for type safety. Handles client-side state, Clerk authentication, and streaming responses from AI agents.

#### API Gateway (`/api-gateway`)
Acts as the reverse proxy and central router for client requests, directing traffic to the appropriate microservices.

#### Business Server (`/business-server`)
Manages core business entities: Products, Orders, Suppliers, and Quotations. Utilizes SQLAlchemy with PostgreSQL/SQLite.

#### Multi-Agent Server (`/multi-agent-server`)
Houses the AI logic. Contains specialized tools for web search, inventory analysis, and sales reporting.

## 🌟 Key Features of the Software

* **Automated Quotations**: Generate and track custom price quotes.
* **AI Business Advisor**: Ask the multi-agent system about top-selling items or stock predictions.
* **Secure Payments**: Stripe integration for order finalization.
* **Supplier Tracking**: Manage supply chains effectively.

## 🚧 Challenges Faced & Solutions
### Problem 1: Orchestrating Multiple Specialized AI Agents
**Solution**: Utilized **LangGraph** to define strict state transitions and tool-sharing protocols among agents.

### Problem 2: Real-time Data Consistency
**Solution**: Implemented robust caching and background worker tasks in FastAPI.
