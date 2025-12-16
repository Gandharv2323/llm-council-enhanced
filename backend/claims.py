"""
Claim extraction and verification for LLM Council.
Extracts atomic claims from responses and checks for agreement/disagreement.
"""

import asyncio
import json
from typing import Optional

from schemas import ExtractedClaim, ClaimExtractionResult
from openrouter import query_model


CLAIM_EXTRACTION_PROMPT = """Analyze these responses to the question: "{question}"

{responses_block}

Extract all distinct factual claims made across these responses.
For each claim, note which responses support it and which contradict it.

Respond with ONLY valid JSON in this exact format:
{{
    "claims": [
        {{
            "claim": "specific factual statement",
            "supporting_models": ["Response A", "Response B"],
            "contradicting_models": ["Response C"],
            "confidence": 0.5 to 1.0
        }}
    ],
    "agreement_score": 0.0 to 1.0,
    "high_disagreement_claims": ["claim text that models disagree on"]
}}
"""

CLAIM_VERIFICATION_PROMPT = """Verify this claim: "{claim}"

Based on your knowledge, is this claim:
- TRUE: The claim is factually accurate
- FALSE: The claim is factually inaccurate
- CONTESTED: The claim is debatable or depends on context
- UNVERIFIABLE: Cannot be determined without external sources

Respond with ONLY valid JSON:
{{
    "status": "verified_true" or "verified_false" or "contested" or "unverified",
    "explanation": "brief explanation",
    "source": "reference if applicable"
}}
"""


async def extract_claims(
    question: str,
    responses: list[dict],
    extractor_model: str
) -> ClaimExtractionResult:
    """Extract factual claims from council responses"""
    responses_block = "\n\n".join([
        f"Response {chr(65+i)} (from {r['model']}):\n{r['content']}"
        for i, r in enumerate(responses)
    ])
    
    prompt = CLAIM_EXTRACTION_PROMPT.format(
        question=question,
        responses_block=responses_block
    )
    
    result = await query_model(extractor_model, prompt, json_mode=True)
    
    try:
        data = json.loads(result["content"])
        claims = [ExtractedClaim(**c) for c in data.get("claims", [])]
        return ClaimExtractionResult(
            claims=claims,
            agreement_score=data.get("agreement_score", 0.5),
            high_disagreement_claims=data.get("high_disagreement_claims", [])
        )
    except Exception as e:
        return ClaimExtractionResult(
            claims=[],
            agreement_score=0.5,
            high_disagreement_claims=[]
        )


async def verify_claim(
    claim: ExtractedClaim,
    verifier_model: str
) -> ExtractedClaim:
    """Verify a single claim using an LLM"""
    prompt = CLAIM_VERIFICATION_PROMPT.format(claim=claim.claim)
    
    result = await query_model(verifier_model, prompt, json_mode=True)
    
    try:
        data = json.loads(result["content"])
        claim.verification_status = data.get("status", "unverified")
        claim.source = data.get("source")
        return claim
    except Exception:
        return claim


async def verify_all_claims(
    claims: list[ExtractedClaim],
    verifier_model: str,
    max_concurrent: int = 3
) -> list[ExtractedClaim]:
    """Verify multiple claims with concurrency limit"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def verify_with_limit(claim):
        async with semaphore:
            return await verify_claim(claim, verifier_model)
    
    verified = await asyncio.gather(*[verify_with_limit(c) for c in claims])
    return list(verified)


def identify_contested_claims(claims: list[ExtractedClaim]) -> list[ExtractedClaim]:
    """Identify claims where models disagree"""
    contested = []
    for claim in claims:
        if claim.contradicting_models and claim.supporting_models:
            contested.append(claim)
    return contested


def compute_claim_agreement(claims: list[ExtractedClaim]) -> float:
    """Compute overall agreement score based on claims"""
    if not claims:
        return 1.0
    
    agreement_scores = []
    for claim in claims:
        n_support = len(claim.supporting_models)
        n_contradict = len(claim.contradicting_models)
        total = n_support + n_contradict
        if total > 0:
            agreement_scores.append(n_support / total)
    
    return sum(agreement_scores) / len(agreement_scores) if agreement_scores else 1.0


def format_claims_for_display(
    claims: list[ExtractedClaim],
    label_to_model: dict[str, str]
) -> list[dict]:
    """Format claims for frontend display with model names"""
    formatted = []
    for claim in claims:
        formatted.append({
            "claim": claim.claim,
            "supporting": [
                label_to_model.get(label, label) 
                for label in claim.supporting_models
            ],
            "contradicting": [
                label_to_model.get(label, label)
                for label in claim.contradicting_models
            ],
            "confidence": claim.confidence,
            "status": claim.verification_status,
            "source": claim.source
        })
    return formatted
