import asyncio
import logging
import sys
import os

sys.path.append("/home/haji/Documents/mahoun-backup-20260507-042302/mahoun-platform-full")

from mahoun.reasoning.graph_symbolic_bridge import GraphSymbolicBridge
from mahoun.reasoning.symbolic_reasoner import SymbolicReasoningEngine
from mahoun.pipelines.ingestion.hardened_legal_pipeline import HardenedLegalPipeline
from mahoun.pipelines.ingestion.llm_refiner import LLMRefinementService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verification")

async def verify_hardening():
    logger.info("Starting hardening verification...")
    
    # 1. Verify Bridge Wiring
    logger.info("Testing GraphSymbolicBridge initialization...")
    try:
        bridge = GraphSymbolicBridge()
        engine = SymbolicReasoningEngine()
        logger.info("✅ GraphSymbolicBridge initialized successfully.")
    except Exception as e:
        logger.error(f"❌ GraphSymbolicBridge initialization failed: {e}")

    # 2. Verify Hardened Pipeline Wiring
    logger.info("Testing HardenedLegalPipeline wiring...")
    try:
        refiner = LLMRefinementService(enable_refinement=True)
        pipeline = HardenedLegalPipeline(refiner=refiner)
        logger.info("✅ HardenedLegalPipeline wired successfully.")
    except Exception as e:
        logger.error(f"❌ HardenedLegalPipeline wiring failed: {e}")

    # 3. Verify Semantic Matcher
    try:
        from mahoun.reasoning.semantic_matcher import SemanticMatcher
        logger.info("Testing SemanticMatcher...")
        matcher = SemanticMatcher()
        is_contr = matcher.are_contradictory("فسخ مجاز است", "فسخ ممنوع است")
        if is_contr:
            logger.info("✅ SemanticMatcher contradiction detection working.")
        else:
            logger.error("❌ SemanticMatcher contradiction detection failed.")
    except Exception as e:
        logger.error(f"❌ SemanticMatcher failed: {e}")

    logger.info("Verification complete.")

if __name__ == "__main__":
    asyncio.run(verify_hardening())
