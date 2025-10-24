#!/usr/bin/env python3
"""
Master Upload Script for Kaggle Datasets to VictoriaLogs
Combines all upload functionality with continuous operation
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

class MasterUploader:
    """Master uploader that combines all upload methods"""
    
    def __init__(self, interval: int = 3600):
        self.interval = interval
        self.logger = self._setup_logger()
        self.upload_history = self._load_upload_history()
        
    def _setup_logger(self):
        """Setup logging"""
        logger = logging.getLogger('master_uploader')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(logs_dir / "master_upload.log")
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
        return "master_upload.py"  # default
    
    def run_comprehensive_upload(self):
        """Run comprehensive upload using all methods"""
        try:
            self.logger.info("Starting comprehensive upload...")
            
            # Import MCP tools
            from mcp_server.server import (
                generate_pillar_logs,
                generate_siem_priority_logs,
                generate_campaign_logs,
                generate_correlated_logs
            )
            
            total_logs = 0
            
            # 1. Generate logs for cybersecurity pillars
            self.logger.info("Generating logs for cybersecurity pillars...")
            pillars = [
                "network_security",
                "endpoint_security", 
                "cloud_security",
                "threat_intelligence",
                "authentication",
                "data_protection",
                "incident_response",
                "vulnerability_management"
            ]
            
            for pillar in pillars:
                try:
                    result = generate_pillar_logs(
                        pillar=pillar,
                        count=300,
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
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error generating logs for {pillar}: {e}")
                    continue
            
            # 2. Generate SIEM priority logs
            self.logger.info("Generating SIEM priority logs...")
            try:
                result = generate_siem_priority_logs(
                    category="all",
                    count=1000,
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
            
            # 3. Generate attack campaign logs
            self.logger.info("Generating attack campaign logs...")
            try:
                result = generate_campaign_logs(
                    threat_actor="APT29",
                    duration="24h",
                    target_count=200,
                    ingest=True
                )
                
                if isinstance(result, str):
                    logs = json.loads(result)
                else:
                    logs = result
                
                campaign_logs = len(logs.get('events', []))
                total_logs += campaign_logs
                self.logger.info(f"Generated {campaign_logs} attack campaign logs")
                
            except Exception as e:
                self.logger.error(f"Error generating campaign logs: {e}")
            
            # 4. Generate correlated logs
            self.logger.info("Generating correlated logs...")
            try:
                result = generate_correlated_logs(
                    log_types="authentication,network_security,endpoint_security",
                    count=500,
                    correlation_strength=0.8,
                    ingest=True
                )
                
                if isinstance(result, str):
                    logs = json.loads(result)
                else:
                    logs = result
                
                correlated_logs = len(logs.get('events', []))
                total_logs += correlated_logs
                self.logger.info(f"Generated {correlated_logs} correlated logs")
                
            except Exception as e:
                self.logger.error(f"Error generating correlated logs: {e}")
            
            return total_logs
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive upload: {e}")
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
                
                # Run comprehensive upload
                logs_generated = self.run_comprehensive_upload()
                
                # Save upload history
                self._save_upload_history("master_upload.py")
                
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
    
    def run_single_upload(self):
        """Run single upload"""
        self.logger.info("Starting single upload...")
        
        # Check yesterday's script
        yesterday_script = self.get_yesterday_script()
        self.logger.info(f"Yesterday's upload script: {yesterday_script}")
        
        # Run comprehensive upload
        logs_generated = self.run_comprehensive_upload()
        
        # Save upload history
        self._save_upload_history("master_upload.py")
        
        self.logger.info(f"Single upload completed. Generated {logs_generated} logs.")
        return logs_generated

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Master upload script for kaggle datasets to VictoriaLogs")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous mode")
    parser.add_argument("--interval", type=int, default=3600, 
                       help="Interval between uploads in seconds (default: 3600 = 1 hour)")
    parser.add_argument("--start", action="store_true", 
                       help="Start continuous upload immediately")
    
    args = parser.parse_args()
    
    # Create uploader
    uploader = MasterUploader(interval=args.interval)
    
    if args.continuous or args.start:
        uploader.run_continuous_upload()
    else:
        print("Master Upload Script for Kaggle Datasets to VictoriaLogs")
        print("=" * 60)
        print(f"Interval: {args.interval} seconds ({args.interval/3600:.1f} hours)")
        print(f"Yesterday's script: {uploader.get_yesterday_script()}")
        print("\nUpload Methods:")
        print("1. Cybersecurity pillar logs (8 pillars)")
        print("2. SIEM priority logs (all categories)")
        print("3. Attack campaign logs (APT29)")
        print("4. Correlated logs (authentication, network, endpoint)")
        print("\nTo start continuous upload, run:")
        print(f"python master_upload.py --continuous --interval {args.interval}")
        print("\nTo start single upload, run:")
        print("python master_upload.py")

if __name__ == "__main__":
    main()



