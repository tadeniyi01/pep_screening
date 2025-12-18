from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional

from orchestrator import ScreeningOrchestrator
from schemas.pep_response import ScreeningResponseSchema


app = FastAPI(
    title="PEP & Adverse Media Screening API",
    version="1.0.0"
)

orchestrator = ScreeningOrchestrator()


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class ScreenRequest(BaseModel):
    query: str = Field(..., description="Full name of the individual")
    country: Optional[str] = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class BatchScreenRequest(BaseModel):
    items: List[ScreenRequest]


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "service": "PEP & Adverse Media Screening",
        "status": "running",
        "docs": "/docs"
    }


@app.post("/screen", response_model=ScreeningResponseSchema)
def screen(payload: ScreenRequest):
    """
    Screen a single individual.
    """
    return orchestrator.run(
        query=payload.query,
        country=payload.country,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )


@app.post("/batch-screen", response_model=List[ScreeningResponseSchema])
def screen_batch(payload: BatchScreenRequest):
    """
    Screen multiple individuals in one request.
    """
    results = []

    for item in payload.items:
        results.append(
            orchestrator.run(
                query=item.query,
                country=item.country,
                start_date=item.start_date,
                end_date=item.end_date,
            )
        )

    return results
