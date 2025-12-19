"""
Calibration tracking for LLM Council.
Tracks stated confidence vs actual accuracy over time.
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.schemas import CalibrationDataPoint, CalibrationCurve


class CalibrationTracker:
    """Tracks model calibration over time"""
    
    def __init__(self, db_path: str = "data/calibration.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    query_hash TEXT NOT NULL,
                    stated_confidence REAL NOT NULL,
                    prediction TEXT NOT NULL,
                    ground_truth TEXT,
                    correct INTEGER,
                    timestamp TEXT NOT NULL,
                    UNIQUE(model, query_hash)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model ON predictions(model)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_hash ON predictions(query_hash)
            """)
    
    def query_hash(self, query: str) -> str:
        return hashlib.sha256(query.encode()).hexdigest()[:16]
    
    def record_prediction(
        self,
        model: str,
        query: str,
        stated_confidence: float,
        prediction: str
    ):
        """Record a model's prediction and stated confidence"""
        qhash = self.query_hash(query)
        timestamp = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO predictions 
                (model, query_hash, stated_confidence, prediction, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (model, qhash, stated_confidence, prediction, timestamp))
    
    def record_outcome(self, query: str, ground_truth: str):
        """Record actual outcome for a query"""
        qhash = self.query_hash(query)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get all predictions for this query
            cursor = conn.execute("""
                SELECT id, prediction FROM predictions WHERE query_hash = ?
            """, (qhash,))
            
            for row in cursor.fetchall():
                pred_id, prediction = row
                # Simple correctness check (can be enhanced)
                correct = 1 if self._check_correctness(prediction, ground_truth) else 0
                conn.execute("""
                    UPDATE predictions 
                    SET ground_truth = ?, correct = ?
                    WHERE id = ?
                """, (ground_truth, correct, pred_id))
    
    def _check_correctness(self, prediction: str, ground_truth: str) -> bool:
        """Check if prediction matches ground truth"""
        pred_lower = prediction.lower().strip()
        truth_lower = ground_truth.lower().strip()
        
        # Exact match
        if pred_lower == truth_lower:
            return True
        
        # Contains match
        if truth_lower in pred_lower or pred_lower in truth_lower:
            return True
        
        # First word match (for single-word answers)
        pred_first = pred_lower.split()[0] if pred_lower else ""
        truth_first = truth_lower.split()[0] if truth_lower else ""
        if pred_first == truth_first and len(truth_first) > 2:
            return True
        
        return False
    
    def get_calibration_curve(self, model: str) -> CalibrationCurve:
        """Get calibration curve for a model"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT stated_confidence, correct
                FROM predictions
                WHERE model = ? AND correct IS NOT NULL
            """, (model,))
            
            rows = cursor.fetchall()
        
        if not rows:
            return CalibrationCurve(
                model=model,
                buckets={},
                total_predictions=0,
                brier_score=None
            )
        
        # Bucket predictions by confidence
        buckets = {f"{i/10:.1f}": {"correct": 0, "total": 0} for i in range(5, 11)}
        brier_sum = 0.0
        
        for confidence, correct in rows:
            # Find appropriate bucket
            bucket_key = f"{min(1.0, max(0.5, round(confidence, 1))):.1f}"
            if bucket_key in buckets:
                buckets[bucket_key]["total"] += 1
                if correct:
                    buckets[bucket_key]["correct"] += 1
            
            # Brier score component
            brier_sum += (confidence - correct) ** 2
        
        # Compute accuracy per bucket
        bucket_accuracies = {}
        for key, data in buckets.items():
            if data["total"] > 0:
                bucket_accuracies[key] = data["correct"] / data["total"]
        
        brier_score = brier_sum / len(rows) if rows else None
        
        return CalibrationCurve(
            model=model,
            buckets=bucket_accuracies,
            total_predictions=len(rows),
            brier_score=brier_score
        )
    
    def get_all_models_calibration(self) -> dict[str, CalibrationCurve]:
        """Get calibration curves for all models"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT model FROM predictions")
            models = [row[0] for row in cursor.fetchall()]
        
        return {model: self.get_calibration_curve(model) for model in models}
    
    def get_model_accuracy(self, model: str) -> Optional[float]:
        """Get overall accuracy for a model"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT AVG(correct) FROM predictions
                WHERE model = ? AND correct IS NOT NULL
            """, (model,))
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else None


# Global instance
_calibration_tracker: Optional[CalibrationTracker] = None


def get_calibration_tracker() -> CalibrationTracker:
    global _calibration_tracker
    if _calibration_tracker is None:
        _calibration_tracker = CalibrationTracker()
    return _calibration_tracker
