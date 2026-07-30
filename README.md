# SignalForge AI

**AI Data Reliability & Decision Intelligence Platform**

SignalForge AI is a production-oriented platform that helps data and operations teams understand whether their datasets are trustworthy before those datasets are used for analytics, machine learning, or AI applications.

The platform profiles uploaded datasets, detects data-quality problems, identifies statistical anomalies, generates machine-readable reports, and exposes all functionality through versioned APIs. Later phases add natural-language analysis, agentic remediation workflows, ML experiment tracking, drift monitoring, and cloud deployment.

This is not a dashboard-only project and not a basic chatbot. It is an end-to-end AI/data engineering system designed around a real enterprise problem: unreliable data creates unreliable models and business decisions.

---

## Business problem

Organizations often train models or build dashboards using datasets that contain:

- missing values;
- duplicated records;
- unexpected schema changes;
- invalid ranges;
- inconsistent categories;
- statistical outliers;
- stale or drifting features;
- personally identifiable information;
- broken relationships between tables.

These issues can cause incorrect forecasts, unstable models, failed pipelines, and poor decisions.

SignalForge AI provides a reusable reliability layer between raw data and downstream analytics or ML systems.

---

## Core workflow

```text
CSV dataset
    │
    ▼
Upload and validation
    │
    ▼
Schema inference
    │
    ▼
Statistical profiling
    │
    ├── Missing values
    ├── Duplicates
    ├── Cardinality
    ├── Numeric distributions
    └── Category frequencies
    │
    ▼
Quality rule engine
    │
    ▼
Anomaly detection
    │
    ▼
Reliability score
    │
    ▼
JSON report / dashboard / downstream API
```

---

## Why this project is valuable

SignalForge AI demonstrates practical skills requested across AI Engineer, ML Engineer, Data Scientist, and Applied AI Engineer roles:

- Python application engineering
- FastAPI and REST API design
- data profiling and validation
- anomaly detection
- statistical analysis
- modular service architecture
- test automation
- Docker
- observability
- production-oriented error handling
- extensibility for agents, LLMs, SQL, MLflow, cloud, and monitoring

---

## Phase 1 features

- CSV upload endpoint
- file type and size validation
- schema inference
- missing-value analysis
- duplicate-row detection
- unique-value and cardinality statistics
- descriptive statistics for numeric columns
- categorical frequency analysis
- IQR-based anomaly detection
- configurable quality thresholds
- dataset reliability score
- structured issue reporting
- request IDs and processing-time headers
- health and readiness endpoints
- automated pytest coverage
- Docker and Docker Compose support

---

## Planned platform modules

### Data Profiler

Creates dataset and column-level statistics.

### Quality Rule Engine

Evaluates built-in and user-defined expectations.

### Anomaly Service

Detects unusual records, distributions, and feature behavior.

### AI Analyst Agent

Explains quality issues in plain English and recommends corrective actions.

### Remediation Agent

Generates safe transformation plans with human approval.

### Drift Monitor

Compares current and reference datasets to identify feature and schema drift.

### Model Risk Hub

Tracks model performance, data dependencies, and quality-related risks.

### Decision Intelligence Dashboard

Shows data health, business KPIs, anomalies, alerts, and remediation status.

---

## Architecture

```text
                     ┌───────────────────────────┐
                     │ React / Analyst Interface │
                     └─────────────┬─────────────┘
                                   │ HTTPS
                     ┌─────────────▼─────────────┐
                     │ FastAPI Application Layer │
                     │ Validation | API | Tracing│
                     └───────┬───────────┬───────┘
                             │           │
                 ┌───────────▼───┐   ┌───▼──────────────┐
                 │ Dataset Service│   │ Report Service   │
                 └───────────┬───┘   └───┬──────────────┘
                             │           │
                 ┌───────────▼───────────▼──────────────┐
                 │ Data Reliability Engine              │
                 │ Profiling | Rules | Anomalies | Score│
                 └───────┬───────────┬──────────────────┘
                         │           │
             ┌───────────▼───┐   ┌───▼──────────────────┐
             │ Object Storage │   │ Metadata / Results DB│
             │ Local / S3     │   │ PostgreSQL           │
             └───────────────┘   └──────────────────────┘
                         │
             ┌───────────▼──────────────────────────────┐
             │ Future AI and ML Layer                   │
             │ Agents | LLM Explanations | Drift | MLflow│
             └──────────────────────────────────────────┘
```

---

## Repository structure

```text
signalforge-ai-phase1/
├── app/
│   ├── api/routes/
│   │   ├── datasets.py
│   │   └── health.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── anomaly.py
│   │   ├── profiling.py
│   │   └── scoring.py
│   └── main.py
├── data/
│   └── sample_manufacturing.csv
├── tests/
│   ├── test_health.py
│   └── test_profile.py
├── .env.example
├── .gitignore
├── compose.yaml
├── Dockerfile
├── LICENSE
├── Makefile
├── pyproject.toml
└── README.md
```

---

## Run locally

### Requirements

- Python 3.11+
- Git
- Optional: Docker Desktop

### Setup

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -e ".[dev]"
```

Create the environment file:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Run:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

---

## API usage

### Health

```http
GET /api/v1/health
GET /api/v1/ready
```

### Profile a CSV dataset

```http
POST /api/v1/datasets/profile
Content-Type: multipart/form-data
```

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/datasets/profile" \
  -F "file=@data/sample_manufacturing.csv"
```

The response contains:

- row and column counts;
- inferred data types;
- missing values;
- duplicate count;
- numeric statistics;
- categorical summaries;
- outlier counts;
- detected quality issues;
- reliability score.

---

## Reliability scoring

The Phase 1 reliability score begins at 100 and applies transparent penalties for:

- excessive missing data;
- duplicate rows;
- columns with high outlier rates;
- constant columns;
- empty datasets.

The score is intentionally explainable. Later phases will add weighted business rules, historical baselines, and learned risk models.

---

## Sample use case: manufacturing analytics

A manufacturing team receives machine and production data every hour. Before the data is used for failure prediction or throughput optimization, SignalForge AI checks:

- whether required sensor columns are present;
- whether temperature or pressure values are missing;
- whether records are duplicated;
- whether values fall outside expected statistical ranges;
- whether the incoming schema changed;
- whether the data distribution shifted from the training baseline.

This reduces the risk of unreliable predictions and incorrect operational decisions.

---

## Testing

```bash
pytest -q
```

Expected result:

```text
2 passed
```

---

## Docker

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000/docs
```

Stop:

```bash
docker compose down
```

---

## Engineering decisions

### Why data reliability?

AI systems cannot be trusted when their input data is unreliable. Data quality is therefore both a data-engineering problem and an AI-risk problem.

### Why FastAPI?

FastAPI provides typed API contracts, automatic OpenAPI documentation, validation, and a clean path to asynchronous processing.

### Why transparent anomaly detection first?

IQR-based detection is explainable and easy to validate. Future phases will compare it with Isolation Forest and learned multivariate techniques.

### Why a modular service layer?

Profiling, quality rules, anomaly detection, scoring, storage, and AI explanations evolve independently. Separating them supports testing and later service decomposition.

---

## Security roadmap

- JWT authentication
- role-based access
- tenant isolation
- file-size limits
- content-type validation
- malware scanning
- PII detection
- encrypted storage
- audit logs
- rate limiting
- signed upload URLs
- secrets management

---

## Observability roadmap

- OpenTelemetry traces
- Prometheus metrics
- Grafana dashboards
- structured JSON logging
- profiling latency
- file-processing failures
- issue counts by dataset
- reliability score trends
- agent token usage and cost

---

## Phase roadmap

### Phase 1 — Reliability API

- [x] CSV ingestion
- [x] schema inference
- [x] profiling
- [x] duplicates
- [x] missing values
- [x] anomaly detection
- [x] reliability score
- [x] tests
- [x] Docker

### Phase 2 — Enterprise data layer

- [ ] PostgreSQL metadata
- [ ] S3-compatible storage
- [ ] asynchronous jobs
- [ ] dataset history
- [ ] custom quality rules
- [ ] SQL and Excel ingestion

### Phase 3 — AI analyst and remediation agents

- [ ] LangGraph workflows
- [ ] natural-language report
- [ ] root-cause analysis
- [ ] transformation recommendations
- [ ] human approval
- [ ] generated SQL and Python fixes

### Phase 4 — ML and drift

- [ ] Isolation Forest
- [ ] multivariate anomalies
- [ ] schema drift
- [ ] feature drift
- [ ] reference datasets
- [ ] MLflow tracking

### Phase 5 — Dashboard

- [ ] React and TypeScript
- [ ] dataset overview
- [ ] quality scorecards
- [ ] anomaly explorer
- [ ] issue trends
- [ ] remediation workflow

### Phase 6 — Cloud and DevOps

- [ ] GitHub Actions
- [ ] AWS deployment
- [ ] Terraform
- [ ] Redis
- [ ] Kubernetes
- [ ] Prometheus and Grafana
- [ ] load testing

---

## Resume-ready project description

**SignalForge AI — Data Reliability & Decision Intelligence Platform**

Designed and implemented a production-oriented data reliability platform that profiles operational datasets, detects missing values, duplicate records and statistical anomalies, and generates explainable dataset health scores through versioned FastAPI services. Built a modular architecture for rule-based validation, automated testing, containerized deployment, AI-assisted remediation, feature drift monitoring, MLflow integration, and cloud-scale processing.

---

## Interview discussion areas

Be prepared to explain:

- how reliability scoring works;
- why data-quality validation should occur before model inference;
- how IQR anomaly detection works and where it fails;
- how you would support multivariate anomaly detection;
- how you would detect schema and feature drift;
- how asynchronous processing would handle large files;
- how PostgreSQL and object storage would be divided;
- how human approval would control agent-generated fixes;
- how tenant isolation and PII protection would work;
- how you would monitor quality, latency, and failures.

---

## License

MIT License.

## Author

Shekhar Jampula  
AI / Machine Learning Engineer
