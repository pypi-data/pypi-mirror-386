#!/usr/bin/env python3
"""
Simple test script for the enhanced cybersecurity log generator.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        from core.models import CyberdefensePillar, ThreatActor, LogSeverity
        print("✅ Core models imported successfully")
        
        from core.enhanced_generator import EnhancedLogGenerator
        print("✅ Enhanced generator imported successfully")
        
        from core.pillar_generators.vendor_risk_generator import VendorRiskGenerator
        print("✅ Vendor risk generator imported successfully")
        
        from core.pillar_generators.api_security_generator import APISecurityGenerator
        print("✅ API security generator imported successfully")
        
        from core.pillar_generators.endpoint_security_generator import EndpointSecurityGenerator
        print("✅ Endpoint security generator imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_generator():
    """Test the enhanced generator."""
    print("\nTesting enhanced generator...")
    
    try:
        from core.enhanced_generator import EnhancedLogGenerator
        from core.models import CyberdefensePillar, ThreatActor
        
        # Initialize generator
        generator = EnhancedLogGenerator()
        print("✅ Generator initialized successfully")
        
        # Test pillar generation
        logs = generator.generate_logs(
            pillar=CyberdefensePillar.VENDOR_RISK,
            count=5,
            time_range="24h"
        )
        print(f"✅ Generated {len(logs)} vendor risk logs")
        
        # Test campaign generation
        campaign = generator.generate_campaign(
            threat_actor=ThreatActor.APT29,
            duration="24h",
            target_count=10
        )
        print(f"✅ Generated {len(campaign.events)} campaign events")
        
        # Test correlated events
        correlated_events = generator.generate_correlated_events(
            log_types="endpoint_security,vendor_risk",
            count=10,
            correlation_strength=0.7
        )
        print(f"✅ Generated {len(correlated_events)} correlated events")
        
        return True
        
    except Exception as e:
        print(f"❌ Generator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Enhanced Cybersecurity Log Generator - Test Suite")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        return False
    
    # Test generator
    if not test_generator():
        print("\n❌ Generator tests failed")
        return False
    
    print("\n✅ All tests passed!")
    print("🎯 Enhanced generator is working correctly")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






