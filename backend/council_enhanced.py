"""
Enhanced council with epistemics integration.
Adds agreement detection, claim extraction, and calibration tracking.
"""

import time
import hashlib
from typing import List, Dict, Any, Tuple, Optional

from backend.council import (
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings
)
from backend.evaluation import (
    compute_kendalls_w,
    detect_disagreement,
    aggregate_rankings,
    classify_query_domain,
    structured_ranking
)
from backend.claims import extract_claims, format_claims_for_display
from backend.calibration import get_calibration_tracker
from backend.schemas import CouncilMetrics, DisagreementResult
from backend.config import COUNCIL_MODELS, CHAIRMAN_MODEL


async def run_enhanced_council(user_query: str) -> Dict[str, Any]:
    """
    Run the council with enhanced epistemics.
    
    Returns all standard outputs plus:
    - agreement_score: Kendall's W coefficient
    - disagreement: DisagreementResult if models disagree
    - claims: Extracted claims with support/contradiction
    - domain: Detected query domain
    - metrics: CouncilMetrics
    """
    start_time = time.time()
    query_hash = hashlib.sha256(user_query.encode()).hexdigest()[:16]
    
    # Detect domain for weighted scoring
    domain = classify_query_domain(user_query)
    
    # Stage 1: Collect responses
    stage1_results = await stage1_collect_responses(user_query)
    
    if not stage1_results:
        return {
            "error": "All models failed to respond",
            "stage1": [],
            "stage2": [],
            "stage3": {"model": "error", "response": "No responses received"},
            "metadata": {}
        }
    
    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(user_query, stage1_results)
    
    # Compute agreement score (Kendall's W)
    rankings_dict = {}
    for result in stage2_results:
        model = result["model"]
        parsed = result.get("parsed_ranking", [])
        if parsed:
            rankings_dict[model] = parsed
    
    agreement_score = compute_kendalls_w(rankings_dict) if rankings_dict else 0.5
    
    # Detect disagreement
    disagreement = detect_disagreement(rankings_dict, threshold=0.5)
    
    # Calculate aggregate rankings with domain weighting
    aggregate = calculate_aggregate_rankings(stage2_results, label_to_model)
    
    # Extract claims from responses
    try:
        claims_result = await extract_claims(
            user_query,
            [{"model": r["model"], "content": r["response"]} for r in stage1_results],
            CHAIRMAN_MODEL
        )
        claims = format_claims_for_display(claims_result.claims, label_to_model)
        contested_claims = [c for c in claims if c["contradicting"]]
    except Exception as e:
        print(f"Claim extraction failed: {e}")
        claims = []
        contested_claims = []
    
    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results
    )
    
    # Calculate metrics
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Track calibration
    tracker = get_calibration_tracker()
    for result in stage1_results:
        model = result["model"]
        # Use agreement as approximate confidence
        tracker.record_prediction(
            model=model,
            query=user_query,
            stated_confidence=agreement_score,
            prediction=result["response"][:200]  # First 200 chars
        )
    
    # Build enhanced metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate,
        "agreement_score": agreement_score,
        "disagreement": {
            "has_consensus": disagreement.has_consensus,
            "agreement_score": disagreement.agreement_score,
            "factions": disagreement.factions,
            "recommendation": disagreement.recommendation
        },
        "claims": claims,
        "contested_claims": contested_claims,
        "domain": domain,
        "metrics": {
            "query_hash": query_hash,
            "total_time_ms": elapsed_ms,
            "models_queried": len(COUNCIL_MODELS),
            "models_succeeded": len(stage1_results),
            "agreement_score": agreement_score
        }
    }
    
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


def format_stage1_for_api(stage1_results: List[Dict]) -> List[Dict]:
    """Format stage1 results for API response"""
    return [
        {
            "model": r["model"],
            "content": r.get("response", r.get("content", ""))
        }
        for r in stage1_results
    ]


def format_stage2_for_api(stage2_results: List[Dict]) -> List[Dict]:
    """Format stage2 results for API response"""
    return [
        {
            "model": r["model"],
            "evaluation": r.get("ranking", ""),
            "parsed_ranking": r.get("parsed_ranking", [])
        }
        for r in stage2_results
    ]
