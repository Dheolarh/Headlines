import json
import csv
import os
from datetime import datetime
from utils.logger import logger
from utils.helpers import flatten_dict, parse_score_value, convert_macro_score

class SignalParser:
    """Parses and standardizes trading signal files."""
    def __init__(self, mapping_file="config/field_mappings.json"):
        """Initialize the parser with field mappings."""
        self.mappings = self.load_mappings(mapping_file)
        self.required_fields = ["ticker", "score", "macro_score", "direction"]

    def load_mappings(self, file_path):
        """Load field mappings from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def detect_file_type(self, record):
        """Detect the type of input file based on its fields."""
        asset_type_key = next((key for key in record if key.lower() == 'type'), None)
        if asset_type_key:
            asset_type = record[asset_type_key].lower()
            if asset_type in ['fx', 'commodity']:
                return 'fx_comm'
            elif asset_type in ['stock', 'index', 'crypto']:
                return 'stocks'
        if 'signal_type' in record:
            return 'clean_signal'
        return 'default'

    def parse_file(self, file_path):
        """Parse a JSON or CSV file and return a list of processed signals."""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = [row for row in reader]
            else:
                logger.error(f"Unsupported file type: {file_path}")
                return []
            processed_signals = []
            for record in data:
                record_lower = {k.lower(): v for k, v in record.items()}
                flat_record = flatten_dict(record_lower)
                file_type = self.detect_file_type(flat_record)
                processed_signal = self.process_record(flat_record, file_type)
                if "error" not in processed_signal:
                    processed_signals.append(processed_signal)
            return processed_signals
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}", exc_info=True)
            return []

    def process_record(self, record, file_type):
        """Standardize a single record using field mappings and check required fields."""
        standardized = {}
        mapping = {k.lower(): v for k, v in self.mappings.get(file_type, self.mappings['default']).items()}
        for std_field, source_fields in mapping.items():
            for src_field in source_fields:
                if src_field.lower() in record:
                    value = record[src_field.lower()]
                    if "score" in std_field:
                        value = parse_score_value(value)
                    elif "macro" in std_field:
                        value = convert_macro_score(value)
                    standardized[std_field] = value
                    break
        missing_fields = [f for f in self.required_fields if f not in standardized]
        if missing_fields:
            logger.warning(f"Record missing required fields: {missing_fields}. Record: {record}")
            standardized["error"] = f"Missing required fields: {', '.join(missing_fields)}"
            return standardized
        ticker = standardized.get("ticker", "UNKNOWN")
        entry = standardized.get("entry_zone", "")
        direction = standardized.get("direction", "")
        standardized["signal_id"] = f"{ticker}-{entry}-{direction}-{int(datetime.now().timestamp())}"
        return standardized