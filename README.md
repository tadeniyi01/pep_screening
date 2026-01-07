# PEP & Adverse Media Screening API

A FastAPI-based application for screening individuals against Politically Exposed Persons (PEP) lists and adverse media sources. This system uses a multi-agent architecture to gather, verify, and resolve identity and reputation data.

## Features
- **Identity Resolution**: Normalizes names and disambiguates common entities.
- **PEP Screening**: Checks against structured databases (e.g., EveryPolitician, OpenSanctions) and unstructured web sources.
- **Adverse Media Check**: Scans news feeds (Google News, RSS) for negative coverage.
- **Audit Logging**: Tracks every screening request and decision in `audit.log`.

## Setup

### Prerequisites
- Python 3.10+
- [Groq](https://groq.com/) API Key (for LLM reasoning)
- [Google News](https://newsapi.org/) API Key (optional, for media)
- [OpenSanctions](https://www.opensanctions.org/) API Key (optional)

### Installation
1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd pep_screenning
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a `.env` file in the root directory:
    ```bash
    cp .env.example .env  # If example exists, otherwise create new
    ```

2.  Add your API keys to `.env`:
    ```ini
    # LLM Providers
    GROQ_API_KEY=your_groq_key_here
    OPENAI_API_KEY=your_openai_key_here  # Optional fallback

    # News & Data Providers
    GNEWS_API_KEY=your_gnews_key_here
    OPENSANCTIONS_API_KEY=your_opensanctions_key_here

    # comma-separated RSS feeds
    RSS_FEEDS=http://feeds.bbci.co.uk/news/world/rss.xml
    ```

## Usage

### Run the Server
```bash
uvicorn app:app --reload
```
The API will be available at `http://localhost:8000`.

### API Documentation
Visit `http://localhost:8000/docs` to see the interactive Swagger UI.

### Endpoints

-   `POST /screen`: Screen a single individual.
    ```json
    {
      "query": "Bola Ahmed Tinubu",
      "country": "Nigeria"
    }
    ```

-   `POST /batch-screen`: Screen multiple individuals.

## Project Structure
-   `app.py`: FastAPI entry point.
-   `orchestrator.py`: Main logic tying agents together.
-   `agents/`: Specialized agents (Identity, PEP, Media).
-   `services/`: External API integrations.
-   `models/`: Domain data models.
