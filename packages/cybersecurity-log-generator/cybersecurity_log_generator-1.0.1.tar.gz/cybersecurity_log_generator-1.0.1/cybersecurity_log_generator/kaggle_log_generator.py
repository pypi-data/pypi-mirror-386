#!/usr/bin/env python3
"""
Kaggle Dataset Log Generator
Generates synthetic logs for all CSV files in the kaggle folder and uploads to VictoriaLogs
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

# Import MCP tools
from mcp_server.server import (
    generate_logs,
    generate_pillar_logs,
    generate_siem_priority_logs,
    generate_campaign_logs,
    generate_correlated_logs
)

class KaggleLogGenerator:
    """Generate logs for all kaggle CSV files and upload to VictoriaLogs"""
    
    def __init__(self, kaggle_dir: str = "../kaggle", continuous: bool = False, interval: int = 3600):
        self.kaggle_dir = Path(kaggle_dir)
        self.continuous = continuous
        self.interval = interval  # seconds between uploads
        self.logger = self._setup_logger()
        self.upload_history = self._load_upload_history()
        
    def _setup_logger(self):
        """Setup logging"""
        logger = logging.getLogger('kaggle_log_generator')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(logs_dir / "kaggle_log_generator.log")
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
        return "kaggle_log_generator.py"  # default
    
    def analyze_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a CSV file to determine log generation strategy"""
        try:
            # Read first few rows to understand structure
            df = pd.read_csv(file_path, nrows=5)
            
            analysis = {
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "columns": list(df.columns),
                "row_count": len(pd.read_csv(file_path)),
                "data_types": df.dtypes.to_dict(),
                "sample_data": df.head(2).to_dict('records')
            }
            
            # Determine log type based on file name and content
            if "attack" in file_path.name.lower():
                analysis["log_type"] = "ids"
                analysis["pillar"] = "network_security"
            elif "cloud" in file_path.name.lower() or "aws" in file_path.name.lower():
                analysis["log_type"] = "cloud_security"
                analysis["pillar"] = "cloud_security"
            elif "intrusion" in file_path.name.lower():
                analysis["log_type"] = "endpoint"
                analysis["pillar"] = "endpoint_security"
            elif "threat" in file_path.name.lower():
                analysis["log_type"] = "ids"
                analysis["pillar"] = "threat_intelligence"
            else:
                analysis["log_type"] = "ids"
                analysis["pillar"] = "network_security"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    def generate_logs_for_file(self, file_analysis: Dict[str, Any], count: int = 100) -> List[Dict]:
        """Generate logs for a specific file based on its analysis"""
        try:
            log_type = file_analysis["log_type"]
            pillar = file_analysis["pillar"]
            
            self.logger.info(f"Generating {count} {log_type} logs for {file_analysis['file_name']}")
            
            # Generate logs using the appropriate method
            if pillar in ["network_security", "endpoint_security", "cloud_security", "threat_intelligence"]:
                # Use pillar-based generation
                result = generate_pillar_logs(
                    pillar=pillar,
                    count=count,
                    time_range="24h",
                    ingest=True,
                    destination="victorialogs"
                )
            else:
                # Use standard log generation
                result = generate_logs(
                    log_type=log_type,
                    count=count,
                    time_range="24h",
                    ingest=True,
                    destination="victorialogs"
                )
            
            if isinstance(result, str):
                logs = json.loads(result)
            else:
                logs = result
            
            self.logger.info(f"Generated {len(logs.get('events', []))} logs for {file_analysis['file_name']}")
            return logs.get('events', [])
            
        except Exception as e:
            self.logger.error(f"Error generating logs for {file_analysis['file_name']}: {e}")
            return []
    
    def process_all_kaggle_files(self):
        """Process all CSV files in the kaggle directory"""
        csv_files = list(self.kaggle_dir.glob("*.csv"))
        
        if not csv_files:
            self.logger.warning(f"No CSV files found in {self.kaggle_dir}")
            return
        
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        
        total_logs_generated = 0
        
        for csv_file in csv_files:
            try:
                self.logger.info(f"Processing {csv_file.name}")
                
                # Analyze the file
                analysis = self.analyze_csv_file(csv_file)
                if not analysis:
                    continue
                
                # Generate logs based on file content
                # Use a portion of the actual row count for log generation
                log_count = min(analysis["row_count"] // 10, 1000)  # Generate up to 1000 logs per file
                if log_count < 10:
                    log_count = 10
                
                logs = self.generate_logs_for_file(analysis, log_count)
                total_logs_generated += len(logs)
                
                self.logger.info(f"Generated {len(logs)} logs for {csv_file.name}")
                
                # Small delay between files to avoid overwhelming VictoriaLogs
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error processing {csv_file.name}: {e}")
                continue
        
        self.logger.info(f"Total logs generated: {total_logs_generated}")
        return total_logs_generated
    
    def run_continuous_upload(self):
        """Run continuous upload with specified interval"""
        self.logger.info(f"Starting continuous upload mode (interval: {self.interval}s)")
        
        while True:
            try:
                self.logger.info("Starting upload cycle...")
                start_time = time.time()
                
                # Process all files
                logs_generated = self.process_all_kaggle_files()
                
                # Save upload history
                self._save_upload_history("kaggle_log_generator.py")
                
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
    
    def run_single_upload(self):
        """Run single upload"""
        self.logger.info("Starting single upload...")
        
        # Check yesterday's script
        yesterday_script = self.get_yesterday_script()
        self.logger.info(f"Yesterday's upload script: {yesterday_script}")
        
        # Process all files
        logs_generated = self.process_all_kaggle_files()
        
        # Save upload history
        self._save_upload_history("kaggle_log_generator.py")
        
        self.logger.info(f"Single upload completed. Generated {logs_generated} logs.")
        return logs_generated

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate logs for kaggle datasets and upload to VictoriaLogs")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous mode")
    parser.add_argument("--interval", type=int, default=3600, help="Interval between uploads in seconds (default: 3600)")
    parser.add_argument("--kaggle-dir", default="../kaggle", help="Path to kaggle directory (default: ../kaggle)")
    
    args = parser.parse_args()
    
    # Create generator
    generator = KaggleLogGenerator(
        kaggle_dir=args.kaggle_dir,
        continuous=args.continuous,
        interval=args.interval
    )
    
    if args.continuous:
        generator.run_continuous_upload()
    else:
        generator.run_single_upload()

if __name__ == "__main__":
    main()



