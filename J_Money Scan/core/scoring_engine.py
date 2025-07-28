import json
from utils.logger import logger

class ScoringEngine:
    """Evaluates trading signals based on thresholds."""
    def __init__(self, thresholds_file="config/thresholds.json"):
        """Initialize the scoring engine with thresholds."""
        with open(thresholds_file) as f:
            self.thresholds = json.load(f)
    
    def evaluate(self, signal):
        """Evaluate a signal and return its status and alert message."""
        try:
            if "error" in signal:
                return "INVALID", signal["error"]
            try:
                score = float(signal.get("score", 0))
                macro = float(signal.get("macro_score", 0))
            except (ValueError, TypeError):
                logger.error(f"Could not convert score/macro to float for signal: {signal.get('ticker')}")
                return "INVALID", "Invalid Score/Macro Format"
            logger.info(f"Evaluating signal '{signal.get('ticker')}': Score={score} (needs >={self.thresholds['min_valid_score']}), Macro={macro} (needs >={self.thresholds['min_valid_macro']})")
            if score >= self.thresholds["min_valid_score"] and macro >= self.thresholds["min_valid_macro"]:
                logger.info(f"Signal '{signal.get('ticker')}' PASSED. Status: VALID")
                return "VALID", "Send Alert"
            elif score >= self.thresholds["min_watch_score"]:
                logger.info(f"Signal '{signal.get('ticker')}' needs review. Status: NEEDS_REVIEW")
                return "NEEDS_REVIEW", "Needs Review"
            logger.info(f"Signal '{signal.get('ticker')}' FAILED. Status: INVALID (Low Score)")
            return "INVALID", "Low Score"
        except Exception as e:
            logger.error(f"Scoring error: {str(e)}", exc_info=True)
            return "INVALID", "Evaluation Error"