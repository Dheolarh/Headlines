import json
import re

def flatten_dict(d, parent_key='', sep='.'):
    """Flatten a nested dictionary."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

def parse_score_value(value):
    """Parse a score value from string or numeric input."""
    if isinstance(value, str):
        if '/' in value:
            return float(value.split('/')[0])
        elif re.match(r"^[A-Za-z]+$", value):
            return {"high": 9.0, "medium": 7.0, "low": 5.0}.get(value.lower(), 0.0)
    try:
        return float(value)
    except:
        return 0.0

def convert_macro_score(value):
    """Convert macro score from string or numeric input to float."""
    if value == "+1": return 10.0
    if value == "0": return 5.0
    if value == "-1": return 0.0
    try:
        return float(value)
    except:
        return 0.0

def format_signal_message(signal):
    """Format a signal as a structured Telegram message."""
    ticker = signal.get('ticker', 'N/A')
    strategy = signal.get('strategy', 'N/A')
    status = signal.get('status', 'N/A')
    signal_id = signal.get('signal_id', 'N/A')[:8]
    parts = [f"<b>{ticker}</b>  |  <b>{strategy}</b>"]
    metrics = [
        ('Status', 'status', ''),
        ('Confidence', 'score', '/10'),
        ('Macro Score', 'macro_score', '/10'),
        ('Entry Zone', 'entry_zone', ''),
        ('Stop Loss', 'stop_loss', ''),
        ('TP1', 'tp1', ''),
        ('TP2', 'tp2', ''),
        ('Risk/Reward', 'risk_reward', 'R'),
    ]
    for label, key, suffix in metrics:
        if key in signal and signal[key] != "":
            value = signal[key]
            parts.append(f"<b>{label}</b>:  {value}{suffix}")
    parts.append(f"<b>ID</b>:  {signal_id}")
    return "\n".join(parts)