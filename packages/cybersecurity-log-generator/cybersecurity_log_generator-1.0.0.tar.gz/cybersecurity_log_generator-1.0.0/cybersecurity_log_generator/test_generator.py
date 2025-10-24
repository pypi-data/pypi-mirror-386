#!/usr/bin/env python3
"""
Simple test script for the Cybersecurity Log Generator.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.generator import LogGenerator
    from core.models import LogType, ThreatActor
    print("✓ Imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_basic_generation():
    """Test basic log generation."""
    print("\n=== Testing Basic Log Generation ===")
    
    try:
        # Initialize generator
        generator = LogGenerator()
        print("✓ Generator initialized")
        
        # Test IDS logs
        ids_logs = generator.generate_logs(LogType.IDS, count=10)
        print(f"✓ Generated {len(ids_logs)} IDS events")
        
        # Test web access logs
        web_logs = generator.generate_logs(LogType.WEB_ACCESS, count=5)
        print(f"✓ Generated {len(web_logs)} web access events")
        
        # Test endpoint logs
        endpoint_logs = generator.generate_logs(LogType.ENDPOINT, count=5)
        print(f"✓ Generated {len(endpoint_logs)} endpoint events")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in basic generation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_attack_campaign():
    """Test attack campaign generation."""
    print("\n=== Testing Attack Campaign Generation ===")
    
    try:
        generator = LogGenerator()
        
        # Generate APT29 campaign
        campaign = generator.generate_security_campaign(
            threat_actor=ThreatActor.APT29,
            duration="1h",
            target_count=10
        )
        
        print(f"✓ Generated campaign: {campaign.name}")
        print(f"✓ Threat actor: {campaign.threat_actor}")
        print(f"✓ Events: {len(campaign.events)}")
        print(f"✓ Attack stages: {campaign.attack_stages}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in attack campaign: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_export():
    """Test log export."""
    print("\n=== Testing Log Export ===")
    
    try:
        generator = LogGenerator()
        
        # Generate some events
        events = generator.generate_logs(LogType.IDS, count=5)
        
        # Test JSON export
        json_result = generator.export_logs(events, format="json")
        print(f"✓ JSON export: {len(json_result)} characters")
        
        # Test CSV export
        csv_result = generator.export_logs(events, format="csv")
        print(f"✓ CSV export: {len(csv_result)} characters")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in export: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Cybersecurity Log Generator - Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_generation,
        test_attack_campaign,
        test_export
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
