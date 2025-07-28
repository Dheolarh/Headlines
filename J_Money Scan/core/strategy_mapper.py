import json
from utils.logger import logger

class StrategyMapper:
    """Applies strategy configuration to trading signals."""
    def __init__(self, config_file="config/strategy_config.json"):
        """Initialize the strategy mapper with configuration."""
        with open(config_file) as f:
            self.config = json.load(f)
    
    def apply_strategy(self, signal):
        """Apply strategy configuration and calculate risk/reward if possible."""
        try:
            strategy = signal.get("strategy", "DEFAULT").upper()
            strategy_conf = self.config.get(strategy, self.config["DEFAULT"])
            signal["risk_multiplier"] = strategy_conf["risk_multiplier"]
            signal["tp_strategy"] = strategy_conf["tp_strategy"]
            if "entry_zone" in signal and "stop_loss" in signal and "tp1" in signal:
                try:
                    entry = sum(signal["entry_zone"])/2 if isinstance(signal["entry_zone"], list) else float(signal["entry_zone"])
                    stop = float(signal["stop_loss"])
                    tp1 = float(signal["tp1"])
                    signal["risk_reward"] = round((tp1 - entry) / (entry - stop), 1)
                except:
                    signal["risk_reward"] = "N/A"
            return signal
        except Exception as e:
            logger.error(f"Strategy error: {str(e)}")
            return signal