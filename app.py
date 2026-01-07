from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import uuid
import traceback

from orchestrator import ScreeningOrchestrator
from schemas.pep_response import ScreeningResponseSchema

app = FastAPI(
    title="PEP & Adverse Media Screening API",
    version="1.0.0"
)

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    logging.error(f"ErrorID={error_id} Path={request.url.path} Error={exc}")
    logging.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error_id,
            "message": "Internal Server Error",
            "detail": str(exc)
        },
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
async def screen(payload: ScreenRequest):
    return await orchestrator.run(
        query=payload.query,
        country=payload.country,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )


@app.post("/batch-screen", response_model=List[ScreeningResponseSchema])
def screen_batch(payload: BatchScreenRequest):
    results = [
        orchestrator.run(
            query=item.query,
            country=item.country,
            start_date=item.start_date,
            end_date=item.end_date,
        )
        for item in payload.items
    ]
    return results
