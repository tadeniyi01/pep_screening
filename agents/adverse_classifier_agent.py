import logging
from typing import List
from models.media_models import MediaItem
from models.llm_schemas import AdverseClassification
from services.llm_service import LLMService
from config.prompts import Prompts

logger = logging.getLogger(__name__)

class AdverseClassifierAgent:
    """
    Classifies news articles using LLM to distinguish between 
    performing official duties and actual adverse involvement.
    """
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def classify(self, name: str, items: List[MediaItem]) -> List[MediaItem]:
        """
        Processes a list of MediaItems and updates their sentiment/score
        based on LLM analysis.
        """
        if not items:
            return []

        # We classify items in parallel or sequence. 
        # For now, sequence is safer for API limits, but we could use asyncio.gather
        import asyncio
        
        async def process_one(item: MediaItem):
            # Skip items that are clearly structured PEP data
            if item.evidence_type == "structured_pep":
                return item

            prompt = Prompts.ADVERSE_CLASSIFICATION.format(
                name=name,
                headline=item.headline,
                excerpt=item.excerpt
            )
            
            try:
                result = await self.llm.generate_structured(prompt, AdverseClassification)
                
                # Update item based on AI classification
                item.inferring = result.sentiment
                
                # If AI says it's not actual adverse involvement, force it to Neutral/Positive
                if not result.is_adverse_involvement:
                    if item.inferring == "Negative":
                        item.inferring = "Neutral"
                
                # Update explanation with the classification reasoning
                item.explanation = result.reasoning
                
            except Exception as e:
                logger.warning(f"[Classifier] Failed to classify item: {e}. Defaulting to Neutral.")
                item.inferring = "Neutral"
            
            return item

        # Execute in parallel
        tasks = [process_one(item) for item in items]
        return await asyncio.gather(*tasks)
