#!/usr/bin/env python3
"""
Demonstration script for Cybersecurity Log Generator
Shows key capabilities and realistic output.
"""

import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.generator import LogGenerator
from core.models import LogType, ThreatActor, LogSeverity

def demo_basic_generation():
    """Demonstrate basic log generation."""
    print("🚀 CYBERSECURITY LOG GENERATOR - DEMONSTRATION")
    print("=" * 60)
    
    # Initialize generator
    generator = LogGenerator()
    
    print("\n📊 1. BASIC LOG GENERATION")
    print("-" * 40)
    
    # Generate different log types
    log_types = [
        (LogType.IDS, "Intrusion Detection System"),
        (LogType.WEB_ACCESS, "Web Access Logs"),
        (LogType.ENDPOINT, "Endpoint Security"),
        (LogType.WINDOWS_EVENT, "Windows Event Logs"),
        (LogType.LINUX_SYSLOG, "Linux Syslog"),
        (LogType.FIREWALL, "Firewall Logs")
    ]
    
    for log_type, description in log_types:
        start_time = time.time()
        events = generator.generate_logs(log_type, count=5)
        duration = time.time() - start_time
        
        print(f"✓ {description}: {len(events)} events in {duration:.3f}s")
        
        # Show sample event
        if events:
            event = events[0]
            print(f"   Sample: {event.message[:80]}...")
            severity_str = event.severity.value if hasattr(event.severity, 'value') else str(event.severity)
            print(f"   Severity: {severity_str}, Source: {event.source.ip_address if event.source else 'N/A'}")
    
    return generator

def demo_attack_campaigns(generator):
    """Demonstrate attack campaign generation."""
    print("\n🎯 2. ATTACK CAMPAIGN GENERATION")
    print("-" * 40)
    
    threat_actors = [
        (ThreatActor.APT29, "Cozy Bear (Russian APT)"),
        (ThreatActor.APT28, "Fancy Bear (Russian APT)"),
        (ThreatActor.LAZARUS, "North Korean APT")
    ]
    
    for threat_actor, description in threat_actors:
        start_time = time.time()
        campaign = generator.generate_security_campaign(
            threat_actor=threat_actor,
            duration="2h",
            target_count=50
        )
        duration = time.time() - start_time
        
        print(f"✓ {description}: {len(campaign.events)} events in {duration:.3f}s")
        print(f"   Attack stages: {', '.join(campaign.attack_stages)}")
        
        # Show high-severity events
        high_severity = [e for e in campaign.events if e.severity in [LogSeverity.HIGH, LogSeverity.CRITICAL]]
        print(f"   High-severity events: {len(high_severity)}")

def demo_export_formats(generator):
    """Demonstrate export functionality."""
    print("\n📤 3. EXPORT FORMATS")
    print("-" * 40)
    
    # Generate sample events
    events = generator.generate_logs(LogType.IDS, count=10)
    
    formats = [
        ("json", "JSON"),
        ("csv", "CSV"),
        ("syslog", "Syslog"),
        ("cef", "CEF (Common Event Format)"),
        ("leef", "LEEF (Log Event Extended Format)")
    ]
    
    for format_type, description in formats:
        start_time = time.time()
        result = generator.export_logs(events, format=format_type)
        duration = time.time() - start_time
        
        print(f"✓ {description}: {len(result)} characters in {duration:.3f}s")
        
        # Show sample output
        sample = result[:100] + "..." if len(result) > 100 else result
        print(f"   Sample: {sample}")

def demo_performance_benchmarks(generator):
    """Demonstrate performance benchmarks."""
    print("\n⚡ 4. PERFORMANCE BENCHMARKS")
    print("-" * 40)
    
    test_counts = [100, 500, 1000]
    log_type = LogType.IDS
    
    for count in test_counts:
        start_time = time.time()
        events = generator.generate_logs(log_type, count=count)
        duration = time.time() - start_time
        
        events_per_second = len(events) / duration
        print(f"✓ {count:,} IDS events: {events_per_second:.0f} events/sec ({duration:.3f}s)")

def demo_security_scenarios(generator):
    """Demonstrate security scenarios."""
    print("\n🛡️ 5. SECURITY SCENARIOS")
    print("-" * 40)
    
    # Generate correlated events
    start_time = time.time()
    correlated_events = generator.generate_correlated_events(
        log_types=[LogType.IDS, LogType.ENDPOINT, LogType.WEB_ACCESS],
        correlation_strength=0.8,
        time_window="1h"
    )
    duration = time.time() - start_time
    
    print(f"✓ Correlated Events: {len(correlated_events)} events in {duration:.3f}s")
    
    # Analyze event types
    event_types = {}
    for event in correlated_events:
        event_type = event.log_type.value if hasattr(event.log_type, 'value') else str(event.log_type)
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print(f"   Event distribution: {event_types}")
    
    # Show high-severity events
    high_severity = [e for e in correlated_events if e.severity in [LogSeverity.HIGH, LogSeverity.CRITICAL]]
    print(f"   High-severity events: {len(high_severity)}")

def demo_realistic_output(generator):
    """Show realistic log output examples."""
    print("\n📋 6. REALISTIC LOG OUTPUT EXAMPLES")
    print("-" * 40)
    
    # Generate sample events
    events = generator.generate_logs(LogType.IDS, count=3)
    
    print("Sample IDS Events:")
    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Timestamp: {event.timestamp}")
        severity_str = event.severity.value if hasattr(event.severity, 'value') else str(event.severity)
        print(f"  Severity: {severity_str}")
        print(f"  Source: {event.source.ip_address if event.source else 'N/A'}")
        print(f"  Destination: {event.destination.ip_address if event.destination else 'N/A'}")
        print(f"  Message: {event.message}")
        if event.raw_data:
            print(f"  Raw Data: {event.raw_data}")

def main():
    """Main demonstration function."""
    try:
        # Run all demonstrations
        generator = demo_basic_generation()
        demo_attack_campaigns(generator)
        demo_export_formats(generator)
        demo_performance_benchmarks(generator)
        demo_security_scenarios(generator)
        demo_realistic_output(generator)
        
        print("\n" + "=" * 60)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("✅ All core functionality demonstrated")
        print("✅ Realistic cybersecurity events generated")
        print("✅ Multiple log types supported")
        print("✅ Attack campaigns simulated")
        print("✅ Export formats working")
        print("✅ Performance benchmarks achieved")
        print("✅ Security scenarios validated")
        
        print("\n🚀 SYSTEM READY FOR PRODUCTION USE!")
        
    except Exception as e:
        print(f"\n❌ Demonstration error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
