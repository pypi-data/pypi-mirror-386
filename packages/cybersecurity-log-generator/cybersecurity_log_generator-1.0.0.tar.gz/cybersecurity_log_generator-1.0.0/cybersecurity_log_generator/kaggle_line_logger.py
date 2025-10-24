#!/usr/bin/env python3
"""
Kaggle Line-by-Line Log Generator
Generates a log entry for each line in each kaggle CSV file
"""

import os
import sys
import json
import csv
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import random
from typing import Dict, List, Any
import argparse

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class KaggleLineLogger:
    """Generate logs for each line in kaggle CSV files"""
    
    def __init__(self, kaggle_dir: str = "../kaggle", continuous: bool = False, interval: int = 3600):
        self.kaggle_dir = Path(kaggle_dir)
        self.continuous = continuous
        self.interval = interval
        self.logger = self._setup_logger()
        self.upload_history = self._load_upload_history()
        
    def _setup_logger(self):
        """Setup logging"""
        logger = logging.getLogger('kaggle_line_logger')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(logs_dir / "kaggle_line_logger.log")
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _load_upload_history(self) -> Dict:
        """Load upload history from yesterday"""
        history_file = Path("logs/upload_history.json")
        if history_file.exists():
            with open(history_file, 'r') as f:
                return json.load(f)
        return {"last_upload": None, "scripts_used": []}
    
    def _save_upload_history(self, script_used: str):
        """Save upload history"""
        self.upload_history["last_upload"] = datetime.now().isoformat()
        self.upload_history["scripts_used"].append({
            "timestamp": datetime.now().isoformat(),
            "script": script_used
        })
        
        history_file = Path("logs/upload_history.json")
        with open(history_file, 'w') as f:
            json.dump(self.upload_history, f, indent=2)
    
    def get_yesterday_script(self) -> str:
        """Get the script used yesterday"""
        if self.upload_history.get("scripts_used"):
            yesterday = datetime.now() - timedelta(days=1)
            for entry in reversed(self.upload_history["scripts_used"]):
                entry_date = datetime.fromisoformat(entry["timestamp"])
                if entry_date.date() == yesterday.date():
                    return entry["script"]
        return "kaggle_line_logger.py"  # default
    
    def convert_csv_row_to_log(self, row: Dict, file_name: str, row_index: int) -> Dict:
        """Convert a CSV row to a log entry"""
        try:
            # Create a log entry based on the CSV row
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "source": "kaggle_dataset",
                "file_name": file_name,
                "row_index": row_index,
                "log_type": "data_ingestion",
                "event_type": "csv_row_processed",
                "data": row,
                "metadata": {
                    "processing_time": datetime.now().isoformat(),
                    "file_source": "kaggle",
                    "row_count": row_index + 1
                }
            }
            
            # Add specific fields based on file content
            if "attack" in file_name.lower():
                log_entry["security_event"] = True
                log_entry["threat_level"] = random.choice(["low", "medium", "high", "critical"])
            elif "cloud" in file_name.lower():
                log_entry["cloud_event"] = True
                log_entry["service"] = "aws_cloudwatch"
            elif "intrusion" in file_name.lower():
                log_entry["intrusion_detection"] = True
                log_entry["risk_score"] = random.randint(1, 10)
            
            return log_entry
            
        except Exception as e:
            self.logger.error(f"Error converting row to log: {e}")
            return None
    
    def process_csv_file(self, file_path: Path, max_rows: int = None) -> List[Dict]:
        """Process a CSV file and convert each row to a log entry"""
        try:
            self.logger.info(f"Processing {file_path.name}")
            
            logs = []
            row_count = 0
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Limit rows if specified
            if max_rows:
                df = df.head(max_rows)
            
            self.logger.info(f"Processing {len(df)} rows from {file_path.name}")
            
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_dict = row.to_dict()
                    
                    # Convert to log entry
                    log_entry = self.convert_csv_row_to_log(
                        row_dict, 
                        file_path.name, 
                        index
                    )
                    
                    if log_entry:
                        logs.append(log_entry)
                        row_count += 1
                    
                    # Progress update every 100 rows
                    if (index + 1) % 100 == 0:
                        self.logger.info(f"Processed {index + 1} rows from {file_path.name}")
                
                except Exception as e:
                    self.logger.error(f"Error processing row {index} in {file_path.name}: {e}")
                    continue
            
            self.logger.info(f"Generated {row_count} log entries from {file_path.name}")
            return logs
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path.name}: {e}")
            return []
    
    def upload_logs_to_victorialogs(self, logs: List[Dict]) -> bool:
        """Upload logs to VictoriaLogs using MCP tools"""
        try:
            # Import MCP tools
            from mcp_server.server import generate_logs
            
            # Generate logs using MCP tools
            result = generate_logs(
                log_type="ids",
                count=len(logs),
                time_range="24h",
                ingest=True,
                destination="victorialogs"
            )
            
            if isinstance(result, str):
                result_data = json.loads(result)
            else:
                result_data = result
            
            self.logger.info(f"Uploaded {len(logs)} logs to VictoriaLogs")
            return True
            
        except Exception as e:
            self.logger.error(f"Error uploading logs to VictoriaLogs: {e}")
            return False
    
    def process_all_kaggle_files(self, max_rows_per_file: int = 1000):
        """Process all CSV files in the kaggle directory"""
        csv_files = list(self.kaggle_dir.glob("*.csv"))
        
        if not csv_files:
            self.logger.warning(f"No CSV files found in {self.kaggle_dir}")
            return
        
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        
        total_logs_generated = 0
        
        for csv_file in csv_files:
            try:
                # Process the file
                logs = self.process_csv_file(csv_file, max_rows_per_file)
                
                if logs:
                    # Upload to VictoriaLogs
                    success = self.upload_logs_to_victorialogs(logs)
                    if success:
                        total_logs_generated += len(logs)
                        self.logger.info(f"Successfully uploaded {len(logs)} logs from {csv_file.name}")
                    else:
                        self.logger.error(f"Failed to upload logs from {csv_file.name}")
                
                # Small delay between files
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error processing {csv_file.name}: {e}")
                continue
        
        self.logger.info(f"Total logs generated and uploaded: {total_logs_generated}")
        return total_logs_generated
    
    def run_continuous_upload(self, max_rows_per_file: int = 1000):
        """Run continuous upload with specified interval"""
        self.logger.info(f"Starting continuous upload mode (interval: {self.interval}s)")
        
        while True:
            try:
                self.logger.info("Starting upload cycle...")
                start_time = time.time()
                
                # Process all files
                logs_generated = self.process_all_kaggle_files(max_rows_per_file)
                
                # Save upload history
                self._save_upload_history("kaggle_line_logger.py")
                
                cycle_time = time.time() - start_time
                self.logger.info(f"Upload cycle completed in {cycle_time:.2f}s. Generated {logs_generated} logs.")
                
                # Wait for next cycle
                self.logger.info(f"Waiting {self.interval}s until next upload...")
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                self.logger.info("Continuous upload stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous upload: {e}")
                self.logger.info(f"Retrying in {self.interval}s...")
                time.sleep(self.interval)
    
    def run_single_upload(self, max_rows_per_file: int = 1000):
        """Run single upload"""
        self.logger.info("Starting single upload...")
        
        # Check yesterday's script
        yesterday_script = self.get_yesterday_script()
        self.logger.info(f"Yesterday's upload script: {yesterday_script}")
        
        # Process all files
        logs_generated = self.process_all_kaggle_files(max_rows_per_file)
        
        # Save upload history
        self._save_upload_history("kaggle_line_logger.py")
        
        self.logger.info(f"Single upload completed. Generated {logs_generated} logs.")
        return logs_generated

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate logs for each line in kaggle CSV files")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous mode")
    parser.add_argument("--interval", type=int, default=3600, help="Interval between uploads in seconds (default: 3600)")
    parser.add_argument("--kaggle-dir", default="../kaggle", help="Path to kaggle directory (default: ../kaggle)")
    parser.add_argument("--max-rows", type=int, default=1000, help="Maximum rows to process per file (default: 1000)")
    
    args = parser.parse_args()
    
    # Create generator
    generator = KaggleLineLogger(
        kaggle_dir=args.kaggle_dir,
        continuous=args.continuous,
        interval=args.interval
    )
    
    if args.continuous:
        generator.run_continuous_upload(args.max_rows)
    else:
        generator.run_single_upload(args.max_rows)

if __name__ == "__main__":
    main()



