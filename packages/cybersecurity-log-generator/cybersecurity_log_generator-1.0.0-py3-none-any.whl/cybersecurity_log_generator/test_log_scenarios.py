#!/usr/bin/env python3
"""
Specialized Test Script for Log Generation Scenarios
Tests specific cybersecurity scenarios and attack patterns.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import traceback

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.generator import LogGenerator
    from core.models import (
        LogType, ThreatActor, LogSeverity, AttackTactic, 
        NetworkTopology, SecurityEvent
    )
    print("✓ Imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class LogScenarioTester:
    """Specialized tester for cybersecurity log scenarios."""
    
    def __init__(self):
        self.generator = LogGenerator()
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    └─ {details}")
        self.test_results.append((test_name, passed, details))
    
    def test_apt29_attack_scenario(self) -> bool:
        """Test APT29 (Cozy Bear) attack scenario."""
        print("\n🔍 Testing APT29 Attack Scenario")
        print("-" * 40)
        
        try:
            # Generate APT29 campaign
            campaign = self.generator.generate_security_campaign(
                threat_actor=ThreatActor.APT29,
                duration="24h",
                target_count=200
            )
            
            # Verify campaign characteristics
            if campaign.threat_actor != ThreatActor.APT29:
                self.log_test("APT29 Threat Actor Attribution", False, f"Expected APT29, got {campaign.threat_actor}")
                return False
            
            # Check attack stages
            expected_stages = ["initial_access", "persistence", "exfiltration"]
            if not all(stage in campaign.attack_stages for stage in expected_stages):
                self.log_test("APT29 Attack Stages", False, f"Missing expected stages: {expected_stages}")
                return False
            
            # Analyze events by type
            event_types = {}
            for event in campaign.events:
                event_type = event.log_type.value
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            print(f"Event distribution: {event_types}")
            
            # Check for high-severity events
            high_severity = [e for e in campaign.events if e.severity in [LogSeverity.HIGH, LogSeverity.CRITICAL]]
            if len(high_severity) == 0:
                self.log_test("APT29 High Severity Events", False, "No high-severity events found")
                return False
            
            self.log_test("APT29 Campaign Generation", True, f"{len(campaign.events)} events, {len(high_severity)} high-severity")
            return True
            
        except Exception as e:
            self.log_test("APT29 Attack Scenario", False, f"Error: {str(e)}")
            return False
    
    def test_sql_injection_attack(self) -> bool:
        """Test SQL injection attack scenario."""
        print("\n💉 Testing SQL Injection Attack Scenario")
        print("-" * 40)
        
        try:
            # Generate web access logs
            events = self.generator.generate_logs(LogType.WEB_ACCESS, count=100)
            
            # Look for SQL injection events
            sql_events = []
            for event in events:
                if (event.raw_data and 
                    ('sql' in event.message.lower() or 
                     'injection' in event.message.lower() or
                     'union' in event.message.lower())):
                    sql_events.append(event)
            
            if len(sql_events) == 0:
                self.log_test("SQL Injection Detection", False, "No SQL injection events found")
                return False
            
            # Check event characteristics
            for event in sql_events:
                if event.severity not in [LogSeverity.HIGH, LogSeverity.CRITICAL]:
                    self.log_test("SQL Injection Severity", False, f"Expected high severity, got {event.severity}")
                    return False
                
                if not event.attack_tactic:
                    self.log_test("SQL Injection Tactic", False, "Missing attack tactic")
                    return False
            
            self.log_test("SQL Injection Attack", True, f"Found {len(sql_events)} SQL injection events")
            return True
            
        except Exception as e:
            self.log_test("SQL Injection Attack", False, f"Error: {str(e)}")
            return False
    
    def test_malware_detection_scenario(self) -> bool:
        """Test malware detection scenario."""
        print("\n🦠 Testing Malware Detection Scenario")
        print("-" * 40)
        
        try:
            # Generate endpoint logs
            events = self.generator.generate_logs(LogType.ENDPOINT, count=150)
            
            # Look for malware detection events
            malware_events = []
            for event in events:
                if ('malware' in event.message.lower() or 
                    'virus' in event.message.lower() or
                    'trojan' in event.message.lower() or
                    'ransomware' in event.message.lower()):
                    malware_events.append(event)
            
            if len(malware_events) == 0:
                self.log_test("Malware Detection", False, "No malware detection events found")
                return False
            
            # Check event characteristics
            for event in malware_events:
                if event.severity != LogSeverity.CRITICAL:
                    self.log_test("Malware Severity", False, f"Expected CRITICAL severity, got {event.severity}")
                    return False
                
                if not event.raw_data or 'threat_name' not in event.raw_data:
                    self.log_test("Malware Event Data", False, "Missing threat information")
                    return False
            
            # Check for different malware types
            threat_types = set()
            for event in malware_events:
                if event.raw_data and 'threat_name' in event.raw_data:
                    threat_types.add(event.raw_data['threat_name'])
            
            self.log_test("Malware Detection", True, f"Found {len(malware_events)} malware events, {len(threat_types)} threat types")
            return True
            
        except Exception as e:
            self.log_test("Malware Detection", False, f"Error: {str(e)}")
            return False
    
    def test_network_scanning_scenario(self) -> bool:
        """Test network scanning scenario."""
        print("\n🔍 Testing Network Scanning Scenario")
        print("-" * 40)
        
        try:
            # Generate IDS logs
            events = self.generator.generate_logs(LogType.IDS, count=200)
            
            # Look for port scanning events
            scan_events = []
            for event in events:
                if ('scan' in event.message.lower() or 
                    'port' in event.message.lower() or
                    'nmap' in event.message.lower()):
                    scan_events.append(event)
            
            if len(scan_events) == 0:
                self.log_test("Network Scanning Detection", False, "No scanning events found")
                return False
            
            # Check event characteristics
            for event in scan_events:
                if event.severity not in [LogSeverity.MEDIUM, LogSeverity.HIGH]:
                    self.log_test("Scan Severity", False, f"Expected medium/high severity, got {event.severity}")
                    return False
                
                if not event.attack_tactic or event.attack_tactic != AttackTactic.RECONNAISSANCE:
                    self.log_test("Scan Tactic", False, "Expected reconnaissance tactic")
                    return False
            
            self.log_test("Network Scanning", True, f"Found {len(scan_events)} scanning events")
            return True
            
        except Exception as e:
            self.log_test("Network Scanning", False, f"Error: {str(e)}")
            return False
    
    def test_privilege_escalation_scenario(self) -> bool:
        """Test privilege escalation scenario."""
        print("\n⬆️ Testing Privilege Escalation Scenario")
        print("-" * 40)
        
        try:
            # Generate Windows event logs
            events = self.generator.generate_logs(LogType.WINDOWS_EVENT, count=100)
            
            # Look for privilege escalation events
            priv_events = []
            for event in events:
                if ('privilege' in event.message.lower() or 
                    'escalation' in event.message.lower() or
                    'sudo' in event.message.lower() or
                    'admin' in event.message.lower()):
                    priv_events.append(event)
            
            if len(priv_events) == 0:
                self.log_test("Privilege Escalation Detection", False, "No privilege escalation events found")
                return False
            
            # Check event characteristics
            for event in priv_events:
                if event.severity not in [LogSeverity.HIGH, LogSeverity.CRITICAL]:
                    self.log_test("Privilege Escalation Severity", False, f"Expected high severity, got {event.severity}")
                    return False
            
            self.log_test("Privilege Escalation", True, f"Found {len(priv_events)} privilege escalation events")
            return True
            
        except Exception as e:
            self.log_test("Privilege Escalation", False, f"Error: {str(e)}")
            return False
    
    def test_data_exfiltration_scenario(self) -> bool:
        """Test data exfiltration scenario."""
        print("\n📤 Testing Data Exfiltration Scenario")
        print("-" * 40)
        
        try:
            # Generate correlated events
            events = self.generator.generate_correlated_events(
                log_types=[LogType.IDS, LogType.WEB_ACCESS, LogType.ENDPOINT],
                correlation_strength=0.9,
                time_window="2h"
            )
            
            # Look for exfiltration events
            exfil_events = []
            for event in events:
                if ('exfiltrat' in event.message.lower() or 
                    'data' in event.message.lower() and 'large' in event.message.lower() or
                    event.attack_tactic == AttackTactic.EXFILTRATION):
                    exfil_events.append(event)
            
            if len(exfil_events) == 0:
                self.log_test("Data Exfiltration Detection", False, "No exfiltration events found")
                return False
            
            # Check event characteristics
            for event in exfil_events:
                if event.severity != LogSeverity.CRITICAL:
                    self.log_test("Exfiltration Severity", False, f"Expected CRITICAL severity, got {event.severity}")
                    return False
            
            self.log_test("Data Exfiltration", True, f"Found {len(exfil_events)} exfiltration events")
            return True
            
        except Exception as e:
            self.log_test("Data Exfiltration", False, f"Error: {str(e)}")
            return False
    
    def test_lateral_movement_scenario(self) -> bool:
        """Test lateral movement scenario."""
        print("\n🔄 Testing Lateral Movement Scenario")
        print("-" * 40)
        
        try:
            # Generate network topology events
            topology = NetworkTopology(
                subnets=["10.0.0.0/8", "192.168.0.0/16"],
                internet_facing_ips=["1.2.3.4"],
                internal_networks=["10.0.0.0/8"],
                critical_assets=["10.0.1.100", "10.0.1.101"]
            )
            
            events = self.generator.generate_network_topology_events(
                topology=topology,
                event_count=300
            )
            
            # Look for lateral movement patterns
            lateral_events = []
            for event in events:
                if (event.attack_tactic == AttackTactic.LATERAL_MOVEMENT or
                    'lateral' in event.message.lower() or
                    'movement' in event.message.lower()):
                    lateral_events.append(event)
            
            # Check for internal network communication
            internal_comm = []
            for event in events:
                if (event.source and event.destination and
                    event.source.ip_address.startswith('10.') and
                    event.destination.ip_address.startswith('10.')):
                    internal_comm.append(event)
            
            if len(internal_comm) == 0:
                self.log_test("Internal Communication", False, "No internal network communication found")
                return False
            
            self.log_test("Lateral Movement", True, f"Found {len(lateral_events)} lateral movement events, {len(internal_comm)} internal communications")
            return True
            
        except Exception as e:
            self.log_test("Lateral Movement", False, f"Error: {str(e)}")
            return False
    
    def test_brute_force_attack_scenario(self) -> bool:
        """Test brute force attack scenario."""
        print("\n🔨 Testing Brute Force Attack Scenario")
        print("-" * 40)
        
        try:
            # Generate web access and Windows event logs
            web_events = self.generator.generate_logs(LogType.WEB_ACCESS, count=100)
            windows_events = self.generator.generate_logs(LogType.WINDOWS_EVENT, count=100)
            
            all_events = web_events + windows_events
            
            # Look for brute force events
            brute_events = []
            for event in all_events:
                if ('brute' in event.message.lower() or 
                    'force' in event.message.lower() or
                    'failed' in event.message.lower() and 'login' in event.message.lower() or
                    'authentication' in event.message.lower() and 'failed' in event.message.lower()):
                    brute_events.append(event)
            
            if len(brute_events) == 0:
                self.log_test("Brute Force Detection", False, "No brute force events found")
                return False
            
            # Check for repeated failures from same source
            source_failures = {}
            for event in brute_events:
                if event.source and event.source.ip_address:
                    source_failures[event.source.ip_address] = source_failures.get(event.source.ip_address, 0) + 1
            
            repeated_failures = [ip for ip, count in source_failures.items() if count > 5]
            
            self.log_test("Brute Force Attack", True, f"Found {len(brute_events)} brute force events, {len(repeated_failures)} sources with repeated failures")
            return True
            
        except Exception as e:
            self.log_test("Brute Force Attack", False, f"Error: {str(e)}")
            return False
    
    def test_ransomware_scenario(self) -> bool:
        """Test ransomware scenario."""
        print("\n🔒 Testing Ransomware Scenario")
        print("-" * 40)
        
        try:
            # Generate endpoint logs
            events = self.generator.generate_logs(LogType.ENDPOINT, count=200)
            
            # Look for ransomware events
            ransom_events = []
            for event in events:
                if ('ransom' in event.message.lower() or 
                    'encrypt' in event.message.lower() or
                    'crypto' in event.message.lower()):
                    ransom_events.append(event)
            
            if len(ransom_events) == 0:
                self.log_test("Ransomware Detection", False, "No ransomware events found")
                return False
            
            # Check event characteristics
            for event in ransom_events:
                if event.severity != LogSeverity.CRITICAL:
                    self.log_test("Ransomware Severity", False, f"Expected CRITICAL severity, got {event.severity}")
                    return False
                
                if not event.raw_data or 'threat_name' not in event.raw_data:
                    self.log_test("Ransomware Event Data", False, "Missing threat information")
                    return False
            
            self.log_test("Ransomware Attack", True, f"Found {len(ransom_events)} ransomware events")
            return True
            
        except Exception as e:
            self.log_test("Ransomware Attack", False, f"Error: {str(e)}")
            return False
    
    def test_insider_threat_scenario(self) -> bool:
        """Test insider threat scenario."""
        print("\n👤 Testing Insider Threat Scenario")
        print("-" * 40)
        
        try:
            # Generate correlated events with high correlation
            events = self.generator.generate_correlated_events(
                log_types=[LogType.WINDOWS_EVENT, LogType.WEB_ACCESS, LogType.ENDPOINT],
                correlation_strength=0.95,
                time_window="4h"
            )
            
            # Look for insider threat indicators
            insider_events = []
            for event in events:
                if (event.user and 
                    ('unauthorized' in event.message.lower() or
                     'privilege' in event.message.lower() or
                     'sensitive' in event.message.lower() or
                     'data' in event.message.lower())):
                    insider_events.append(event)
            
            # Check for unusual user activity
            user_activity = {}
            for event in events:
                if event.user:
                    user_activity[event.user] = user_activity.get(event.user, 0) + 1
            
            # Find users with high activity
            high_activity_users = [user for user, count in user_activity.items() if count > 20]
            
            self.log_test("Insider Threat", True, f"Found {len(insider_events)} insider threat events, {len(high_activity_users)} high-activity users")
            return True
            
        except Exception as e:
            self.log_test("Insider Threat", False, f"Error: {str(e)}")
            return False
    
    def test_zero_day_exploit_scenario(self) -> bool:
        """Test zero-day exploit scenario."""
        print("\n💥 Testing Zero-Day Exploit Scenario")
        print("-" * 40)
        
        try:
            # Generate IDS and endpoint logs
            ids_events = self.generator.generate_logs(LogType.IDS, count=150)
            endpoint_events = self.generator.generate_logs(LogType.ENDPOINT, count=150)
            
            all_events = ids_events + endpoint_events
            
            # Look for zero-day indicators
            zero_day_events = []
            for event in all_events:
                if ('exploit' in event.message.lower() or 
                    'zero' in event.message.lower() or
                    'unknown' in event.message.lower() or
                    'new' in event.message.lower() and 'threat' in event.message.lower()):
                    zero_day_events.append(event)
            
            if len(zero_day_events) == 0:
                self.log_test("Zero-Day Detection", False, "No zero-day events found")
                return False
            
            # Check for high confidence scores
            high_confidence = [e for e in zero_day_events if e.confidence_score and e.confidence_score > 0.8]
            
            self.log_test("Zero-Day Exploit", True, f"Found {len(zero_day_events)} zero-day events, {len(high_confidence)} high-confidence")
            return True
            
        except Exception as e:
            self.log_test("Zero-Day Exploit", False, f"Error: {str(e)}")
            return False
    
    def run_all_scenarios(self) -> None:
        """Run all cybersecurity scenarios."""
        print("🛡️ Cybersecurity Log Generation - Scenario Testing")
        print("=" * 60)
        
        scenarios = [
            ("APT29 Attack", self.test_apt29_attack_scenario),
            ("SQL Injection", self.test_sql_injection_attack),
            ("Malware Detection", self.test_malware_detection_scenario),
            ("Network Scanning", self.test_network_scanning_scenario),
            ("Privilege Escalation", self.test_privilege_escalation_scenario),
            ("Data Exfiltration", self.test_data_exfiltration_scenario),
            ("Lateral Movement", self.test_lateral_movement_scenario),
            ("Brute Force Attack", self.test_brute_force_attack_scenario),
            ("Ransomware", self.test_ransomware_scenario),
            ("Insider Threat", self.test_insider_threat_scenario),
            ("Zero-Day Exploit", self.test_zero_day_exploit_scenario),
        ]
        
        for scenario_name, test_func in scenarios:
            try:
                test_func()
            except Exception as e:
                self.log_test(scenario_name, False, f"Exception: {str(e)}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 SCENARIO TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, passed, _ in self.test_results if passed)
        total = len(self.test_results)
        
        print(f"Total Scenarios: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for name, passed, details in self.test_results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} {name}")
            if details:
                print(f"    └─ {details}")
        
        print("\n🎯 SCENARIO INSIGHTS:")
        if passed == total:
            print("🎉 All scenarios passed! The system generates realistic cybersecurity events.")
        elif passed >= total * 0.8:
            print("✅ Most scenarios passed. The system is working well for most attack types.")
        elif passed >= total * 0.6:
            print("⚠️  Some scenarios failed. Review attack pattern generation.")
        else:
            print("❌ Many scenarios failed. System needs significant improvements.")
        
        # Attack type coverage
        attack_types = [
            "APT Campaigns", "Web Attacks", "Malware", "Network Reconnaissance",
            "Privilege Escalation", "Data Exfiltration", "Lateral Movement",
            "Brute Force", "Ransomware", "Insider Threats", "Zero-Day Exploits"
        ]
        
        print(f"\n🔍 ATTACK TYPE COVERAGE:")
        for i, attack_type in enumerate(attack_types):
            if i < len(self.test_results):
                _, passed, _ = self.test_results[i]
                status = "✓" if passed else "✗"
                print(f"  {status} {attack_type}")


def main():
    """Main function to run scenario tests."""
    try:
        tester = LogScenarioTester()
        tester.run_all_scenarios()
        
        # Return exit code based on results
        passed = sum(1 for _, passed, _ in tester.test_results if passed)
        total = len(tester.test_results)
        
        if passed == total:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"Scenario testing error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
