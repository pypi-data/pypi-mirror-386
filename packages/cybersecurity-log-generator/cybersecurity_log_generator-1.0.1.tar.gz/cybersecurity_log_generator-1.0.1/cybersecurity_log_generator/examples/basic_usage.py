#!/usr/bin/env python3
"""
Basic usage examples for cybersecurity-log-generator.
"""

from cybersecurity_log_generator import LogGenerator, EnhancedLogGenerator
from cybersecurity_log_generator.core.models import LogType, CyberdefensePillar
from cybersecurity_log_generator.utils import export_logs, validate_logs, analyze_log_patterns


def basic_log_generation():
    """Example of basic log generation."""
    print("=== Basic Log Generation ===")
    
    # Create generator
    generator = LogGenerator()
    
    # Generate IDS logs
    print("Generating IDS logs...")
    ids_logs = generator.generate_logs(LogType.IDS, count=10, time_range="1h")
    print(f"Generated {len(ids_logs)} IDS logs")
    
    # Generate web access logs
    print("Generating web access logs...")
    web_logs = generator.generate_logs(LogType.WEB_ACCESS, count=5, time_range="30m")
    print(f"Generated {len(web_logs)} web access logs")
    
    return ids_logs, web_logs


def enhanced_log_generation():
    """Example of enhanced log generation."""
    print("\n=== Enhanced Log Generation ===")
    
    # Create enhanced generator
    enhanced_generator = EnhancedLogGenerator()
    
    # Generate authentication logs
    print("Generating authentication logs...")
    auth_logs = enhanced_generator.generate_logs(
        CyberdefensePillar.AUTHENTICATION, 
        count=15, 
        time_range="2h"
    )
    print(f"Generated {len(auth_logs)} authentication logs")
    
    # Generate network security logs
    print("Generating network security logs...")
    network_logs = enhanced_generator.generate_logs(
        CyberdefensePillar.NETWORK_SECURITY,
        count=10,
        time_range="1h"
    )
    print(f"Generated {len(network_logs)} network security logs")
    
    return auth_logs, network_logs


def correlated_events_example():
    """Example of correlated events generation."""
    print("\n=== Correlated Events Generation ===")
    
    enhanced_generator = EnhancedLogGenerator()
    
    # Generate correlated events across multiple pillars
    print("Generating correlated events...")
    correlated_logs = enhanced_generator.generate_correlated_events(
        pillars=[
            CyberdefensePillar.AUTHENTICATION,
            CyberdefensePillar.NETWORK_SECURITY,
            CyberdefensePillar.ENDPOINT_SECURITY
        ],
        count=20,
        correlation_strength=0.8
    )
    print(f"Generated {len(correlated_logs)} correlated events")
    
    return correlated_logs


def campaign_logs_example():
    """Example of campaign logs generation."""
    print("\n=== Campaign Logs Generation ===")
    
    enhanced_generator = EnhancedLogGenerator()
    
    # Generate APT29 campaign logs
    print("Generating APT29 campaign logs...")
    campaign_logs = enhanced_generator.generate_campaign_logs(
        threat_actor="APT29",
        duration="24h",
        target_count=25
    )
    print(f"Generated {len(campaign_logs)} campaign logs")
    
    return campaign_logs


def export_examples():
    """Example of log export functionality."""
    print("\n=== Log Export Examples ===")
    
    # Generate some sample logs
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.IDS, count=5, time_range="1h")
    
    # Convert to dictionary format
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    
    # Export in different formats
    print("Exporting logs in different formats...")
    
    # JSON export
    json_file = export_logs(logs_data, format="json", output_path="example_logs")
    print(f"Exported to {json_file}")
    
    # CSV export
    csv_file = export_logs(logs_data, format="csv", output_path="example_logs")
    print(f"Exported to {csv_file}")
    
    # Syslog export
    syslog_file = export_logs(logs_data, format="syslog", output_path="example_logs")
    print(f"Exported to {syslog_file}")
    
    return logs_data


def validation_example():
    """Example of log validation."""
    print("\n=== Log Validation Example ===")
    
    # Generate some logs
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.WEB_ACCESS, count=10, time_range="1h")
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    
    # Validate logs
    print("Validating logs...")
    validation_result = validate_logs(logs_data)
    
    print(f"Valid: {validation_result['valid']}")
    print(f"Count: {validation_result['count']}")
    print(f"Errors: {len(validation_result['errors'])}")
    print(f"Warnings: {len(validation_result['warnings'])}")
    print(f"Unique event types: {validation_result['unique_event_types']}")
    print(f"Unique severities: {validation_result['unique_severities']}")
    
    return validation_result


def analysis_example():
    """Example of log pattern analysis."""
    print("\n=== Log Pattern Analysis Example ===")
    
    # Generate some logs
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.ENDPOINT, count=20, time_range="2h")
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    
    # Analyze patterns
    print("Analyzing log patterns...")
    analysis_result = analyze_log_patterns(logs_data)
    
    print(f"Total logs: {analysis_result['total_logs']}")
    print(f"Unique event types: {analysis_result['unique_event_types']}")
    print(f"Unique severities: {analysis_result['unique_severities']}")
    print(f"Unique sources: {analysis_result['unique_sources']}")
    print(f"Most common event type: {analysis_result['most_common_event_type']}")
    print(f"Most common severity: {analysis_result['most_common_severity']}")
    
    return analysis_result


def main():
    """Run all examples."""
    print("Cybersecurity Log Generator - Basic Usage Examples")
    print("=" * 60)
    
    try:
        # Basic log generation
        ids_logs, web_logs = basic_log_generation()
        
        # Enhanced log generation
        auth_logs, network_logs = enhanced_log_generation()
        
        # Correlated events
        correlated_logs = correlated_events_example()
        
        # Campaign logs
        campaign_logs = campaign_logs_example()
        
        # Export examples
        exported_logs = export_examples()
        
        # Validation
        validation_result = validation_example()
        
        # Analysis
        analysis_result = analysis_example()
        
        print("\n=== Summary ===")
        print("All examples completed successfully!")
        print(f"Generated {len(ids_logs)} IDS logs")
        print(f"Generated {len(web_logs)} web access logs")
        print(f"Generated {len(auth_logs)} authentication logs")
        print(f"Generated {len(network_logs)} network security logs")
        print(f"Generated {len(correlated_logs)} correlated events")
        print(f"Generated {len(campaign_logs)} campaign logs")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())