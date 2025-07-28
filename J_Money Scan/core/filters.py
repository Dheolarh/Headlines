class Filters:
    @staticmethod
    def by_status(signals, status):
        return [s for s in signals if s.get("status") == status]
    
    @staticmethod
    def by_strategy(signals, strategy):
        return [s for s in signals if s.get("strategy", "").upper() == strategy.upper()]
    
    @staticmethod
    def for_alert(signals):
        return [s for s in signals if s.get("alert") == "Send Alert"]
    
    @staticmethod
    def validate_signal_id(signals, existing_ids):
        return [s for s in signals if s["signal_id"] not in existing_ids]