#!/usr/bin/env python3
"""
Command-line interface for cybersecurity-log-generator.
"""

import argparse
import sys
import json
from typing import Optional

from .core.generator import LogGenerator
from .core.enhanced_generator import EnhancedLogGenerator
from .core.models import LogType, CyberdefensePillar


def generate_logs_cmd(args):
    """Generate logs using the basic generator."""
    try:
        generator = LogGenerator()
        log_type = LogType(args.log_type.lower())
        logs = generator.generate_logs(log_type, count=args.count, time_range=args.time_range)
        
        # Convert to dictionary format
        logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(logs_data, f, indent=2, default=str)
            print(f"Generated {len(logs_data)} logs and saved to {args.output}")
        else:
            print(json.dumps(logs_data, indent=2, default=str))
            
    except Exception as e:
        print(f"Error generating logs: {e}", file=sys.stderr)
        sys.exit(1)


def generate_pillar_logs_cmd(args):
    """Generate logs using the enhanced generator for specific pillars."""
    try:
        enhanced_generator = EnhancedLogGenerator()
        pillar = CyberdefensePillar(args.pillar.lower())
        logs = enhanced_generator.generate_logs(pillar, count=args.count, time_range=args.time_range)
        
        # Convert to dictionary format
        logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(logs_data, f, indent=2, default=str)
            print(f"Generated {len(logs_data)} {args.pillar} logs and saved to {args.output}")
        else:
            print(json.dumps(logs_data, indent=2, default=str))
            
    except Exception as e:
        print(f"Error generating pillar logs: {e}", file=sys.stderr)
        sys.exit(1)


def list_supported_types():
    """List all supported log types and pillars."""
    print("Supported Log Types:")
    for log_type in LogType:
        print(f"  - {log_type.value}")
    
    print("\nSupported Cyberdefense Pillars:")
    for pillar in CyberdefensePillar:
        print(f"  - {pillar.value}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cybersecurity Log Generator - Generate synthetic cybersecurity logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate --type ids --count 100
  %(prog)s pillar --pillar authentication --count 200 --output auth_logs.json
  %(prog)s list-types
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate logs command
    generate_parser = subparsers.add_parser('generate', help='Generate basic cybersecurity logs')
    generate_parser.add_argument('--type', required=True, 
                               choices=[lt.value for lt in LogType],
                               help='Type of logs to generate')
    generate_parser.add_argument('--count', type=int, default=100,
                               help='Number of logs to generate (default: 100)')
    generate_parser.add_argument('--time-range', default='24h',
                               help='Time range for events (default: 24h)')
    generate_parser.add_argument('--output', '-o',
                               help='Output file path (default: stdout)')
    generate_parser.set_defaults(func=generate_logs_cmd)
    
    # Generate pillar logs command
    pillar_parser = subparsers.add_parser('pillar', help='Generate logs for specific cyberdefense pillars')
    pillar_parser.add_argument('--pillar', required=True,
                              choices=[p.value for p in CyberdefensePillar],
                              help='Cyberdefense pillar to generate logs for')
    pillar_parser.add_argument('--count', type=int, default=100,
                              help='Number of logs to generate (default: 100)')
    pillar_parser.add_argument('--time-range', default='24h',
                              help='Time range for events (default: 24h)')
    pillar_parser.add_argument('--output', '-o',
                              help='Output file path (default: stdout)')
    pillar_parser.set_defaults(func=generate_pillar_logs_cmd)
    
    # List types command
    list_parser = subparsers.add_parser('list-types', help='List all supported log types and pillars')
    list_parser.set_defaults(func=lambda args: list_supported_types())
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
