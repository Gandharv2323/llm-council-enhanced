"""
Structured output schemas for LLM Council.
Replaces regex-based parsing with type-safe Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


class ResponseLabel(str, Enum):
    A = "Response A"
    B = "Response B"
    C = "Response C"
    D = "Response D"
    E = "Response E"
    F = "Response F"


class PairwiseComparison(BaseModel):
    """Result of comparing two responses"""
    response_a: str
    response_b: str
    winner: Literal["A", "B", "tie"]
    confidence: float = Field(ge=0.0, le=1.0, description="0.5=uncertain, 1.0=certain")
    reasoning: str


class ModelEvaluation(BaseModel):
    """Structured evaluation from a single model"""
    rankings: list[str] = Field(description="Ordered list: best first")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    dissent: str | None = Field(default=None, description="If one response differs fundamentally")


class ExtractedClaim(BaseModel):
    """A single factual claim extracted from responses"""
    claim: str
    supporting_models: list[str]
    contradicting_models: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    verification_status: Literal["unverified", "verified_true", "verified_false", "contested"] = "unverified"
    source: str | None = None


class ClaimExtractionResult(BaseModel):
    """All claims extracted from council responses"""
    claims: list[ExtractedClaim]
    agreement_score: float = Field(ge=0.0, le=1.0)
    high_disagreement_claims: list[str] = Field(default_factory=list)


class AggregatedScore(BaseModel):
    """Final score for a response after aggregation"""
    response_id: str
    model_name: str
    raw_score: float
    weighted_score: float
    rank: int
    votes_first: int
    votes_last: int


class DisagreementResult(BaseModel):
    """Detected disagreement between models"""
    has_consensus: bool
    agreement_score: float = Field(ge=0.0, le=1.0, description="Kendall's W")
    factions: list[dict] = Field(default_factory=list)
    recommendation: str


class CouncilMetrics(BaseModel):
    """Metrics for a single council query"""
    query_hash: str
    total_cost_usd: float
    total_time_ms: int
    models_queried: int
    models_succeeded: int
    agreement_score: float
    confidence_mean: float
    confidence_std: float


class CostEstimate(BaseModel):
    """Pre-flight cost estimation"""
    estimated_cost_min: float
    estimated_cost_max: float
    estimated_tokens_input: int
    estimated_tokens_output: int
    estimated_time_seconds: float
    model_breakdown: dict[str, float]


class CalibrationDataPoint(BaseModel):
    """Single calibration measurement"""
    model: str
    query_hash: str
    stated_confidence: float
    prediction: str
    ground_truth: str | None = None
    correct: bool | None = None
    timestamp: str


class CalibrationCurve(BaseModel):
    """Calibration curve for a model"""
    model: str
    buckets: dict[str, float]  # {"0.5": 0.52, "0.7": 0.68, ...}
    total_predictions: int
    brier_score: float | None = None


# Domain expertise weights
EXPERTISE_WEIGHTS: dict[str, dict[str, float]] = {
    "math": {
        "deepseek": 0.9, "gemini": 0.7, "llama": 0.5, "gemma": 0.4,
        "gpt": 0.8, "claude": 0.7, "mistral": 0.5
    },
    "code": {
        "deepseek": 0.85, "gemini": 0.7, "llama": 0.7, "gemma": 0.5,
        "gpt": 0.9, "claude": 0.85, "mistral": 0.6
    },
    "creative": {
        "deepseek": 0.4, "gemini": 0.8, "llama": 0.7, "gemma": 0.6,
        "gpt": 0.85, "claude": 0.9, "mistral": 0.6
    },
    "factual": {
        "deepseek": 0.7, "gemini": 0.8, "llama": 0.6, "gemma": 0.6,
        "gpt": 0.8, "claude": 0.75, "mistral": 0.5
    },
    "reasoning": {
        "deepseek": 0.9, "gemini": 0.75, "llama": 0.6, "gemma": 0.5,
        "gpt": 0.85, "claude": 0.8, "mistral": 0.5
    },
}


def get_model_weight(model_id: str, domain: str) -> float:
    """Get expertise weight for a model in a domain"""
    domain_weights = EXPERTISE_WEIGHTS.get(domain, EXPERTISE_WEIGHTS["factual"])
    for key, weight in domain_weights.items():
        if key in model_id.lower():
            return weight
    return 0.5  # Default weight
