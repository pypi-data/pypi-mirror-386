#!/usr/bin/env python3
"""
Optimized Attack Data Ingestor for VictoriaLogs

This optimized version handles the existing attack_data directory efficiently,
with proper Git LFS detection and fallback parsing for various log formats.
"""

import os
import sys
import json
import yaml
import time
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import re
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_attack_data_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedAttackDataIngestor:
    """Optimized bulk ingestor for attack_data datasets into VictoriaLogs."""
    
    def __init__(self, 
                 victorialogs_url: str = "http://localhost:9428",
                 attack_data_path: str = "attack_data/attack_data",
                 batch_size: int = 1000,
                 max_workers: int = 4,
                 dry_run: bool = False):
        """Initialize the optimized attack data ingestor."""
        self.victorialogs_url = victorialogs_url.rstrip('/')
        self.attack_data_path = Path(attack_data_path)
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.dry_run = dry_run
        
        # Statistics
        self.stats = {
            'datasets_processed': 0,
            'log_files_processed': 0,
            'log_entries_ingested': 0,
            'lfs_files_skipped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OptimizedAttackDataIngestor/1.0'
        })
    
    def is_lfs_pointer(self, file_path: str) -> bool:
        """Check if a file is a Git LFS pointer."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                return first_line.startswith('version https://git-lfs.github.com/spec/v1')
        except:
            return False
    
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
                    
                    # Validate dataset files exist and are not LFS pointers
                    valid_datasets = []
                    for dataset in dataset_info.get('datasets', []):
                        dataset_path = self.attack_data_path / dataset['path'].lstrip('/')
                        if dataset_path.exists():
                            if self.is_lfs_pointer(str(dataset_path)):
                                logger.debug(f"Skipping LFS pointer file: {dataset_path}")
                                self.stats['lfs_files_skipped'] += 1
                                continue
                            dataset['full_path'] = str(dataset_path)
                            valid_datasets.append(dataset)
                        else:
                            logger.warning(f"Dataset file not found: {dataset_path}")
                    
                    dataset_info['datasets'] = valid_datasets
                    if valid_datasets:  # Only add datasets with valid files
                        datasets.append(dataset_info)
                    
            except Exception as e:
                logger.error(f"Error processing {yaml_file}: {e}")
                self.stats['errors'] += 1
        
        logger.info(f"Discovered {len(datasets)} datasets with {sum(len(d['datasets']) for d in datasets)} log files")
        return datasets
    
    def parse_xml_windows_event(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse XML Windows Event Log entries."""
        try:
            # Parse XML
            root = ET.fromstring(line)
            
            # Extract system information
            system = root.find('System')
            if system is None:
                return None
            
            # Get basic fields
            event_id = system.find('EventID')
            computer = system.find('Computer')
            time_created = system.find('TimeCreated')
            
            # Extract event data
            event_data = root.find('EventData')
            data_fields = {}
            if event_data is not None:
                for data in event_data.findall('Data'):
                    name = data.get('Name')
                    if name:
                        data_fields[name] = data.text
            
            return {
                'timestamp': time_created.get('SystemTime') if time_created is not None else datetime.now(timezone.utc).isoformat(),
                'event_id': event_id.text if event_id is not None else None,
                'computer': computer.text if computer is not None else None,
                'source': 'windows_event',
                'sourcetype': 'XmlWinEventLog',
                'raw_log': line,
                'log_type': 'windows_event',
                'event_data': data_fields
            }
        except Exception as e:
            logger.debug(f"Error parsing XML event: {e}")
            return None
    
    def parse_crowdstrike_falcon(self, line: str) -> Optional[Dict[str, Any]]:
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
                'source': 'crowdstrike',
                'sourcetype': 'crowdstrike:events:sensor',
                'raw_log': line,
                'log_type': 'crowdstrike_falcon',
                'json_data': data
            }
        except Exception as e:
            logger.debug(f"Error parsing CrowdStrike JSON: {e}")
            return None
    
    def parse_json_log(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse generic JSON logs."""
        try:
            data = json.loads(line)
            return {
                'timestamp': data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'source': 'json_log',
                'sourcetype': 'json',
                'raw_log': line,
                'log_type': 'json_generic',
                'json_data': data
            }
        except Exception as e:
            logger.debug(f"Error parsing JSON: {e}")
            return None
    
    def parse_syslog(self, line: str) -> Optional[Dict[str, Any]]:
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
                    'source': 'syslog',
                    'sourcetype': 'syslog',
                    'raw_log': line,
                    'log_type': 'syslog'
                }
        except Exception as e:
            logger.debug(f"Error parsing syslog: {e}")
            return None
    
    def parse_log_file(self, log_file_path: str, sourcetype: str, source: str) -> List[Dict[str, Any]]:
        """Parse a log file and convert to VictoriaLogs format."""
        log_entries = []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse based on sourcetype and content
                    parsed_entry = None
                    
                    if sourcetype == 'XmlWinEventLog':
                        parsed_entry = self.parse_xml_windows_event(line)
                    elif sourcetype == 'crowdstrike:events:sensor':
                        parsed_entry = self.parse_crowdstrike_falcon(line)
                    elif line.startswith('{') and line.endswith('}'):
                        # Try JSON parsing
                        parsed_entry = self.parse_json_log(line)
                    elif re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', line):
                        # Try syslog parsing
                        parsed_entry = self.parse_syslog(line)
                    else:
                        # Generic parsing
                        parsed_entry = {
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'source': source,
                            'sourcetype': sourcetype,
                            'raw_log': line,
                            'log_type': 'generic'
                        }
                    
                    if parsed_entry:
                        parsed_entry['_metadata'] = {
                            'file_path': log_file_path,
                            'line_number': line_num,
                            'sourcetype': sourcetype,
                            'source': source
                        }
                        log_entries.append(parsed_entry)
        
        except Exception as e:
            logger.error(f"Error parsing {log_file_path}: {e}")
            self.stats['errors'] += 1
        
        return log_entries
    
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
                logger.debug(f"Successfully sent batch of {len(batch)} entries")
                return True
            else:
                logger.error(f"Failed to send batch: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending batch to VictoriaLogs: {e}")
            return False
    
    def process_dataset(self, dataset_info: Dict[str, Any]) -> None:
        """Process a single dataset."""
        dataset_name = dataset_info.get('id', 'unknown')
        logger.info(f"Processing dataset: {dataset_name}")
        
        for dataset in dataset_info.get('datasets', []):
            log_file_path = dataset.get('full_path')
            sourcetype = dataset.get('sourcetype', 'unknown')
            source = dataset.get('source', 'unknown')
            
            if not log_file_path or not os.path.exists(log_file_path):
                logger.warning(f"Skipping missing file: {log_file_path}")
                continue
            
            logger.info(f"Processing log file: {os.path.basename(log_file_path)}")
            
            try:
                # Parse log file
                log_entries = self.parse_log_file(log_file_path, sourcetype, source)
                
                if not log_entries:
                    logger.warning(f"No entries parsed from {log_file_path}")
                    continue
                
                # Process in batches
                for i in range(0, len(log_entries), self.batch_size):
                    batch = log_entries[i:i + self.batch_size]
                    
                    # Add dataset metadata to each entry
                    for entry in batch:
                        entry['dataset_id'] = dataset_name
                        entry['dataset_description'] = dataset_info.get('description', '')
                        entry['mitre_technique'] = dataset_info.get('mitre_technique', [])
                        entry['author'] = dataset_info.get('author', '')
                        entry['date'] = dataset_info.get('date', '')
                        entry['environment'] = dataset_info.get('environment', '')
                    
                    # Send batch to VictoriaLogs
                    if self.send_batch_to_victorialogs(batch):
                        self.stats['log_entries_ingested'] += len(batch)
                    else:
                        self.stats['errors'] += 1
                
                self.stats['log_files_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing {log_file_path}: {e}")
                self.stats['errors'] += 1
    
    def ingest_all_datasets(self) -> None:
        """Ingest all discovered datasets."""
        logger.info("Starting optimized bulk ingestion of attack_data datasets...")
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
                future = executor.submit(self.process_dataset, dataset)
                futures.append(future)
            
            # Wait for completion and handle results
            for future in as_completed(futures):
                try:
                    future.result()
                    self.stats['datasets_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing dataset: {e}")
                    self.stats['errors'] += 1
        
        self.stats['end_time'] = datetime.now()
        self.print_statistics()
    
    def print_statistics(self) -> None:
        """Print ingestion statistics."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("=" * 60)
        logger.info("OPTIMIZED INGESTION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Datasets processed: {self.stats['datasets_processed']}")
        logger.info(f"Log files processed: {self.stats['log_files_processed']}")
        logger.info(f"Log entries ingested: {self.stats['log_entries_ingested']:,}")
        logger.info(f"LFS files skipped: {self.stats['lfs_files_skipped']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Total duration: {duration:.2f} seconds")
        
        if self.stats['log_entries_ingested'] > 0:
            rate = self.stats['log_entries_ingested'] / duration
            logger.info(f"Ingestion rate: {rate:.2f} entries/second")
        
        logger.info("=" * 60)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Optimized Attack Data Ingestor for VictoriaLogs')
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
    ingestor = OptimizedAttackDataIngestor(
        victorialogs_url=args.victorialogs_url,
        attack_data_path=args.attack_data_path,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        dry_run=args.dry_run
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
