#!/usr/bin/env python3
"""
Real-time monitoring script for Cybersecurity Log Generator
Monitors file changes, process activity, and log generation
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

class CybersecurityMonitor:
    def __init__(self, watch_dir="/Users/tredkar/Documents/GitHub/hd-syntheticdata/cybersecurity_log_generator"):
        self.watch_dir = Path(watch_dir)
        self.last_files = set()
        self.last_processes = set()
        self.start_time = datetime.now()
        
    def get_file_info(self):
        """Get information about JSON files in the directory"""
        files = {}
        for file_path in self.watch_dir.glob("*.json"):
            if file_path.is_file():
                stat = file_path.stat()
                files[str(file_path)] = {
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'events': self.count_events_in_file(file_path)
                }
        return files
    
    def count_events_in_file(self, file_path):
        """Count events in a JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'total_logs' in data:
                    return data['total_logs']
                elif 'events' in data:
                    return len(data['events'])
                else:
                    return 0
        except:
            return 0
    
    def get_processes(self):
        """Get running processes related to cybersecurity log generator"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = []
            for line in result.stdout.split('\n'):
                if any(keyword in line.lower() for keyword in ['cybersecurity', 'mcp', 'server.py', 'log_generator']):
                    processes.append(line.strip())
            return processes
        except:
            return []
    
    def print_header(self):
        """Print monitoring header"""
        print("🔍 Cybersecurity Log Generator - Real-time Monitor")
        print("=" * 60)
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Watching: {self.watch_dir}")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        print()
    
    def print_status(self):
        """Print current status"""
        current_time = datetime.now()
        uptime = current_time - self.start_time
        
        print(f"⏰ {current_time.strftime('%H:%M:%S')} (Uptime: {uptime})")
        
        # File status
        files = self.get_file_info()
        if files:
            print("📁 Files:")
            for file_path, info in files.items():
                filename = os.path.basename(file_path)
                size_mb = info['size'] / (1024 * 1024)
                events = info['events']
                print(f"   {filename}: {size_mb:.1f}MB, {events} events, modified: {info['modified'].strftime('%H:%M:%S')}")
        else:
            print("📁 No JSON files found")
        
        # Process status
        processes = self.get_processes()
        if processes:
            print("🔄 Processes:")
            for process in processes[:3]:  # Show first 3 processes
                parts = process.split()
                if len(parts) > 10:
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    cmd = ' '.join(parts[10:])
                    print(f"   PID {pid}: {cpu}% CPU, {mem}% MEM - {cmd[:50]}...")
        else:
            print("🔄 No cybersecurity processes found")
        
        print("-" * 60)
    
    def run(self, interval=5):
        """Run the monitor"""
        self.print_header()
        
        try:
            while True:
                self.print_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            print(f"📊 Total monitoring time: {datetime.now() - self.start_time}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        watch_dir = sys.argv[1]
    else:
        watch_dir = "/Users/tredkar/Documents/GitHub/hd-syntheticdata/cybersecurity_log_generator"
    
    monitor = CybersecurityMonitor(watch_dir)
    monitor.run()

if __name__ == "__main__":
    main()




