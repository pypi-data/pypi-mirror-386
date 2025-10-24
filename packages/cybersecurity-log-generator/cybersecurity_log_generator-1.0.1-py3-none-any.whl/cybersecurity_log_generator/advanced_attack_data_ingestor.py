#!/usr/bin/env python3
"""
Advanced Bulk Attack Data Ingestor for VictoriaLogs

This advanced version handles Git LFS files, provides better performance,
and includes comprehensive monitoring and error handling.

Features:
- Git LFS file handling
- Streaming processing for large files
- Advanced log parsing with format detection
- Real-time progress monitoring
- Comprehensive error handling and recovery
- Performance metrics and optimization
- Configurable parsing rules
"""

import os
import sys
import json
import yaml
import time
import uuid
import logging
import argparse
import requests
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple, Iterator
import re
import gc
import psutil
from queue import Queue, Empty
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_attack_data_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor performance metrics during ingestion."""
    
    def __init__(self):
        self.start_time = time.time()
        self.processed_entries = 0
        self.processed_files = 0
        self.errors = 0
        self.last_report_time = time.time()
        self.report_interval = 10  # seconds
        
    def update(self, entries: int = 0, files: int = 0, errors: int = 0):
        """Update performance metrics."""
        self.processed_entries += entries
        self.processed_files += files
        self.errors += errors
        
        current_time = time.time()
        if current_time - self.last_report_time >= self.report_interval:
            self.report_progress()
            self.last_report_time = current_time
    
    def report_progress(self):
        """Report current progress and performance metrics."""
        elapsed = time.time() - self.start_time
        rate = self.processed_entries / elapsed if elapsed > 0 else 0
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        logger.info(f"Progress: {self.processed_entries:,} entries, {self.processed_files} files, "
                   f"{self.errors} errors | Rate: {rate:.1f} entries/sec | "
                   f"Memory: {memory.percent:.1f}% | CPU: {cpu:.1f}%")
    
    def get_final_stats(self) -> Dict[str, Any]:
        """Get final performance statistics."""
        elapsed = time.time() - self.start_time
        return {
            'total_entries': self.processed_entries,
            'total_files': self.processed_files,
            'total_errors': self.errors,
            'elapsed_time': elapsed,
            'avg_rate': self.processed_entries / elapsed if elapsed > 0 else 0
        }

class GitLFSHandler:
    """Handle Git LFS files."""
    
    @staticmethod
    def is_lfs_file(file_path: str) -> bool:
        """Check if a file is a Git LFS pointer."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                return first_line.startswith('version https://git-lfs.github.com/spec/v1')
        except:
            return False
    
    @staticmethod
    def get_lfs_file_info(file_path: str) -> Optional[Dict[str, str]]:
        """Extract LFS file information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            info = {}
            for line in lines:
                if line.startswith('oid sha256:'):
                    info['oid'] = line.split(':', 1)[1].strip()
                elif line.startswith('size '):
                    info['size'] = line.split(' ', 1)[1].strip()
            
            return info if info else None
        except:
            return None
    
    @staticmethod
    def download_lfs_file(file_path: str) -> bool:
        """Download the actual LFS file content."""
        try:
            # Use git lfs pull to download the file
            result = subprocess.run(
                ['git', 'lfs', 'pull', '--include', file_path],
                cwd=os.path.dirname(file_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Downloaded LFS file: {file_path}")
                return True
            else:
                logger.error(f"Failed to download LFS file {file_path}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error downloading LFS file {file_path}: {e}")
            return False

class AdvancedLogParser:
    """Advanced log parser with format detection."""
    
    def __init__(self):
        self.parsers = {
            'xml_windows_event': self._parse_xml_windows_event,
            'json_crowdstrike': self._parse_json_crowdstrike,
            'json_generic': self._parse_json_generic,
            'syslog': self._parse_syslog,
            'csv': self._parse_csv,
            'generic': self._parse_generic
        }
    
    def detect_format(self, line: str, sourcetype: str) -> str:
        """Detect log format based on content and sourcetype."""
        line = line.strip()
        
        if not line:
            return 'generic'
        
        # Check for XML format
        if line.startswith('<') and '>' in line:
            return 'xml_windows_event'
        
        # Check for JSON format
        if line.startswith('{') and line.endswith('}'):
            return 'json_crowdstrike' if 'crowdstrike' in sourcetype.lower() else 'json_generic'
        
        # Check for syslog format
        if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', line):
            return 'syslog'
        
        # Check for CSV format
        if ',' in line and line.count(',') > 2:
            return 'csv'
        
        return 'generic'
    
    def parse_line(self, line: str, sourcetype: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line."""
        format_type = self.detect_format(line, sourcetype)
        parser = self.parsers.get(format_type, self._parse_generic)
        
        try:
            return parser(line, sourcetype, source)
        except Exception as e:
            logger.debug(f"Error parsing line with {format_type} parser: {e}")
            return self._parse_generic(line, sourcetype, source)
    
    def _parse_xml_windows_event(self, line: str, sourcetype: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse XML Windows Event Log entries."""
        try:
            # Extract key fields from XML
            timestamp_match = re.search(r'<TimeCreated SystemTime="([^"]+)"', line)
            event_id_match = re.search(r'<EventID>(\d+)</EventID>', line)
            computer_match = re.search(r'<Computer>([^<]+)</Computer>', line)
            user_match = re.search(r'<Data Name="TargetUserName">([^<]+)</Data>', line)
            process_match = re.search(r'<Data Name="ProcessName">([^<]+)</Data>', line)
            
            timestamp = timestamp_match.group(1) if timestamp_match else datetime.now(timezone.utc).isoformat()
            
            return {
                'timestamp': timestamp,
                'event_id': event_id_match.group(1) if event_id_match else None,
                'computer': computer_match.group(1) if computer_match else None,
                'user': user_match.group(1) if user_match else None,
                'process': process_match.group(1) if process_match else None,
                'source': source,
                'sourcetype': sourcetype,
                'raw_log': line,
                'log_type': 'windows_event',
                'format': 'xml_windows_event'
            }
        except Exception as e:
            logger.debug(f"Error parsing XML event: {e}")
            return None
    
    def _parse_json_crowdstrike(self, line: str, sourcetype: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse CrowdStrike Falcon JSON logs."""
        try:
            data = json.loads(line)
            return {
                'timestamp': data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'event_type': data.get('event_type'),
                'computer_name': data.get('ComputerName'),
                'user_name': data.get('UserName'),
                'process_name': data.get('ProcessName'),
                'command_line': data.get('CommandLine'),
                'parent_process': data.get('ParentProcessName'),
                'source': source,
                'sourcetype': sourcetype,
                'raw_log': line,
                'log_type': 'crowdstrike_falcon',
                'format': 'json_crowdstrike'
            }
        except Exception as e:
            logger.debug(f"Error parsing CrowdStrike JSON: {e}")
            return None
    
    def _parse_json_generic(self, line: str, sourcetype: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse generic JSON logs."""
        try:
            data = json.loads(line)
            return {
                'timestamp': data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'source': source,
                'sourcetype': sourcetype,
                'raw_log': line,
                'log_type': 'json_generic',
                'format': 'json_generic',
                'json_data': data
            }
        except Exception as e:
            logger.debug(f"Error parsing generic JSON: {e}")
            return None
    
    def _parse_syslog(self, line: str, sourcetype: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse syslog format logs."""
        try:
            # Basic syslog parsing
            parts = line.split(' ', 5)
            if len(parts) >= 6:
                timestamp = f"{parts[0]} {parts[1]}"
                hostname = parts[2]
                program = parts[3]
                pid = parts[4].strip('[]')
                message = parts[5]
                
                return {
                    'timestamp': timestamp,
                    'hostname': hostname,
                    'program': program,
                    'pid': pid,
                    'message': message,
                    'source': source,
                    'sourcetype': sourcetype,
                    'raw_log': line,
                    'log_type': 'syslog',
                    'format': 'syslog'
                }
        except Exception as e:
            logger.debug(f"Error parsing syslog: {e}")
            return None
    
    def _parse_csv(self, line: str, sourcetype: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse CSV format logs."""
        try:
            parts = line.split(',')
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'csv_fields': parts,
                'source': source,
                'sourcetype': sourcetype,
                'raw_log': line,
                'log_type': 'csv',
                'format': 'csv'
            }
        except Exception as e:
            logger.debug(f"Error parsing CSV: {e}")
            return None
    
    def _parse_generic(self, line: str, sourcetype: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse generic log format."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': source,
            'sourcetype': sourcetype,
            'raw_log': line,
            'log_type': 'generic',
            'format': 'generic'
        }

class AdvancedAttackDataIngestor:
    """Advanced bulk ingestor for attack_data datasets into VictoriaLogs."""
    
    def __init__(self, 
                 victorialogs_url: str = "http://localhost:9428",
                 attack_data_path: str = "attack_data/attack_data",
                 batch_size: int = 1000,
                 max_workers: int = 4,
                 dry_run: bool = False,
                 config_file: str = None):
        """Initialize the advanced attack data ingestor."""
        self.victorialogs_url = victorialogs_url.rstrip('/')
        self.attack_data_path = Path(attack_data_path)
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.dry_run = dry_run
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize components
        self.parser = AdvancedLogParser()
        self.monitor = PerformanceMonitor()
        self.lfs_handler = GitLFSHandler()
        
        # Statistics
        self.stats = {
            'datasets_processed': 0,
            'log_files_processed': 0,
            'log_entries_ingested': 0,
            'lfs_files_downloaded': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Thread-safe queue for batching
        self.batch_queue = Queue()
        self.session = requests.Session()
        
        # Configure session for optimal performance
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AdvancedAttackDataIngestor/2.0'
        })
        
        # Connection pool for better performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers,
            pool_maxsize=max_workers * 2,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self.shutdown_requested = False
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file."""
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Error loading config file {config_file}: {e}")
        
        # Return default configuration
        return {
            'victorialogs': {'url': self.victorialogs_url, 'batch_size': self.batch_size},
            'processing': {'max_workers': self.max_workers},
            'monitoring': {'log_level': 'INFO'}
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received, finishing current batches...")
        self.shutdown_requested = True
    
    def discover_datasets(self) -> List[Dict[str, Any]]:
        """Discover all datasets in the attack_data directory."""
        logger.info("Discovering datasets...")
        datasets = []
        
        # Find all YAML files that describe datasets
        yaml_files = list(self.attack_data_path.rglob("*.yml")) + list(self.attack_data_path.rglob("*.yaml"))
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    dataset_info = yaml.safe_load(f)
                
                if dataset_info and 'datasets' in dataset_info:
                    # Add metadata
                    dataset_info['yaml_file'] = str(yaml_file)
                    dataset_info['dataset_path'] = str(yaml_file.parent)
                    
                    # Validate dataset files exist
                    valid_datasets = []
                    for dataset in dataset_info.get('datasets', []):
                        dataset_path = self.attack_data_path / dataset['path'].lstrip('/')
                        if dataset_path.exists():
                            dataset['full_path'] = str(dataset_path)
                            valid_datasets.append(dataset)
                        else:
                            logger.warning(f"Dataset file not found: {dataset_path}")
                    
                    dataset_info['datasets'] = valid_datasets
                    datasets.append(dataset_info)
                    
            except Exception as e:
                logger.error(f"Error processing {yaml_file}: {e}")
                self.stats['errors'] += 1
        
        logger.info(f"Discovered {len(datasets)} datasets with {sum(len(d['datasets']) for d in datasets)} log files")
        return datasets
    
    def process_log_file_streaming(self, log_file_path: str, sourcetype: str, source: str) -> Iterator[Dict[str, Any]]:
        """Process a log file using streaming to handle large files."""
        try:
            # Check if it's an LFS file
            if self.lfs_handler.is_lfs_file(log_file_path):
                logger.info(f"LFS file detected: {log_file_path}")
                if not self.lfs_handler.download_lfs_file(log_file_path):
                    logger.error(f"Failed to download LFS file: {log_file_path}")
                    return
            
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if self.shutdown_requested:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    parsed_entry = self.parser.parse_line(line, sourcetype, source)
                    if parsed_entry:
                        parsed_entry['_metadata'] = {
                            'file_path': log_file_path,
                            'line_number': line_num,
                            'sourcetype': sourcetype,
                            'source': source
                        }
                        yield parsed_entry
                        
        except Exception as e:
            logger.error(f"Error processing {log_file_path}: {e}")
            self.stats['errors'] += 1
    
    def send_batch_to_victorialogs(self, batch: List[Dict[str, Any]]) -> bool:
        """Send a batch of log entries to VictoriaLogs."""
        if self.dry_run:
            logger.debug(f"DRY RUN: Would send {len(batch)} entries to VictoriaLogs")
            return True
        
        try:
            # Prepare data for VictoriaLogs
            victorialogs_data = []
            for entry in batch:
                # Convert to VictoriaLogs format
                vl_entry = {
                    'timestamp': entry.get('timestamp', datetime.now(timezone.utc).isoformat()),
                    'message': entry.get('raw_log', ''),
                    'source': entry.get('source', 'unknown'),
                    'sourcetype': entry.get('sourcetype', 'unknown'),
                    'log_type': entry.get('log_type', 'unknown'),
                    'format': entry.get('format', 'unknown'),
                    'metadata': entry.get('_metadata', {}),
                    'fields': {k: v for k, v in entry.items() 
                             if k not in ['timestamp', 'raw_log', '_metadata'] and v is not None}
                }
                victorialogs_data.append(vl_entry)
            
            # Send to VictoriaLogs
            response = self.session.post(
                f"{self.victorialogs_url}/insert/jsonline",
                json=victorialogs_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to send batch: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending batch to VictoriaLogs: {e}")
            return False
    
    def process_dataset(self, dataset_info: Dict[str, Any]) -> None:
        """Process a single dataset with streaming."""
        dataset_name = dataset_info.get('id', 'unknown')
        logger.info(f"Processing dataset: {dataset_name}")
        
        for dataset in dataset_info.get('datasets', []):
            if self.shutdown_requested:
                break
                
            log_file_path = dataset.get('full_path')
            sourcetype = dataset.get('sourcetype', 'unknown')
            source = dataset.get('source', 'unknown')
            
            if not log_file_path or not os.path.exists(log_file_path):
                logger.warning(f"Skipping missing file: {log_file_path}")
                continue
            
            logger.info(f"Processing log file: {os.path.basename(log_file_path)}")
            
            try:
                # Process file in streaming mode
                batch = []
                for entry in self.process_log_file_streaming(log_file_path, sourcetype, source):
                    if self.shutdown_requested:
                        break
                    
                    # Add dataset metadata to each entry
                    entry['dataset_id'] = dataset_name
                    entry['dataset_description'] = dataset_info.get('description', '')
                    entry['mitre_technique'] = dataset_info.get('mitre_technique', [])
                    entry['author'] = dataset_info.get('author', '')
                    entry['date'] = dataset_info.get('date', '')
                    entry['environment'] = dataset_info.get('environment', '')
                    
                    batch.append(entry)
                    
                    # Send batch when it reaches the configured size
                    if len(batch) >= self.batch_size:
                        if self.send_batch_to_victorialogs(batch):
                            self.stats['log_entries_ingested'] += len(batch)
                            self.monitor.update(entries=len(batch))
                        else:
                            self.stats['errors'] += 1
                            self.monitor.update(errors=1)
                        
                        batch = []
                        
                        # Force garbage collection periodically
                        if self.stats['log_entries_ingested'] % 10000 == 0:
                            gc.collect()
                
                # Send remaining entries in the batch
                if batch and not self.shutdown_requested:
                    if self.send_batch_to_victorialogs(batch):
                        self.stats['log_entries_ingested'] += len(batch)
                        self.monitor.update(entries=len(batch))
                    else:
                        self.stats['errors'] += 1
                        self.monitor.update(errors=1)
                
                self.stats['log_files_processed'] += 1
                self.monitor.update(files=1)
                
            except Exception as e:
                logger.error(f"Error processing {log_file_path}: {e}")
                self.stats['errors'] += 1
                self.monitor.update(errors=1)
    
    def ingest_all_datasets(self) -> None:
        """Ingest all discovered datasets."""
        logger.info("Starting advanced bulk ingestion of attack_data datasets...")
        self.stats['start_time'] = datetime.now()
        
        # Discover all datasets
        datasets = self.discover_datasets()
        
        if not datasets:
            logger.warning("No datasets found to ingest")
            return
        
        logger.info(f"Found {len(datasets)} datasets to process")
        
        # Process datasets in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for dataset in datasets:
                if self.shutdown_requested:
                    break
                future = executor.submit(self.process_dataset, dataset)
                futures.append(future)
            
            # Wait for completion and handle results
            for future in as_completed(futures):
                if self.shutdown_requested:
                    break
                try:
                    future.result()
                    self.stats['datasets_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing dataset: {e}")
                    self.stats['errors'] += 1
        
        self.stats['end_time'] = datetime.now()
        self.print_statistics()
    
    def print_statistics(self) -> None:
        """Print comprehensive ingestion statistics."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        final_stats = self.monitor.get_final_stats()
        
        logger.info("=" * 80)
        logger.info("ADVANCED INGESTION COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Datasets processed: {self.stats['datasets_processed']}")
        logger.info(f"Log files processed: {self.stats['log_files_processed']}")
        logger.info(f"Log entries ingested: {self.stats['log_entries_ingested']:,}")
        logger.info(f"LFS files downloaded: {self.stats['lfs_files_downloaded']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Total duration: {duration:.2f} seconds")
        
        if self.stats['log_entries_ingested'] > 0:
            rate = self.stats['log_entries_ingested'] / duration
            logger.info(f"Average ingestion rate: {rate:.2f} entries/second")
            logger.info(f"Peak ingestion rate: {final_stats['avg_rate']:.2f} entries/second")
        
        # Memory usage
        memory = psutil.virtual_memory()
        logger.info(f"Final memory usage: {memory.percent:.1f}%")
        
        logger.info("=" * 80)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Advanced Bulk Attack Data Ingestor for VictoriaLogs')
    parser.add_argument('--victorialogs-url', default='http://localhost:9428',
                       help='VictoriaLogs endpoint URL (default: http://localhost:9428)')
    parser.add_argument('--attack-data-path', default='attack_data/attack_data',
                       help='Path to attack_data directory (default: attack_data/attack_data)')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Number of log entries per batch (default: 1000)')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform a dry run without actually sending data')
    parser.add_argument('--config', type=str,
                       help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate paths
    if not os.path.exists(args.attack_data_path):
        logger.error(f"Attack data path not found: {args.attack_data_path}")
        sys.exit(1)
    
    # Test VictoriaLogs connection
    if not args.dry_run:
        try:
            response = requests.get(f"{args.victorialogs_url}/api/v1/status", timeout=5)
            if response.status_code != 200:
                logger.error(f"VictoriaLogs not accessible at {args.victorialogs_url}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Cannot connect to VictoriaLogs at {args.victorialogs_url}: {e}")
            sys.exit(1)
    
    # Create and run ingestor
    ingestor = AdvancedAttackDataIngestor(
        victorialogs_url=args.victorialogs_url,
        attack_data_path=args.attack_data_path,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        dry_run=args.dry_run,
        config_file=args.config
    )
    
    try:
        ingestor.ingest_all_datasets()
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
