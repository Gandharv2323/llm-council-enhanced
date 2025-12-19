"""
Evaluation pipeline for LLM Council.
Implements pairwise preference aggregation with Bradley-Terry model.
"""

import asyncio
import itertools
import math
from typing import Any

from backend.schemas import (
    PairwiseComparison,
    ModelEvaluation,
    AggregatedScore,
    DisagreementResult,
    get_model_weight,
)
from backend.openrouter import query_model


PAIRWISE_EVALUATION_PROMPT = """Compare these two responses to the question: "{question}"

Response A:
{response_a}

Response B:
{response_b}

Which response is better in terms of accuracy, completeness, and clarity?

You MUST respond with ONLY valid JSON in this exact format:
{{
    "response_a": "brief summary of Response A",
    "response_b": "brief summary of Response B",
    "winner": "A" or "B" or "tie",
    "confidence": 0.5 to 1.0,
    "reasoning": "why you chose this"
}}
"""

STRUCTURED_RANKING_PROMPT = """You are evaluating multiple responses to this question: "{question}"

{responses_block}

Rank ALL responses from best to worst. Be objective.

You MUST respond with ONLY valid JSON in this exact format:
{{
    "rankings": ["Response X", "Response Y", ...],
    "confidence": 0.5 to 1.0,
    "reasoning": "explanation",
    "dissent": null or "explanation if one response fundamentally differs"
}}
"""


async def pairwise_compare(
    question: str,
    response_a: dict,
    response_b: dict,
    judge_model: str
) -> PairwiseComparison:
    """Compare two responses using a judge model"""
    prompt = PAIRWISE_EVALUATION_PROMPT.format(
        question=question,
        response_a=response_a["content"],
        response_b=response_b["content"]
    )
    
    result = await query_model(judge_model, prompt, json_mode=True)
    
    try:
        import json
        data = json.loads(result["content"])
        return PairwiseComparison(**data)
    except Exception:
        # Fallback: try to extract winner from text
        content = result["content"].lower()
        if "response a" in content and "better" in content:
            winner = "A"
        elif "response b" in content and "better" in content:
            winner = "B"
        else:
            winner = "tie"
        
        return PairwiseComparison(
            response_a=response_a["model"],
            response_b=response_b["model"],
            winner=winner,
            confidence=0.5,
            reasoning="Fallback parsing"
        )


async def structured_ranking(
    question: str,
    responses: list[dict],
    judge_model: str
) -> ModelEvaluation:
    """Get structured ranking from a judge model"""
    responses_block = "\n\n".join([
        f"Response {chr(65+i)} (from {r['model']}):\n{r['content']}"
        for i, r in enumerate(responses)
    ])
    
    prompt = STRUCTURED_RANKING_PROMPT.format(
        question=question,
        responses_block=responses_block
    )
    
    result = await query_model(judge_model, prompt, json_mode=True)
    
    try:
        import json
        data = json.loads(result["content"])
        return ModelEvaluation(**data)
    except Exception:
        # Fallback: extract Response X patterns
        import re
        matches = re.findall(r"Response ([A-F])", result["content"])
        rankings = [f"Response {m}" for m in matches]
        if not rankings:
            rankings = [f"Response {chr(65+i)}" for i in range(len(responses))]
        
        return ModelEvaluation(
            rankings=rankings,
            confidence=0.5,
            reasoning="Fallback parsing"
        )


async def stage2_pairwise_evaluation(
    question: str,
    responses: list[dict],
    judge_models: list[str]
) -> list[PairwiseComparison]:
    """Collect pairwise comparisons from all judges"""
    pairs = list(itertools.combinations(enumerate(responses), 2))
    
    async def compare_pair(pair, judge):
        (i, resp_a), (j, resp_b) = pair
        comparison = await pairwise_compare(question, resp_a, resp_b, judge)
        comparison.response_a = f"Response {chr(65+i)}"
        comparison.response_b = f"Response {chr(65+j)}"
        return comparison
    
    tasks = [
        compare_pair(pair, judge)
        for pair in pairs
        for judge in judge_models
    ]
    
    return await asyncio.gather(*tasks, return_exceptions=True)


def bradley_terry_scores(comparisons: list[PairwiseComparison]) -> dict[str, float]:
    """
    Compute Bradley-Terry preference scores from pairwise comparisons.
    Uses iterative maximum likelihood estimation.
    """
    # Extract all unique responses
    responses = set()
    for c in comparisons:
        if isinstance(c, PairwiseComparison):
            responses.add(c.response_a)
            responses.add(c.response_b)
    
    if not responses:
        return {}
    
    responses = sorted(responses)
    n = len(responses)
    
    # Initialize scores uniformly
    scores = {r: 1.0 for r in responses}
    
    # Count wins for each pair
    wins = {r: {s: 0 for s in responses} for r in responses}
    for c in comparisons:
        if not isinstance(c, PairwiseComparison):
            continue
        if c.winner == "A":
            wins[c.response_a][c.response_b] += c.confidence
        elif c.winner == "B":
            wins[c.response_b][c.response_a] += c.confidence
        else:  # tie
            wins[c.response_a][c.response_b] += 0.5 * c.confidence
            wins[c.response_b][c.response_a] += 0.5 * c.confidence
    
    # Iterative update (simplified Bradley-Terry)
    for _ in range(20):
        new_scores = {}
        for r in responses:
            numerator = sum(wins[r].values())
            denominator = sum(
                (wins[r][s] + wins[s][r]) / (scores[r] + scores[s])
                for s in responses if s != r
            )
            new_scores[r] = numerator / max(denominator, 0.001)
        
        # Normalize
        total = sum(new_scores.values())
        scores = {r: s / total for r, s in new_scores.items()}
    
    return scores


def compute_kendalls_w(rankings: dict[str, list[str]]) -> float:
    """
    Compute Kendall's coefficient of concordance (W).
    Returns 0.0 (no agreement) to 1.0 (perfect agreement).
    """
    if len(rankings) < 2:
        return 1.0
    
    judges = list(rankings.keys())
    items = rankings[judges[0]]
    n_items = len(items)
    n_judges = len(judges)
    
    if n_items < 2:
        return 1.0
    
    # Convert to rank matrix
    rank_matrix = []
    for judge in judges:
        ranking = rankings[judge]
        ranks = {item: i + 1 for i, item in enumerate(ranking)}
        rank_matrix.append([ranks.get(item, n_items) for item in items])
    
    # Compute sum of ranks for each item
    rank_sums = [sum(row[i] for row in rank_matrix) for i in range(n_items)]
    
    # Compute S (sum of squared deviations)
    mean_rank_sum = sum(rank_sums) / n_items
    S = sum((rs - mean_rank_sum) ** 2 for rs in rank_sums)
    
    # Maximum possible S
    S_max = (n_judges ** 2 * (n_items ** 3 - n_items)) / 12
    
    W = S / S_max if S_max > 0 else 0
    return min(max(W, 0.0), 1.0)


def detect_disagreement(
    rankings: dict[str, list[str]],
    threshold: float = 0.5
) -> DisagreementResult:
    """Detect if there's significant disagreement among judges"""
    W = compute_kendalls_w(rankings)
    
    if W >= threshold:
        return DisagreementResult(
            has_consensus=True,
            agreement_score=W,
            factions=[],
            recommendation="Council reached consensus"
        )
    
    # Identify factions (simplified: group by first choice)
    factions_dict: dict[str, list[str]] = {}
    for judge, ranking in rankings.items():
        first_choice = ranking[0] if ranking else "unknown"
        if first_choice not in factions_dict:
            factions_dict[first_choice] = []
        factions_dict[first_choice].append(judge)
    
    factions = [
        {"position": pos, "models": models}
        for pos, models in factions_dict.items()
    ]
    
    return DisagreementResult(
        has_consensus=False,
        agreement_score=W,
        factions=factions,
        recommendation="Council disagrees. Review competing positions."
    )


def aggregate_rankings(
    rankings: dict[str, ModelEvaluation],
    label_to_model: dict[str, str],
    domain: str = "factual"
) -> list[AggregatedScore]:
    """
    Aggregate rankings from multiple judges with domain expertise weighting.
    """
    all_responses = set()
    for eval_result in rankings.values():
        all_responses.update(eval_result.rankings)
    
    scores: dict[str, dict] = {r: {"weighted_sum": 0, "weight_total": 0, "first": 0, "last": 0} for r in all_responses}
    
    for judge_model, eval_result in rankings.items():
        weight = get_model_weight(judge_model, domain)
        n = len(eval_result.rankings)
        
        for rank_idx, response in enumerate(eval_result.rankings):
            # Convert rank to score (1st = n points, last = 1 point)
            rank_score = n - rank_idx
            scores[response]["weighted_sum"] += rank_score * weight * eval_result.confidence
            scores[response]["weight_total"] += weight * eval_result.confidence
            
            if rank_idx == 0:
                scores[response]["first"] += 1
            if rank_idx == n - 1:
                scores[response]["last"] += 1
    
    # Compute final scores
    results = []
    for response, data in scores.items():
        weighted_score = data["weighted_sum"] / max(data["weight_total"], 0.001)
        results.append(AggregatedScore(
            response_id=response,
            model_name=label_to_model.get(response, response),
            raw_score=data["weighted_sum"],
            weighted_score=weighted_score,
            rank=0,  # Will be set below
            votes_first=data["first"],
            votes_last=data["last"]
        ))
    
    # Sort by weighted score and assign ranks
    results.sort(key=lambda x: x.weighted_score, reverse=True)
    for i, r in enumerate(results):
        r.rank = i + 1
    
    return results


def classify_query_domain(query: str) -> str:
    """Simple heuristic to classify query domain"""
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in ["code", "program", "function", "bug", "error", "python", "javascript"]):
        return "code"
    if any(kw in query_lower for kw in ["math", "calculate", "equation", "prove", "theorem"]):
        return "math"
    if any(kw in query_lower for kw in ["write", "story", "poem", "creative", "imagine"]):
        return "creative"
    if any(kw in query_lower for kw in ["why", "how", "explain", "reason", "logic"]):
        return "reasoning"
    
    return "factual"
