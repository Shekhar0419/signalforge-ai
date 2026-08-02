# SignalForge AI

<p align="center">
  <strong>AI-Powered Dataset Quality Intelligence Platform</strong>
  </p>
## Architecture

<p align="center">
  <img src="docs/architecture.png"
       alt="SignalForge AI Architecture"
       width="1000"/>
</p>

<p align="center">
  Profile datasets, detect quality issues, generate cleaning recommendations,
  save cleaned versions, compare changes, and explore reliability trends
  through a production-style FastAPI and React application.
</p>

<p align="center">
  <img
    src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white"
    alt="Python 3.11"
  />
  <img
    src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white"
    alt="FastAPI"
  />
  <img
    src="https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black"
    alt="React"
  />
  <img
    src="https://img.shields.io/badge/TypeScript-Frontend-3178C6?logo=typescript&logoColor=white"
    alt="TypeScript"
  />
  <img
    src="https://img.shields.io/badge/SQLAlchemy-ORM-D71F00"
    alt="SQLAlchemy"
  />
  <img
    src="https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white"
    alt="SQLite"
  />
  <img
    src="https://img.shields.io/badge/Tests-87%20passing-success"
    alt="Tests"
  />
  <img
    src="https://img.shields.io/badge/License-MIT-green"
    alt="MIT License"
  />
</p>

---

## Overview

SignalForge AI is an end-to-end data-quality intelligence platform for analyzing CSV datasets before they are used in analytics, reporting, or machine-learning workflows.

The application combines deterministic profiling, business-rule validation, anomaly detection, automated cleaning, version management, comparison analytics, and an AI-style copilot interface in one workflow.

Users can:

- Upload and profile CSV datasets
- Measure dataset reliability
- Detect missing values, duplicates, outliers, and anomalies
- Review cleaning recommendations
- Preview safe transformations before applying them
- Download cleaned datasets
- Save cleaned versions without overwriting originals
- Reopen historical analyses
- Compare original and cleaned versions
- Visualize reliability trends across a dataset lineage
- Generate reports and cleaning scripts
- Ask dataset-specific questions through the Copilot interface

---

## Key Features

### Dataset Profiling

SignalForge automatically calculates:

- Row and column counts
- Missing-value counts and ratios
- Duplicate rows
- Unique-value statistics
- Numeric summary statistics
- Inferred column types
- Top-value distributions
- Outlier counts and ratios
- Overall reliability score

### Data-Quality Intelligence

The platform identifies:

- Missing values
- Duplicate records
- Invalid or suspicious formats
- Statistical outliers
- Business-rule violations
- Machine-learning anomaly findings
- Potential risks for analytics and model training

### Cleaning Assistant

SignalForge generates cleaning recommendations and executable examples for:

- Pandas
- PySpark
- SQL

The application separates safe automated transformations from operations that require domain review.

### Cleaning Preview

Before creating a new version, users can preview:

- Before-and-after row counts
- Missing-value changes
- Duplicate removal
- Reliability score changes
- Applied cleaning actions
- Review-required actions
- Sample cleaned rows

### Dataset Versioning

Every upload begins as:

```text
Version 1 · ORIGINAL
---

---

# Application Screenshots

The following screenshots demonstrate the complete end-to-end workflow of SignalForge AI, from dataset ingestion through profiling, AI-assisted quality analysis, cleaning, version management, and reliability tracking.

---

## Dashboard

The dashboard provides the primary entry point for the platform. Users can upload CSV datasets, initiate automated profiling, and immediately view the current dataset version and analysis status.

<p align="center">
  <img src="docs/screenshots/dashboard.png" width="1000">
</p>

---

## Dataset Quality Metrics

SignalForge automatically profiles every uploaded dataset and calculates key quality metrics including reliability score, missing values, duplicate records, column statistics, anomaly counts, and overall dataset health.

<p align="center">
  <img src="docs/screenshots/metrics.png" width="1000">
</p>

---

## AI Insights

The platform generates AI-powered insights by combining statistical profiling, business-rule validation, anomaly detection, and quality analysis. These insights help users quickly identify potential data-quality issues before downstream analytics or machine-learning workflows.

<p align="center">
  <img src="docs/screenshots/ai-insights.png" width="1000">
</p>

---

## Cleaning Assistant

The Cleaning Assistant recommends deterministic cleaning operations together with executable code examples. Users can review suggested transformations before applying them.

<p align="center">
  <img src="docs/screenshots/cleaning-assistant.png" width="1000">
</p>

---

## Before & After Cleaning Preview

SignalForge generates a safe transformation preview that allows users to review cleaning results without modifying the original dataset. Users can compare quality metrics, inspect transformed rows, and validate changes before saving a new version.

<p align="center">
  <img src="docs/screenshots/before and after cleaning.png" width="1000">
</p>

---

## Cleaned Dataset Preview

Users can inspect the cleaned dataset before downloading or saving it as a new dataset version, ensuring complete transparency in every transformation.

<p align="center">
  <img src="docs/screenshots/cleaned dataset preview.png" width="1000">
</p>

---

## Dataset Version History

Every cleaned dataset is stored as a separate immutable version. SignalForge preserves the original dataset while allowing users to revisit historical analyses and track dataset evolution over time.

<p align="center">
  <img src="docs/screenshots/dataset history.png" width="1000">
</p>

---

## Dataset Version Comparison

The Version Comparison module provides side-by-side analytics between any two dataset versions. Users can compare reliability score, missing values, duplicate records, outliers, business-rule violations, anomaly counts, and other quality indicators.

<p align="center">
  <img src="docs/screenshots/versions comparison.png" width="1000">
</p>

---

## Reliability Trend Analytics

SignalForge visualizes how overall dataset quality evolves across multiple dataset versions, making it easier to measure the impact of cleaning operations over time.

<p align="center">
  <img src="docs/screenshots/Relibility Trend.png" width="1000">
</p>

---

## AI Data Copilot

The integrated AI Copilot enables users to ask natural-language questions about uploaded datasets, receive contextual insights, understand quality issues, and obtain intelligent recommendations directly within the application.

<p align="center">
  <img src="docs/screenshots/ai data copilot.png" width="1000">
</p>

# Author

## Shekhar Jampula

**AI Engineer | Machine Learning Engineer | Applied AI**

🎓 Master of Science in Computer and Information Sciences  
Saint Louis University

### Connect with me

- **GitHub:** https://github.com/Shekhar0419
- **LinkedIn:** https://www.linkedin.com/in/shekhar-jampula-b586383b8

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

<p align="center">
Built with ❤️ using FastAPI, React, TypeScript, SQLAlchemy, and Python.
</p>
