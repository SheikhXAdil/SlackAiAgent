# Slack AI Agent

An intelligent Slack bot built with **FastAPI** that automatically researches new Slack community members and analyzes their fit for your commercial product using **Google Gemini**, **LangChain**, and **Render PostgreSQL**. The application is designed for deployment on **FastAPI Cloud**.

---

## Features

- **Automatic Member Detection**
  - Listens for new Slack workspace members.
- **AI-Powered Research**
  - Collects publicly available information such as GitHub profiles and company websites.
- **Intelligent Member Analysis**
  - Uses **Google Gemini** through **LangChain** to generate:
    - Fit score
    - Key insights
    - Engagement recommendations
- **Persistent Storage**
  - Stores all analyses in **Render PostgreSQL** before sending them to Slack.
- **Private Slack Reports**
  - Sends formatted analysis reports to a private Slack channel.
- **Comprehensive Logging**
  - Centralized logging for monitoring and debugging.
- **Cloud Ready**
  - Designed for deployment on **FastAPI Cloud**.

---

## Architecture

```
                   Slack Workspace
                          │
                          ▼
                 Socket Mode Events
                          │
                          ▼
                FastAPI + Slack Bolt
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     Member Research              AI Analysis
   (GitHub / Company)       (LangChain + Gemini)
            │                           │
            └─────────────┬─────────────┘
                          ▼
                 PostgreSQL Database
                    (Render.com)
                          │
                          ▼
              Private Slack Report Channel
```

---

## Tech Stack

- FastAPI
- Slack Bolt (Async)
- Google Gemini
- LangChain
- AsyncPG
- PostgreSQL (Render)
- HTTPX
- Pydantic
- Uvicorn

---

## Project Structure

```
.
├── db.py                 # Database connection and queries
├── logger.py             # Logging utility
├── main.py               # FastAPI application & Slack agent
├── models.py             # Pydantic models
├── pyproject.toml
├── uv.lock
├── .python-version
└── .gitignore
```

---

## Prerequisites

- Python 3.12+
- uv (recommended) or pip
- Slack Workspace
- Google AI API Key
- Render PostgreSQL Database

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd SlackAgent
```

#### 2. Install dependencies

Using **uv**:

```bash
uv sync
```

#### 3. Create a Slack App

Create a Slack app and configure:

- Enable **Socket Mode**
- Create an **App-Level Token** with `connections:write`
- Add Bot OAuth Scopes:
  - `chat:write`
  - `channels:read`
  - `users:read`
  - `users:read.email`
- Enable **Event Subscriptions**
- Subscribe to:
  - `team_join`
  - `member_joined_channel`
- Install the app to your workspace.

#### 4. Create a Google AI API Key

Generate a Gemini API key from Google AI Studio.

#### 5. Create a PostgreSQL Database

Create a PostgreSQL database (Render PostgreSQL recommended) and copy the connection string.

#### 6. Configure Environment Variables

Copy `.env.example` to `.env` and provide values for all required environment variables.

#### 7. Run the application

Development:

```bash
uv run fastapi dev
```

Production:

```bash
uv run fastapi run
```

The Slack AI Agent is now ready to receive Slack events and analyze new workspace members.

## Deployment

This project is designed to be deployed on **FastAPI Cloud**.

1. Push the repository to GitHub.
2. Create a new FastAPI Cloud project.
3. Connect the repository.
4. Configure the required environment variables.
5. Deploy.

## Acknowledgements

This project is based on the original **Slack AI Agent** created by **Ania Kubów**.

The original implementation uses **Node.js**, **Express**, and JavaScript. This repository is an independent Python/FastAPI implementation inspired by the original project. While it follows the same overall concept, the backend has been redesigned using FastAPI, asynchronous Python libraries, and FastAPI Cloud deployment.

### Major Changes

- Reimplemented the backend using **FastAPI** instead of Express/Node.js.
- Replaced the JavaScript implementation with **Python**.
- Used **Async Slack Bolt** with FastAPI.
- Used **AsyncPG** for asynchronous PostgreSQL access.
- Deployed the application on **FastAPI Cloud** instead of Render Web Services.
- Connected to a **Render PostgreSQL** database.
- Built the project using modern Python tooling (`uv`, `pyproject.toml`).

### Original Resources

- Original GitHub repository:
  https://github.com/kubowania/slack-ai-agent


- I followed the FreeCodeCamp tutorial featuring **Ania Kubów** while building this Python/FastAPI version:
  https://youtu.be/MnG0ugK2JAI?si=v4oaLdCGSx0XLTWf

- **Ania Kubów** Youtube:
  https://www.youtube.com/@aniakubow

- **FreeCodeCamp** YouTube:
  https://www.youtube.com/@freecodecamp