#!/usr/bin/env python3
"""
Enhanced demo script for the 24-pillar cybersecurity log generator.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_generator import EnhancedLogGenerator
from core.models import CyberdefensePillar, ThreatActor


def demo_pillar_generation():
    """Demo generating logs for specific pillars."""
    print("🔒 Enhanced Cybersecurity Log Generator - 24 Pillars Demo")
    print("=" * 60)
    
    # Initialize the enhanced generator
    generator = EnhancedLogGenerator()
    
    # Demo 1: Generate logs for Vendor Risk pillar
    print("\n📊 Demo 1: Vendor Risk Pillar")
    print("-" * 30)
    
    vendor_risk_logs = generator.generate_logs(
        pillar=CyberdefensePillar.VENDOR_RISK,
        count=10,
        time_range="24h"
    )
    
    print(f"Generated {len(vendor_risk_logs)} vendor risk logs")
    for i, log in enumerate(vendor_risk_logs[:3]):  # Show first 3
        print(f"  {i+1}. {log.message} (Severity: {log.severity})")
    
    # Demo 2: Generate logs for API Security pillar
    print("\n🔌 Demo 2: API Security Pillar")
    print("-" * 30)
    
    api_security_logs = generator.generate_logs(
        pillar=CyberdefensePillar.API_SECURITY,
        count=10,
        time_range="24h"
    )
    
    print(f"Generated {len(api_security_logs)} API security logs")
    for i, log in enumerate(api_security_logs[:3]):  # Show first 3
        print(f"  {i+1}. {log.message} (Severity: {log.severity})")
    
    # Demo 3: Generate logs for Endpoint Security pillar
    print("\n💻 Demo 3: Endpoint Security Pillar")
    print("-" * 30)
    
    endpoint_security_logs = generator.generate_logs(
        pillar=CyberdefensePillar.ENDPOINT_SECURITY,
        count=10,
        time_range="24h"
    )
    
    print(f"Generated {len(endpoint_security_logs)} endpoint security logs")
    for i, log in enumerate(endpoint_security_logs[:3]):  # Show first 3
        print(f"  {i+1}. {log.message} (Severity: {log.severity})")


def demo_campaign_generation():
    """Demo generating attack campaigns."""
    print("\n🎯 Demo 4: Attack Campaign Generation")
    print("-" * 40)
    
    generator = EnhancedLogGenerator()
    
    # Generate APT29 campaign
    campaign = generator.generate_campaign(
        threat_actor=ThreatActor.APT29,
        duration="24h",
        target_count=20
    )
    
    print(f"Generated {len(campaign.events)} events for {campaign.threat_actor.value} campaign")
    print(f"Campaign ID: {campaign.campaign_id}")
    print(f"Objectives: {', '.join(campaign.objectives)}")
    
    # Show sample events
    print("\nSample campaign events:")
    for i, event in enumerate(campaign.events[:3]):
        print(f"  {i+1}. {event.message} (Pillar: {event.pillar.value})")


def demo_correlated_events():
    """Demo generating correlated events."""
    print("\n🔗 Demo 5: Correlated Events Generation")
    print("-" * 40)
    
    generator = EnhancedLogGenerator()
    
    # Generate correlated events across multiple pillars
    correlated_events = generator.generate_correlated_events(
        log_types="endpoint_security,vendor_risk,api_security",
        count=15,
        correlation_strength=0.8
    )
    
    print(f"Generated {len(correlated_events)} correlated events")
    
    # Group by pillar
    pillar_counts = {}
    for event in correlated_events:
        pillar = event.pillar.value
        pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
    
    print("Events by pillar:")
    for pillar, count in pillar_counts.items():
        print(f"  {pillar}: {count} events")
    
    # Show correlation IDs
    correlation_ids = set(event.correlation_id for event in correlated_events if event.correlation_id)
    print(f"Correlation IDs: {len(correlation_ids)}")


def demo_pillar_analysis():
    """Demo analyzing pillar capabilities."""
    print("\n📈 Demo 6: Pillar Analysis")
    print("-" * 30)
    
    generator = EnhancedLogGenerator()
    
    # Get supported pillars
    pillars = generator.get_supported_pillars()
    print(f"Supported pillars: {len(pillars)}")
    
    # Show first 10 pillars
    print("First 10 pillars:")
    for i, pillar in enumerate(pillars[:10]):
        print(f"  {i+1}. {pillar.value}")
    
    # Get threat actors
    threat_actors = generator.get_threat_actors()
    print(f"\nSupported threat actors: {len(threat_actors)}")
    for actor in threat_actors:
        print(f"  - {actor.value}")
    
    # Get correlation rules
    correlation_rules = generator.get_correlation_rules()
    print(f"\nCorrelation rules: {len(correlation_rules)}")
    for rule in correlation_rules:
        print(f"  - {rule['name']}: {', '.join([p.value for p in rule['pillars']])}")


def save_sample_logs():
    """Save sample logs to files."""
    print("\n💾 Demo 7: Saving Sample Logs")
    print("-" * 30)
    
    generator = EnhancedLogGenerator()
    
    # Generate sample logs for each implemented pillar
    implemented_pillars = [
        CyberdefensePillar.VENDOR_RISK,
        CyberdefensePillar.API_SECURITY,
        CyberdefensePillar.ENDPOINT_SECURITY
    ]
    
    for pillar in implemented_pillars:
        logs = generator.generate_logs(pillar, count=5, time_range="24h")
        
        # Convert to JSON
        logs_data = [log.dict() for log in logs]
        json_data = json.dumps(logs_data, indent=2, default=str)
        
        # Save to file
        filename = f"sample_{pillar.value}_logs.json"
        with open(filename, 'w') as f:
            f.write(json_data)
        
        print(f"Saved {len(logs)} {pillar.value} logs to {filename}")


def main():
    """Run all demos."""
    try:
        demo_pillar_generation()
        demo_campaign_generation()
        demo_correlated_events()
        demo_pillar_analysis()
        save_sample_logs()
        
        print("\n✅ Enhanced Cybersecurity Log Generator Demo Complete!")
        print("=" * 60)
        print("🎯 Key Features Demonstrated:")
        print("  • 24 Cyberdefense Pillars Support")
        print("  • Pillar-Specific Attack Patterns")
        print("  • Coordinated Attack Campaigns")
        print("  • Cross-Pillar Correlation")
        print("  • Threat Actor Attribution")
        print("  • Realistic Log Generation")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()






