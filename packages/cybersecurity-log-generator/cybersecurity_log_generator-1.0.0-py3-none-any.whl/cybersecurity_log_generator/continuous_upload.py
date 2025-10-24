#!/usr/bin/env python3
"""
Continuous Data Upload to VictoriaLogs
Uploads kaggle dataset logs to VictoriaLogs on a continuous basis
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ContinuousUploader:
    """Continuous uploader for kaggle datasets to VictoriaLogs"""
    
    def __init__(self, interval: int = 3600):
        self.interval = interval  # seconds between uploads
        self.logger = self._setup_logger()
        self.upload_history = self._load_upload_history()
        
    def _setup_logger(self):
        """Setup logging"""
        logger = logging.getLogger('continuous_uploader')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(logs_dir / "continuous_upload.log")
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
    
    def _load_upload_history(self) -> dict:
        """Load upload history"""
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
        return "continuous_upload.py"  # default
    
    def generate_kaggle_logs(self):
        """Generate logs for kaggle datasets using MCP tools"""
        try:
            # Import MCP tools
            from mcp_server.server import (
                generate_pillar_logs,
                generate_siem_priority_logs,
                generate_campaign_logs
            )
            
            total_logs = 0
            
            # Generate logs for different cybersecurity pillars
            pillars = [
                "network_security",
                "endpoint_security", 
                "cloud_security",
                "threat_intelligence",
                "authentication",
                "data_protection"
            ]
            
            for pillar in pillars:
                try:
                    self.logger.info(f"Generating logs for pillar: {pillar}")
                    
                    # Generate 200 logs per pillar
                    result = generate_pillar_logs(
                        pillar=pillar,
                        count=200,
                        time_range="24h",
                        ingest=True,
                        destination="victorialogs"
                    )
                    
                    if isinstance(result, str):
                        logs = json.loads(result)
                    else:
                        logs = result
                    
                    pillar_logs = len(logs.get('events', []))
                    total_logs += pillar_logs
                    self.logger.info(f"Generated {pillar_logs} logs for {pillar}")
                    
                    # Small delay between pillars
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error generating logs for {pillar}: {e}")
                    continue
            
            # Generate SIEM priority logs
            try:
                self.logger.info("Generating SIEM priority logs")
                result = generate_siem_priority_logs(
                    category="all",
                    count=500,
                    time_range="24h",
                    ingest=True,
                    destination="victorialogs"
                )
                
                if isinstance(result, str):
                    logs = json.loads(result)
                else:
                    logs = result
                
                siem_logs = len(logs.get('events', []))
                total_logs += siem_logs
                self.logger.info(f"Generated {siem_logs} SIEM priority logs")
                
            except Exception as e:
                self.logger.error(f"Error generating SIEM logs: {e}")
            
            return total_logs
            
        except Exception as e:
            self.logger.error(f"Error in generate_kaggle_logs: {e}")
            return 0
    
    def run_continuous_upload(self):
        """Run continuous upload"""
        self.logger.info(f"Starting continuous upload (interval: {self.interval}s)")
        
        # Check yesterday's script
        yesterday_script = self.get_yesterday_script()
        self.logger.info(f"Yesterday's upload script: {yesterday_script}")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"Starting upload cycle #{cycle_count}")
                start_time = time.time()
                
                # Generate and upload logs
                logs_generated = self.generate_kaggle_logs()
                
                # Save upload history
                self._save_upload_history("continuous_upload.py")
                
                cycle_time = time.time() - start_time
                self.logger.info(f"Cycle #{cycle_count} completed in {cycle_time:.2f}s. Generated {logs_generated} logs.")
                
                # Wait for next cycle
                self.logger.info(f"Waiting {self.interval}s until next upload...")
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                self.logger.info("Continuous upload stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous upload cycle #{cycle_count}: {e}")
                self.logger.info(f"Retrying in {self.interval}s...")
                time.sleep(self.interval)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Continuous upload to VictoriaLogs")
    parser.add_argument("--interval", type=int, default=3600, 
                       help="Interval between uploads in seconds (default: 3600 = 1 hour)")
    parser.add_argument("--start", action="store_true", 
                       help="Start continuous upload immediately")
    
    args = parser.parse_args()
    
    # Create uploader
    uploader = ContinuousUploader(interval=args.interval)
    
    if args.start:
        uploader.run_continuous_upload()
    else:
        print("Continuous Upload to VictoriaLogs")
        print("=" * 40)
        print(f"Interval: {args.interval} seconds ({args.interval/3600:.1f} hours)")
        print(f"Yesterday's script: {uploader.get_yesterday_script()}")
        print("\nTo start continuous upload, run:")
        print(f"python continuous_upload.py --start --interval {args.interval}")

if __name__ == "__main__":
    main()



