# Slack AI Agent

An AI-powered **Slack bot for automated community-member research and analysis**, rebuilt with **FastAPI, Python, Google Gemini, LangChain, Slack Bolt, and PostgreSQL**.

This project started from a tutorial by **Ania Kubów / freeCodeCamp**, but I independently reimplemented the backend using **FastAPI** instead of the original Node.js/Express stack and deployed it using **FastAPI Cloud**.

## About

The Slack AI Agent monitors new members joining a Slack workspace, researches publicly available information about them, uses an AI model to analyze their potential fit for a product or community, stores the analysis in PostgreSQL, and sends a formatted report to a private Slack channel.

The overall application concept and functionality were inspired by the original project. The main implementation difference is that this version was **rebuilt in Python using FastAPI**, with a different application structure, async integrations, Python tooling, and deployment workflow.

### How It Works

```text
                Slack Workspace
                       │
                       ▼
              Slack Events / Socket Mode
                       │
                       ▼
               FastAPI + Slack Bolt
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
      Member Research       AI Analysis
     GitHub / Websites    Gemini + LangChain
             │                   │
             └─────────┬─────────┘
                       ▼
                PostgreSQL
                       │
                       ▼
             Private Slack Channel
```

When a new member joins:

1. The Slack application receives the member event.
2. The agent collects publicly available information about the member.
3. The information is passed to the AI analysis pipeline.
4. Google Gemini analyzes the member and generates:

   * Fit score
   * Key insights
   * Engagement recommendations
5. The analysis is stored in PostgreSQL.
6. A formatted report is sent to a private Slack channel.

## My Implementation

Although the project was based on an existing tutorial, I treated it as an opportunity to **rebuild the application using the Python ecosystem rather than simply reproduce the original implementation**.

The original tutorial uses **Node.js/Express and Render**. My implementation makes several significant changes:

* Reimplemented the backend using **FastAPI**
* Replaced the Node.js implementation with **Python**
* Used **Async Slack Bolt** with FastAPI
* Used **AsyncPG** for asynchronous PostgreSQL access
* Used **Google Gemini through LangChain**
* Used **Render PostgreSQL** for persistent storage
* Deployed the application using **FastAPI Cloud**
* Adopted **uv** for Python dependency and environment management
* Structured the project around `pyproject.toml` and `uv.lock`
* Worked through integration and debugging issues using official documentation

These changes made the project particularly useful as a practical introduction to the modern **FastAPI + uv** development workflow.

## Tech Stack

* **Python 3.12+**
* **FastAPI**
* **Slack Bolt for Python (Async)**
* **Google Gemini**
* **LangChain**
* **PostgreSQL**
* **AsyncPG**
* **HTTPX**
* **Pydantic**
* **Uvicorn**
* **uv**
* **FastAPI Cloud**

## Key Features

* Automatic detection of new Slack workspace members
* Public-profile and web research
* AI-powered member analysis
* Fit scoring
* Key insights generation
* Engagement recommendations
* PostgreSQL persistence
* Private Slack reporting
* Asynchronous Slack integration
* Centralized application logging
* Cloud deployment support

## FastAPI & uv

One of the most valuable outcomes of this project was becoming comfortable with a **proper FastAPI project setup using modern Python tooling**.

I used `uv` for dependency management and project environments rather than relying on a traditional `pip`-based workflow.

The project uses:

```text
pyproject.toml
uv.lock
.python-version
```

and can be synchronized and run with:

```bash
uv sync
uv run fastapi dev
```

This experience helped me understand the structure of a modern FastAPI application and the role of tools such as `uv`, `pyproject.toml`, and application servers such as Uvicorn.

I have since carried this knowledge into other **FastAPI-based projects, including my current FYP and production-oriented applications**.

## Installation

### Prerequisites

* Python 3.12+
* `uv`
* A Slack workspace where you can create and install applications
* Google AI API key
* PostgreSQL database

### Clone the Repository

```bash
git clone https://github.com/SheikhXAdil/SlackAiAgent.git
cd SlackAiAgent
```

### Install Dependencies

Using `uv`:

```bash
uv sync
```

### Configure Environment Variables

Create a `.env` file based on the provided example:

```bash
cp .env.example .env
```

Configure the required Slack, Google Gemini, and PostgreSQL credentials.

### Run Locally

For development:

```bash
uv run fastapi dev
```

For a production-style local run:

```bash
uv run fastapi run
```

The application can then receive Slack events and process new workspace members.

## Deployment

The application was deployed using **FastAPI Cloud** rather than the Render web-service deployment used in the original tutorial.

The deployment workflow involved connecting the GitHub repository to FastAPI Cloud and configuring the required environment variables.

The PostgreSQL database was hosted separately using **Render PostgreSQL**.

### Current Deployment Status

The application was successfully deployed on FastAPI Cloud.

However, the **free Render PostgreSQL database used by the project has since expired**, so the deployed application is currently **not operational** because its database dependency is no longer available.

The FastAPI Cloud deployment therefore remains primarily as a record of the deployment work rather than as an actively functioning public application.

## Learning & Development Experience

This project was particularly valuable because I did not rely heavily on AI to produce the implementation.

The tutorial provided the initial application concept and functionality, but I wrote the FastAPI implementation myself and used AI primarily when I needed help **understanding FastAPI concepts or debugging specific issues**.

For the rest of the implementation and troubleshooting, I relied heavily on:

* Reading the **FastAPI documentation**
* Reading the **Slack documentation**
* Debugging integration issues
* Understanding error messages
* Comparing behavior between the original implementation and my Python version
* Experimenting with the application locally

This made the project more than simply following a tutorial. It became an exercise in **translating an existing application architecture into a different technology stack and solving the implementation problems that came with that change**.

It also introduced me to **FastAPI Cloud** and its deployment workflow, giving me practical experience deploying a Python/FastAPI application to a cloud platform.

Most importantly, the project refreshed my backend development skills and helped me become comfortable again with **FastAPI, asynchronous Python, `uv`, PostgreSQL integration, and cloud deployment**.

## Original Tutorial & Attribution

This project was inspired by the original Slack AI Agent created by **Ania Kubów**.

The original project and tutorial were used as the reference for the application's overall functionality and workflow. This repository is an independent **Python/FastAPI reimplementation** with significant changes to the backend technology, tooling, database integration, and deployment approach.

**Original repository:**
https://github.com/kubowania/slack-ai-agent

**Tutorial:**
https://www.youtube.com/watch?v=MnG0ugK2JAI

**Original creator:**
https://www.youtube.com/@aniakubow

## Status

**Completed personal project.**

The project was successfully implemented and deployed during development. The current cloud deployment is inactive because the Render PostgreSQL database used by the application has expired.

The repository is maintained as a record of the implementation and, more importantly, as a practical example of my experience with **FastAPI, asynchronous Python, AI integration, Slack APIs, PostgreSQL, `uv`, and FastAPI Cloud deployment**.
