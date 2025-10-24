#!/usr/bin/env python3
"""
Test script for attack_data ingestor

This script tests the ingestor with a small subset of data to ensure
everything is working correctly before running a full ingestion.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import yaml
import json

def create_test_dataset():
    """Create a small test dataset for validation."""
    test_dir = Path("test_attack_data")
    test_dir.mkdir(exist_ok=True)
    
    # Create test dataset structure
    dataset_dir = test_dir / "datasets" / "attack_techniques" / "T1003.001" / "atomic_red_team"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test YAML file
    yaml_content = {
        'author': 'Test Author',
        'id': 'test-dataset-001',
        'date': '2025-10-16',
        'description': 'Test dataset for credential dumping simulation',
        'environment': 'test_environment',
        'directory': 'atomic_red_team',
        'mitre_technique': ['T1003.001'],
        'datasets': [
            {
                'name': 'test-windows-sysmon',
                'path': '/datasets/attack_techniques/T1003.001/atomic_red_team/test-windows-sysmon.log',
                'sourcetype': 'XmlWinEventLog',
                'source': 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'
            },
            {
                'name': 'test-crowdstrike',
                'path': '/datasets/attack_techniques/T1003.001/atomic_red_team/test-crowdstrike.log',
                'sourcetype': 'crowdstrike:events:sensor',
                'source': 'crowdstrike'
            }
        ]
    }
    
    with open(dataset_dir / "test_dataset.yml", 'w') as f:
        yaml.dump(yaml_content, f)
    
    # Create test log files
    sysmon_log = """<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
<System>
<Provider Name="Microsoft-Windows-Sysmon" Guid="{5770385f-c22a-43e6-b456-0eff9d4b5a2f}"/>
<EventID>1</EventID>
<Version>5</Version>
<Level>4</Level>
<Task>1</Task>
<Opcode>0</Opcode>
<Keywords>0x8000000000000000</Keywords>
<TimeCreated SystemTime="2025-10-16T21:00:00.0000000Z"/>
<EventRecordID>1</EventRecordID>
<Correlation/>
<Execution ProcessID="4" ThreadID="8"/>
<Channel>Microsoft-Windows-Sysmon/Operational</Channel>
<Computer>TEST-PC</Computer>
<Security UserID="S-1-5-18"/>
</System>
<EventData>
<Data Name="RuleName">-</Data>
<Data Name="UtcTime">2025-10-16 21:00:00.000</Data>
<Data Name="ProcessGuid">{12345678-1234-1234-1234-123456789abc}</Data>
<Data Name="ProcessId">1234</Data>
<Data Name="Image">C:\\Windows\\System32\\lsass.exe</Data>
<Data Name="FileVersion">10.0.19041.1</Data>
<Data Name="Description">Local Security Authority Process</Data>
<Data Name="Product">Microsoft® Windows® Operating System</Data>
<Data Name="Company">Microsoft Corporation</Data>
<Data Name="CommandLine">C:\\Windows\\system32\\lsass.exe</Data>
<Data Name="CurrentDirectory">C:\\Windows\\system32\\</Data>
<Data Name="User">NT AUTHORITY\\SYSTEM</Data>
<Data Name="LogonGuid">{87654321-4321-4321-4321-cba987654321}</Data>
<Data Name="LogonId">0x3e7</Data>
<Data Name="TerminalSessionId">0</Data>
<Data Name="IntegrityLevel">System</Data>
<Data Name="Hashes">SHA1=1234567890abcdef,SHA256=abcdef1234567890</Data>
<Data Name="ParentProcessGuid">{11111111-1111-1111-1111-111111111111}</Data>
<Data Name="ParentProcessId">1</Data>
<Data Name="ParentImage">C:\\Windows\\System32\\wininit.exe</Data>
<Data Name="ParentCommandLine">wininit.exe</Data>
</EventData>
</Event>"""
    
    with open(dataset_dir / "test-windows-sysmon.log", 'w') as f:
        f.write(sysmon_log)
    
    # Create test CrowdStrike log
    crowdstrike_log = {
        "timestamp": "2025-10-16T21:00:00.000Z",
        "event_type": "ProcessRollup2",
        "ComputerName": "TEST-PC",
        "UserName": "TEST\\Administrator",
        "ProcessName": "C:\\Windows\\System32\\lsass.exe",
        "CommandLine": "C:\\Windows\\system32\\lsass.exe",
        "ParentProcessName": "C:\\Windows\\System32\\wininit.exe",
        "ProcessId": 1234,
        "ParentProcessId": 1
    }
    
    with open(dataset_dir / "test-crowdstrike.log", 'w') as f:
        f.write(json.dumps(crowdstrike_log))
    
    print(f"✅ Created test dataset at: {test_dir}")
    return test_dir

def test_basic_ingestor():
    """Test the basic ingestor with test data."""
    print("🧪 Testing basic attack_data ingestor...")
    
    # Create test dataset
    test_dir = create_test_dataset()
    
    try:
        # Import and test the basic ingestor
        from attack_data_ingestor import AttackDataIngestor
        
        ingestor = AttackDataIngestor(
            victorialogs_url="http://localhost:9428",
            attack_data_path=str(test_dir),
            batch_size=10,
            max_workers=1,
            dry_run=True  # Don't actually send data
        )
        
        # Test dataset discovery
        datasets = ingestor.discover_datasets()
        print(f"📊 Discovered {len(datasets)} datasets")
        
        if datasets:
            dataset = datasets[0]
            print(f"📋 Dataset: {dataset.get('id', 'unknown')}")
            print(f"📁 Log files: {len(dataset.get('datasets', []))}")
            
            # Test log file parsing
            for log_file in dataset.get('datasets', []):
                file_path = log_file.get('full_path')
                if file_path and os.path.exists(file_path):
                    print(f"🔍 Testing log file: {os.path.basename(file_path)}")
                    
                    entries = ingestor.parse_log_file(
                        file_path,
                        log_file.get('sourcetype', 'unknown'),
                        log_file.get('source', 'unknown')
                    )
                    
                    print(f"   ✅ Parsed {len(entries)} entries")
                    
                    if entries:
                        entry = entries[0]
                        print(f"   📝 Sample entry: {entry.get('log_type', 'unknown')} - {entry.get('timestamp', 'no timestamp')}")
        
        print("✅ Basic ingestor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Basic ingestor test failed: {e}")
        return False
    
    finally:
        # Cleanup test data
        shutil.rmtree(test_dir, ignore_errors=True)

def test_advanced_ingestor():
    """Test the advanced ingestor with test data."""
    print("🧪 Testing advanced attack_data ingestor...")
    
    # Create test dataset
    test_dir = create_test_dataset()
    
    try:
        # Import and test the advanced ingestor
        from advanced_attack_data_ingestor import AdvancedAttackDataIngestor
        
        ingestor = AdvancedAttackDataIngestor(
            victorialogs_url="http://localhost:9428",
            attack_data_path=str(test_dir),
            batch_size=10,
            max_workers=1,
            dry_run=True  # Don't actually send data
        )
        
        # Test dataset discovery
        datasets = ingestor.discover_datasets()
        print(f"📊 Discovered {len(datasets)} datasets")
        
        if datasets:
            dataset = datasets[0]
            print(f"📋 Dataset: {dataset.get('id', 'unknown')}")
            print(f"📁 Log files: {len(dataset.get('datasets', []))}")
            
            # Test streaming log file processing
            for log_file in dataset.get('datasets', []):
                file_path = log_file.get('full_path')
                if file_path and os.path.exists(file_path):
                    print(f"🔍 Testing streaming log file: {os.path.basename(file_path)}")
                    
                    entry_count = 0
                    for entry in ingestor.process_log_file_streaming(
                        file_path,
                        log_file.get('sourcetype', 'unknown'),
                        log_file.get('source', 'unknown')
                    ):
                        entry_count += 1
                        if entry_count == 1:  # Show first entry
                            print(f"   📝 Sample entry: {entry.get('log_type', 'unknown')} - {entry.get('format', 'unknown')}")
                    
                    print(f"   ✅ Streamed {entry_count} entries")
        
        print("✅ Advanced ingestor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Advanced ingestor test failed: {e}")
        return False
    
    finally:
        # Cleanup test data
        shutil.rmtree(test_dir, ignore_errors=True)

def main():
    """Run all tests."""
    print("🚀 Starting attack_data ingestor tests...")
    print("=" * 60)
    
    # Test basic ingestor
    basic_success = test_basic_ingestor()
    print()
    
    # Test advanced ingestor
    advanced_success = test_advanced_ingestor()
    print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Basic Ingestor: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"Advanced Ingestor: {'✅ PASS' if advanced_success else '❌ FAIL'}")
    
    if basic_success and advanced_success:
        print("\n🎉 All tests passed! The ingestor is ready to use.")
        print("\n📋 Next steps:")
        print("1. Set up the attack_data repository: ./setup_attack_data.sh")
        print("2. Run a dry test: python attack_data_ingestor.py --dry-run")
        print("3. Start full ingestion: python advanced_attack_data_ingestor.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
