from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from orchestrator import ScreeningOrchestrator
from schemas.pep_response import ScreeningResponseSchema


app = FastAPI(
    title="PEP & Adverse Media Screening API",
    version="1.0.0"
)

orchestrator = ScreeningOrchestrator()


# ---------- Models ----------

class ScreenRequest(BaseModel):
    name: str
    country: str = ""


# ---------- Routes ----------

@app.get("/")
def root():
    return {
        "service": "PEP & Adverse Media Screening",
        "status": "running",
        "docs": "/docs"
    }

@app.post("/screen", response_model=ScreeningResponseSchema)
def screen(payload: dict):
    return orchestrator.run(
        query=payload.get("query"),
        country=payload.get("country"),
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date")
    )


@app.post("/batch-screen")
def screen_batch(payload: list):
    return [orchestrator.run(**item) for item in payload]
