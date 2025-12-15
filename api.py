from fastapi import FastAPI
from orchestrator import ScreeningOrchestrator
from typing import List

app = FastAPI(title="PEP & Adverse Media Screening")

orchestrator = ScreeningOrchestrator()


@app.post("/screen")
def screen(name: str, country: str = ""):
    return orchestrator.run(name, country)


@app.post("/batch-screen")
def batch_screen(requests: List[dict]):
    return [
        orchestrator.run(r["name"], r.get("country", ""))
        for r in requests
    ]
