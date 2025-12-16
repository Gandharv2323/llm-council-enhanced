"""
Benchmark runner for LLM Council.
Supports running councils on standard datasets with ablations.
"""

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Literal, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkQuestion:
    """A single benchmark question"""
    id: str
    question: str
    answer: str
    category: str = ""
    difficulty: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result for a single question"""
    question_id: str
    question: str
    ground_truth: str
    council_answer: str
    correct: bool
    agreement_score: float
    total_cost: float
    total_time_ms: int
    per_model_answers: dict[str, str] = field(default_factory=dict)
    per_model_correct: dict[str, bool] = field(default_factory=dict)


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run"""
    name: str
    dataset_path: str
    council_models: list[str]
    chairman_model: str
    skip_stage2: bool = False
    skip_stage3: bool = False
    max_questions: Optional[int] = None
    timeout_per_question: float = 60.0


@dataclass
class AblationConfig:
    """Configuration for an ablation study"""
    name: str
    remove_models: list[str] = field(default_factory=list)
    skip_stage2: bool = False
    alternative_chairman: Optional[str] = None
    single_model_baseline: Optional[str] = None


@dataclass
class BenchmarkReport:
    """Final benchmark report"""
    config_name: str
    total_questions: int
    correct: int
    accuracy: float
    avg_agreement: float
    avg_time_ms: float
    total_cost: float
    per_model_accuracy: dict[str, float]
    results: list[BenchmarkResult]


def load_dataset(path: str, format: str = "auto") -> list[BenchmarkQuestion]:
    """Load benchmark dataset from file"""
    path = Path(path)
    
    if format == "auto":
        format = path.suffix.lstrip(".")
    
    with open(path, "r", encoding="utf-8") as f:
        if format == "json":
            data = json.load(f)
        elif format == "jsonl":
            data = [json.loads(line) for line in f if line.strip()]
        else:
            raise ValueError(f"Unknown format: {format}")
    
    questions = []
    for i, item in enumerate(data):
        questions.append(BenchmarkQuestion(
            id=item.get("id", str(i)),
            question=item.get("question", item.get("prompt", "")),
            answer=item.get("answer", item.get("target", "")),
            category=item.get("category", item.get("subject", "")),
            difficulty=item.get("difficulty", ""),
            metadata=item
        ))
    
    return questions


def evaluate_answer(council_answer: str, ground_truth: str) -> bool:
    """Evaluate if council answer matches ground truth"""
    answer_lower = council_answer.lower().strip()
    truth_lower = ground_truth.lower().strip()
    
    # Exact match
    if answer_lower == truth_lower:
        return True
    
    # Contains match (for short answers)
    if len(truth_lower) < 50:
        if truth_lower in answer_lower:
            return True
        # First word match
        truth_first = truth_lower.split()[0] if truth_lower else ""
        if truth_first and truth_first in answer_lower.split()[:10]:
            return True
    
    # Letter answer (A/B/C/D)
    if len(truth_lower) == 1 and truth_lower.isalpha():
        # Look for patterns like "answer is A" or "(A)" or "A."
        import re
        pattern = rf"(?:answer|correct|is|chose|select)[:\s]*[(\[]?{truth_lower}[)\].]?"
        if re.search(pattern, answer_lower):
            return True
        # Check if first capital letter matches
        first_letter = re.search(r"\b([A-D])\b", council_answer)
        if first_letter and first_letter.group(1).lower() == truth_lower:
            return True
    
    return False


async def run_single_question(
    question: BenchmarkQuestion,
    config: BenchmarkConfig,
    council_func
) -> BenchmarkResult:
    """Run council on a single question"""
    start_time = time.time()
    
    try:
        result = await asyncio.wait_for(
            council_func(question.question, config),
            timeout=config.timeout_per_question
        )
    except asyncio.TimeoutError:
        return BenchmarkResult(
            question_id=question.id,
            question=question.question,
            ground_truth=question.answer,
            council_answer="[TIMEOUT]",
            correct=False,
            agreement_score=0.0,
            total_cost=0.0,
            total_time_ms=int(config.timeout_per_question * 1000)
        )
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    council_answer = result.get("stage3", result.get("final_answer", ""))
    correct = evaluate_answer(council_answer, question.answer)
    
    per_model_answers = {}
    per_model_correct = {}
    for resp in result.get("stage1", []):
        model = resp.get("model", "unknown")
        content = resp.get("content", "")
        per_model_answers[model] = content
        per_model_correct[model] = evaluate_answer(content, question.answer)
    
    return BenchmarkResult(
        question_id=question.id,
        question=question.question,
        ground_truth=question.answer,
        council_answer=council_answer,
        correct=correct,
        agreement_score=result.get("agreement_score", 0.0),
        total_cost=result.get("total_cost", 0.0),
        total_time_ms=elapsed_ms,
        per_model_answers=per_model_answers,
        per_model_correct=per_model_correct
    )


async def run_benchmark(
    config: BenchmarkConfig,
    council_func,
    progress_callback=None
) -> BenchmarkReport:
    """Run full benchmark"""
    questions = load_dataset(config.dataset_path)
    
    if config.max_questions:
        questions = questions[:config.max_questions]
    
    results = []
    for i, question in enumerate(questions):
        if progress_callback:
            progress_callback(i, len(questions), question.id)
        
        result = await run_single_question(question, config, council_func)
        results.append(result)
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    # Aggregate
    correct = sum(1 for r in results if r.correct)
    accuracy = correct / len(results) if results else 0
    
    # Per-model accuracy
    model_correct = {}
    model_total = {}
    for r in results:
        for model, is_correct in r.per_model_correct.items():
            model_correct[model] = model_correct.get(model, 0) + (1 if is_correct else 0)
            model_total[model] = model_total.get(model, 0) + 1
    
    per_model_accuracy = {
        m: model_correct[m] / model_total[m]
        for m in model_total
    }
    
    return BenchmarkReport(
        config_name=config.name,
        total_questions=len(results),
        correct=correct,
        accuracy=accuracy,
        avg_agreement=sum(r.agreement_score for r in results) / len(results) if results else 0,
        avg_time_ms=sum(r.total_time_ms for r in results) / len(results) if results else 0,
        total_cost=sum(r.total_cost for r in results),
        per_model_accuracy=per_model_accuracy,
        results=results
    )


async def run_ablation_study(
    base_config: BenchmarkConfig,
    ablations: list[AblationConfig],
    council_func,
    progress_callback=None
) -> dict[str, BenchmarkReport]:
    """Run ablation study comparing configurations"""
    reports = {}
    
    # Run baseline
    reports["baseline"] = await run_benchmark(base_config, council_func, progress_callback)
    
    # Run ablations
    for ablation in ablations:
        config = BenchmarkConfig(
            name=ablation.name,
            dataset_path=base_config.dataset_path,
            council_models=[m for m in base_config.council_models if m not in ablation.remove_models],
            chairman_model=ablation.alternative_chairman or base_config.chairman_model,
            skip_stage2=ablation.skip_stage2,
            max_questions=base_config.max_questions,
            timeout_per_question=base_config.timeout_per_question
        )
        
        if ablation.single_model_baseline:
            config.council_models = [ablation.single_model_baseline]
            config.skip_stage2 = True
        
        reports[ablation.name] = await run_benchmark(config, council_func, progress_callback)
    
    return reports


def save_benchmark_report(report: BenchmarkReport, output_path: str):
    """Save benchmark report to file"""
    output = {
        "config_name": report.config_name,
        "total_questions": report.total_questions,
        "correct": report.correct,
        "accuracy": report.accuracy,
        "avg_agreement": report.avg_agreement,
        "avg_time_ms": report.avg_time_ms,
        "total_cost": report.total_cost,
        "per_model_accuracy": report.per_model_accuracy,
        "results": [
            {
                "question_id": r.question_id,
                "question": r.question,
                "ground_truth": r.ground_truth,
                "council_answer": r.council_answer,
                "correct": r.correct,
                "agreement_score": r.agreement_score,
                "total_cost": r.total_cost,
                "total_time_ms": r.total_time_ms,
                "per_model_correct": r.per_model_correct
            }
            for r in report.results
        ]
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
