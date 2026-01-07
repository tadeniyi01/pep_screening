
import asyncio
from orchestrator import ScreeningOrchestrator
from config import settings
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)

async def main():
    try:
        orch = ScreeningOrchestrator()
        print("Orchestrator initialized. Running screen...")
        result = await orch.run(query="Bola Ahmed Tinubu", country="Nigeria")
        print("Screening successful!")
        print(f"PEP Level: {result.pep.pep_level}")
    except Exception as e:
        print("Caught exception:")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
