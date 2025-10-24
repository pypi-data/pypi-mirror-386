#!/usr/bin/env python3
"""
Enhanced MCP server implementation with comprehensive cybersecurity log generation tools.
This server provides detailed prompts, examples, and comprehensive documentation for all tools.
"""

import asyncio
import json
import sys
import requests
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import traceback
import signal
import os
import uvicorn
from fastmcp import FastMCP
import argparse
from dotenv import load_dotenv

# Global shutdown flag
shutdown_requested = False

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.generator import LogGenerator
from core.enhanced_generator import EnhancedLogGenerator
from core.models import LogType, ThreatActor, CyberdefensePillar

# Import hd-logging
from hd_logging import setup_logger

# Setup logger
logger = setup_logger("cybersecurity_log_generator", "logs/cybersecurity_log_generator.log")

def ingest_logs_to_victorialogs(logs_data: List[Dict], victorialogs_url: str = "http://localhost:9428") -> bool:
    """Ingest logs into VictoriaLogs.
    
    Args:
        logs_data: List of log dictionaries to ingest
        victorialogs_url: VictoriaLogs endpoint URL
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ingest_url = f"{victorialogs_url}/insert/jsonline"
        headers = {"Content-Type": "application/stream+json"}
        
        # Convert logs to ndjson format with datetime handling
        ndjson_data = "\n".join(json.dumps(log, cls=DateTimeEncoder) for log in logs_data)
        
        logger.info(f"Ingesting {len(logs_data)} logs to VictoriaLogs at {ingest_url}")
        
        response = requests.post(ingest_url, data=ndjson_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"Successfully ingested {len(logs_data)} logs to VictoriaLogs")
            return True
        else:
            logger.error(f"Failed to ingest logs to VictoriaLogs: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error ingesting logs to VictoriaLogs: {str(e)}")
        return False



def create_proper_mcp_server() -> FastMCP:
    """Create an enhanced MCP server with comprehensive cybersecurity log generation tools."""
    logger.info("Creating Enhanced Cybersecurity Log Generator MCP Server")
    
    # Initialize the log generators
    generator = LogGenerator()
    enhanced_generator = EnhancedLogGenerator()
    
    # Create MCP server with comprehensive configuration
    server = FastMCP(   
                     name="cybersecurity_log_generator",
                     instructions="""
        This MCP server provides comprehensive cybersecurity log generation tools for testing and analysis across all 24 cyberdefense pillars.
        
        🎯 CORE LOG GENERATION TOOLS:
        - generate_logs: Generate synthetic cybersecurity logs (with optional VictoriaLogs ingestion)
        - generate_attack_campaign: Generate coordinated attack campaigns  
        - get_supported_log_types: Get list of supported log types
        - get_supported_threat_actors: Get list of supported threat actors
        - generate_correlated_events: Generate correlated events across log types
        - export_logs: Export logs to files (JSON, CSV, Syslog, CEF, LEEF)
        - analyze_log_patterns: Analyze log patterns and provide insights
        - ingest_logs_to_victorialogs_tool: Ingest logs directly into VictoriaLogs
        
        🔑 24-PILLAR ENHANCED TOOLS:
        - generate_pillar_logs: Generate logs for specific cyberdefense pillars (vendor_risk, api_security, endpoint_security, etc.)
        - generate_campaign_logs: Generate coordinated attack campaigns across multiple pillars
        - generate_correlated_logs: Generate correlated events across multiple log types with configurable correlation strength
        - get_supported_pillars: Get list of all 24 supported cyberdefense pillars
        - get_pillar_attack_patterns: Get specific attack patterns for a pillar
        - get_threat_actors: Get supported threat actors (APT29, APT28, Lazarus, etc.)
        - get_correlation_rules: Get available correlation rules for cross-pillar attacks
        
        📊 SUPPORTED 24 PILLARS:
        1. vendor_risk - 3rd-Party/Vendor Risk management
        2. api_security - API Security and protection
        3. application_security - Application Security (SDLC)
        4. audit_compliance - Audit & Compliance
        5. authentication - Authentication systems
        6. authorization - Authorization controls
        7. cloud_security - Cloud Security (CNAPP)
        8. container_security - Container Security
        9. data_privacy - Data Privacy & Sovereignty
        10. data_protection - Data Protection & Backup
        11. detection_correlation - Detection & Correlation
        12. disaster_recovery - Disaster Recovery
        13. due_diligence - Due Diligence
        14. encryption - Encryption systems
        15. endpoint_security - Endpoint Security
        16. ai_security - Enterprise AI Security
        17. governance_risk - Governance, Risk & Strategy
        18. identity_governance - Identity Governance (IGA)
        19. incident_response - Incident Response
        20. network_security - Network Security
        21. ot_physical_security - OT/ICS & Physical Security
        22. security_awareness - Security Awareness & Training
        23. threat_intelligence - Threat Intelligence
        24. vulnerability_management - Vulnerability Management
        
        🎯 EXAMPLES:
        - "Generate 100 vendor risk logs" → call generate_pillar_logs("vendor_risk", 100)
        - "Create APT29 attack campaign" → call generate_campaign_logs("APT29", "72h", 100)
        - "Generate correlated events across endpoint and network security" → call generate_correlated_logs("endpoint_security,network_security", 50, 0.8)
        - "What pillars are supported?" → call get_supported_pillars()
        - "Get attack patterns for vendor risk" → call get_pillar_attack_patterns("vendor_risk")
        - "Generate 10 firewall logs" → call generate_logs("firewall", 10)
        """,
    )
    
    # Core Log Generation Tools
    @server.tool()
    def generate_logs(log_type: str, count: int = 100, time_range: str = "24h", ingest: bool = False, destination: str = "file") -> str:
        """Generate synthetic cybersecurity logs.
        
        This tool generates realistic cybersecurity logs for testing and analysis. It supports multiple log types with configurable parameters and optional VictoriaLogs ingestion.
        
        Args:
            log_type: Type of logs to generate. Supported types:
                - "ids": Intrusion Detection System logs with attack patterns
                - "web_access": Web application access logs with security events
                - "endpoint": Endpoint Detection and Response logs with malware detection
                - "windows_event": Windows Event Logs with security and system events
                - "linux_syslog": Linux Syslog with authentication and system events
                - "firewall": Firewall logs with traffic patterns and security events
            count: Number of log entries to generate (default: 100, max: 10000)
            time_range: Time range for events (default: "24h", examples: "1h", "24h", "7d")
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
            destination: Destination for logs - "file" or "victorialogs" (default: "file")
        
        Returns:
            JSON string containing generated log events with realistic patterns, timestamps, and security context.
            
        Examples:
            - "Generate 100 IDS logs" → generate_logs("ids", 100)
            - "Create 500 web access logs for 7 days" → generate_logs("web_access", 500, "7d")
            - "Generate 1000 endpoint logs and ingest to VictoriaLogs" → generate_logs("endpoint", 1000, "24h", ingest=True, destination="victorialogs")
            - "Generate firewall logs for 1 hour" → generate_logs("firewall", 200, "1h")
        """
        try:
            logger.info(f"Generating {count} {log_type} logs for {time_range}")
            
            # Convert string to LogType enum and generate logs
            try:
                log_type_enum = LogType(log_type.lower())
                logs = generator.generate_logs(
                    log_type=log_type_enum,
                    count=count,
                    time_range=time_range
                )
            except ValueError:
                return f"Error: Unsupported log type '{log_type}'. Supported types: ids, web_access, endpoint, windows_event, linux_syslog, firewall"
            
            # Convert to dictionary format
            logs_data = []
            for log in logs:
                log_dict = log.dict() if hasattr(log, 'dict') else log
                logs_data.append(log_dict)
            
            # Ingest to VictoriaLogs if requested
            if ingest and destination == "victorialogs":
                success = ingest_logs_to_victorialogs(logs_data)
                if success:
                    logger.info(f"Successfully ingested {len(logs_data)} logs to VictoriaLogs")
                else:
                    logger.warning("Failed to ingest some logs to VictoriaLogs")
            
            result = {
                "success": True,
                "log_type": log_type,
                "count": len(logs_data),
                "time_range": time_range,
                "ingested": ingest and destination == "victorialogs",
                "logs": logs_data
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating logs: {str(e)}")
            return f"Error generating logs: {str(e)}"
    
    @server.tool()
    def generate_attack_campaign(threat_actor: str, duration: str = "24h", target_count: int = 50) -> str:
        """Generate a coordinated attack campaign.
        
        This tool generates realistic attack campaigns with threat actor attribution, coordinated attacks across multiple log types, and campaign objectives.
        
        Args:
            threat_actor: Threat actor to simulate. Supported actors:
                - "APT29": Cozy Bear - Russian state-sponsored group
                - "APT28": Fancy Bear - Russian state-sponsored group  
                - "Lazarus": North Korean state-sponsored group
                - "FIN7": Financially motivated cybercriminal group
                - "UNC2452": SolarWinds attack group
                - "Wizard Spider": TrickBot/Conti ransomware group
                - "Ryuk": Ransomware group
                - "Conti": Ransomware group
                - "Maze": Ransomware group
            duration: Duration of the campaign (default: "24h", examples: "1h", "24h", "72h", "7d")
            target_count: Number of target events to generate (default: 50, max: 1000)
        
        Returns:
            JSON string containing the attack campaign with coordinated events, threat actor attribution, and campaign objectives.
            
        Examples:
            - "Generate APT29 attack campaign" → generate_attack_campaign("APT29", "72h", 100)
            - "Create Lazarus campaign for 7 days" → generate_attack_campaign("Lazarus", "7d", 200)
            - "Generate FIN7 campaign with 50 events" → generate_attack_campaign("FIN7", "24h", 50)
        """
        try:
            logger.info(f"Generating {threat_actor} attack campaign for {duration} with {target_count} events")
            
            # Generate attack campaign
            campaign = generator.generate_attack_campaign(
                threat_actor=threat_actor,
                duration=duration,
                target_count=target_count
            )
            
            # Convert to dictionary format
            campaign_data = {
                "campaign_id": campaign.campaign_id,
                "threat_actor": campaign.threat_actor,
                "duration": campaign.duration,
                "start_time": campaign.start_time,
                "end_time": campaign.end_time,
                "target_count": len(campaign.events),
                "events": [event.dict() if hasattr(event, 'dict') else event for event in campaign.events]
            }
            
            result = {
                "success": True,
                "campaign": campaign_data,
                "summary": {
                    "threat_actor": threat_actor,
                    "duration": duration,
                    "total_events": len(campaign.events),
                    "campaign_id": campaign.campaign_id
                }
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating attack campaign: {str(e)}")
            return f"Error generating attack campaign: {str(e)}"
    
    @server.tool()
    def generate_correlated_events(log_types: str, count: int = 100, correlation_strength: float = 0.7) -> str:
        """Generate correlated events across multiple log types.
        
        This tool generates correlated security events that span multiple log types, simulating realistic attack scenarios where events in one system trigger events in another.
        
        Args:
            log_types: Comma-separated list of log types (e.g., "ids,firewall,web_access")
            count: Number of events to generate (default: 100, max: 1000)
            correlation_strength: Strength of correlation between events (0.0-1.0, default: 0.7)
                - 0.0: No correlation (random events)
                - 0.5: Moderate correlation (some related events)
                - 0.7: Strong correlation (many related events)
                - 1.0: Perfect correlation (all events related)
        
        Returns:
            JSON string containing correlated events with correlation IDs, cross-log relationships, and attack patterns.
        
        Examples:
            - "Generate correlated IDS and firewall events" → generate_correlated_events("ids,firewall", 100, 0.8)
            - "Create correlated events across 3 log types" → generate_correlated_events("ids,web_access,endpoint", 200, 0.6)
            - "Generate highly correlated events" → generate_correlated_events("ids,firewall,web_access", 150, 0.9)
        """
        try:
            logger.info(f"Generating {count} correlated events for {log_types} with correlation strength {correlation_strength}")
            
            # Parse log types
            log_type_list = [lt.strip() for lt in log_types.split(",")]
            
            # Generate correlated events
            correlated_events = generator.generate_correlated_events(
                log_types=log_type_list,
                count=count,
                correlation_strength=correlation_strength
            )
            
            # Convert to dictionary format
            events_data = []
            correlation_groups = {}
            
            for event in correlated_events:
                event_dict = event.dict() if hasattr(event, 'dict') else event
                events_data.append(event_dict)
                
                # Group by correlation ID
                if hasattr(event, 'correlation_id') and event.correlation_id:
                    if event.correlation_id not in correlation_groups:
                        correlation_groups[event.correlation_id] = []
                    correlation_groups[event.correlation_id].append(event_dict)
            
            result = {
                "success": True,
                "log_types": log_type_list,
                "count": len(events_data),
                "correlation_strength": correlation_strength,
                "correlation_groups": len(correlation_groups),
                "events": events_data,
                "correlation_analysis": {
                    "total_groups": len(correlation_groups),
                    "average_group_size": len(events_data) / len(correlation_groups) if correlation_groups else 0
                }
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating correlated events: {str(e)}")
            return f"Error generating correlated events: {str(e)}"
    
    # Enhanced 24-Pillar Tools
    @server.tool()
    def generate_pillar_logs(pillar: str, count: int = 100, time_range: str = "24h", 
                           ingest: bool = False, destination: str = "file") -> str:
        """Generate logs for a specific cyberdefense pillar with realistic attack patterns.
        
        This tool generates logs for any of the 24 cyberdefense pillars with pillar-specific
        attack patterns, threat indicators, and mitigation controls.
        
        Args:
            pillar: Cyberdefense pillar name. Supported pillars:
                - "vendor_risk": Vendor risk management logs
                - "api_security": API security logs with authentication and authorization
                - "endpoint_security": Endpoint detection and response logs
                - "authentication": Authentication logs with login attempts and failures
                - "authorization": Authorization logs with permission changes
                - "application_security": Application security logs with vulnerabilities
                - "audit_compliance": Audit and compliance logs
                - "cloud_security": Cloud platform security logs
                - "container_security": Container and orchestration security logs
                - "data_privacy": Data privacy and protection logs
                - "data_protection": Data protection and encryption logs
                - "detection_correlation": Detection and correlation logs
                - "disaster_recovery": Disaster recovery and backup logs
                - "due_diligence": Due diligence and assessment logs
                - "encryption": Encryption and key management logs
                - "ai_security": AI and machine learning security logs
                - "governance_risk": Governance and risk management logs
                - "identity_governance": Identity governance logs
                - "incident_response": Incident response and forensics logs
                - "network_security": Network security and firewall logs
                - "ot_physical_security": OT and physical security logs
                - "security_awareness": Security awareness and training logs
                - "threat_intelligence": Threat intelligence and IOCs
                - "vulnerability_management": Vulnerability management logs
                - "siem_logs": SIEM priority logs across all categories
            count: Number of log entries to generate (default: 100, max: 10000)
            time_range: Time range for events (default: "24h", examples: "1h", "24h", "7d")
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
            destination: Destination for logs - "file" or "victorialogs" (default: "file")
        
        Returns:
            JSON string containing generated log events with pillar-specific attack patterns,
            threat indicators, and mitigation controls.
        
        Examples:
            - "Generate 100 vendor risk logs" → generate_pillar_logs("vendor_risk", 100)
            - "Create 200 API security logs for 7 days" → generate_pillar_logs("api_security", 200, "7d")
            - "Generate 500 endpoint security logs and ingest to VictoriaLogs" → generate_pillar_logs("endpoint_security", 500, "24h", ingest=True, destination="victorialogs")
            - "Generate SIEM priority logs" → generate_pillar_logs("siem_logs", 1000, "24h")
        """
        try:
            logger.info(f"Generating {count} logs for pillar: {pillar}")
            
            # Convert string to enum
            try:
                pillar_enum = CyberdefensePillar(pillar)
            except ValueError:
                return f"Error: Invalid pillar '{pillar}'. Use get_supported_pillars() to see all supported pillars."
            
            # Generate logs using enhanced generator
            logs = enhanced_generator.generate_logs(
                pillar=pillar_enum,
                count=count,
                time_range=time_range
            )
            
            # Convert to dictionary format
            logs_data = []
            for log in logs:
                log_dict = log.dict() if hasattr(log, 'dict') else log
                logs_data.append(log_dict)
            
            # Ingest to VictoriaLogs if requested
            if ingest and destination == "victorialogs":
                success = ingest_logs_to_victorialogs(logs_data)
                if success:
                    logger.info(f"Successfully ingested {len(logs_data)} logs to VictoriaLogs")
                else:
                    logger.warning("Failed to ingest some logs to VictoriaLogs")
            
            result = {
                "success": True,
                "pillar": pillar,
                "count": len(logs_data),
                "time_range": time_range,
                "ingested": ingest and destination == "victorialogs",
                "logs": logs_data
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating pillar logs: {str(e)}")
            return f"Error generating pillar logs: {str(e)}"

    @server.tool()
    def generate_campaign_logs(threat_actor: str, duration: str = "24h", 
                             target_count: int = 50, ingest: bool = False) -> str:
        """Generate coordinated attack campaign logs across multiple cyberdefense pillars.
        
        This tool generates realistic attack campaigns with threat actor attribution,
        coordinated attacks across multiple pillars, and campaign objectives.
        
        Args:
            threat_actor: Threat actor name. Supported actors:
                - "APT29": Cozy Bear - Russian state-sponsored group
                - "APT28": Fancy Bear - Russian state-sponsored group
                - "Lazarus": North Korean state-sponsored group
                - "FIN7": Financially motivated cybercriminal group
                - "UNC2452": SolarWinds attack group
                - "Wizard Spider": TrickBot/Conti ransomware group
                - "Ryuk": Ransomware group
                - "Conti": Ransomware group
                - "Maze": Ransomware group
            duration: Campaign duration (default: "24h", examples: "1h", "24h", "72h", "7d")
            target_count: Number of target events to generate (default: 50, max: 1000)
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
        
        Returns:
            JSON string containing the attack campaign with coordinated events,
            threat actor attribution, and campaign objectives.
        
        Examples:
            - "Generate APT29 campaign across all pillars" → generate_campaign_logs("APT29", "72h", 100)
            - "Create Lazarus campaign and ingest to VictoriaLogs" → generate_campaign_logs("Lazarus", "24h", 50, ingest=True)
            - "Generate 7-day APT28 campaign" → generate_campaign_logs("APT28", "7d", 200)
        """
        try:
            logger.info(f"Generating {threat_actor} campaign for {duration} with {target_count} events")
            
            # Generate campaign using enhanced generator
            campaign = enhanced_generator.generate_campaign(
                threat_actor=ThreatActor(threat_actor),
                duration=duration,
                target_count=target_count
            )
            
            # Convert to dictionary format
            campaign_data = {
                "campaign_id": campaign.campaign_id,
                "threat_actor": campaign.threat_actor,
                "duration": campaign.duration,
                "start_time": campaign.start_time,
                "end_time": campaign.end_time,
                "target_count": len(campaign.events),
                "events": [event.dict() if hasattr(event, 'dict') else event for event in campaign.events]
            }
            
            # Ingest to VictoriaLogs if requested
            if ingest:
                success = ingest_logs_to_victorialogs([event.dict() if hasattr(event, 'dict') else event for event in campaign.events])
                if success:
                    logger.info(f"Successfully ingested {len(campaign.events)} campaign events to VictoriaLogs")
                else:
                    logger.warning("Failed to ingest some campaign events to VictoriaLogs")
            
            result = {
                "success": True,
                "campaign": campaign_data,
                "summary": {
                    "threat_actor": threat_actor,
                    "duration": duration,
                    "total_events": len(campaign.events),
                    "campaign_id": campaign.campaign_id,
                    "ingested": ingest
                }
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating campaign logs: {str(e)}")
            return f"Error generating campaign logs: {str(e)}"

    @server.tool()
    def generate_correlated_logs(log_types: str, count: int = 100, 
                               correlation_strength: float = 0.7, ingest: bool = False) -> str:
        """Generate correlated events across multiple cyberdefense pillars.
        
        This tool generates correlated security events that span multiple pillars,
        simulating realistic attack chains and coordinated threats.
        
        Args:
            log_types: Comma-separated list of pillar names (e.g., "authentication,network_security,endpoint_security")
            count: Number of events to generate (default: 100, max: 1000)
            correlation_strength: Strength of correlation between events (0.0-1.0, default: 0.7)
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
        
        Returns:
            JSON string containing correlated events with correlation IDs,
            cross-pillar attack patterns, and coordinated threat indicators.
        
        Examples:
            - "Generate correlated authentication and network security events" → generate_correlated_logs("authentication,network_security", 100, 0.8)
            - "Create correlated events across 3 pillars" → generate_correlated_logs("vendor_risk,api_security,endpoint_security", 200, 0.6)
            - "Generate highly correlated events and ingest to VictoriaLogs" → generate_correlated_logs("authentication,authorization,data_protection", 150, 0.9, ingest=True)
        """
        try:
            logger.info(f"Generating {count} correlated logs for {log_types} with correlation strength {correlation_strength}")
            
            # Parse log types
            log_type_list = [lt.strip() for lt in log_types.split(",")]
            
            # Generate correlated logs using enhanced generator
            correlated_logs = enhanced_generator.generate_correlated_logs(
                log_types=log_type_list,
                count=count,
                correlation_strength=correlation_strength
            )
            
            # Convert to dictionary format
            logs_data = []
            correlation_groups = {}
            
            for log in correlated_logs:
                log_dict = log.dict() if hasattr(log, 'dict') else log
                logs_data.append(log_dict)
                
                # Group by correlation ID
                if hasattr(log, 'correlation_id') and log.correlation_id:
                    if log.correlation_id not in correlation_groups:
                        correlation_groups[log.correlation_id] = []
                    correlation_groups[log.correlation_id].append(log_dict)
            
            # Ingest to VictoriaLogs if requested
            if ingest:
                success = ingest_logs_to_victorialogs(logs_data)
                if success:
                    logger.info(f"Successfully ingested {len(logs_data)} correlated logs to VictoriaLogs")
                else:
                    logger.warning("Failed to ingest some correlated logs to VictoriaLogs")
            
            result = {
                "success": True,
                "log_types": log_type_list,
                "count": len(logs_data),
                "correlation_strength": correlation_strength,
                "correlation_groups": len(correlation_groups),
                "ingested": ingest,
                "logs": logs_data,
                "correlation_analysis": {
                    "total_groups": len(correlation_groups),
                    "average_group_size": len(logs_data) / len(correlation_groups) if correlation_groups else 0
                }
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating correlated logs: {str(e)}")
            return f"Error generating correlated logs: {str(e)}"

    # SIEM Priority Logs Tools
    @server.tool()
    def generate_siem_priority_logs(category: str, count: int = 100, time_range: str = "24h", 
                                  ingest: bool = False, destination: str = "file") -> str:
        """Generate SIEM priority logs for specific categories.
        
        This tool generates logs for the 13 SIEM priority categories as defined in the
        National Cyber Security Agency guidance document.
        
        Args:
            category: SIEM category. Supported categories:
                - "edr": Endpoint Detection and Response logs (20% distribution)
                - "network": Network device logs - firewall, router, IDS/IPS (15.5% distribution)
                - "ad": Active Directory and Domain Service Security logs (11.4% distribution)
                - "windows": Microsoft Windows endpoint logs (10.1% distribution)
                - "cloud": Cloud platform logs - AWS, Azure, GCP, Office 365 (8% distribution)
                - "linux": Linux endpoint auditing logs (7.3% distribution)
                - "container": Container and orchestration logs (5.7% distribution)
                - "database": Database access and query logs (5.1% distribution)
                - "dns": DNS server logs (4.6% distribution)
                - "mobile": Mobile device management logs (4.6% distribution)
                - "macos": Apple macOS endpoint logs (4.7% distribution)
                - "virtualization": Virtualization system logs (1.2% distribution)
                - "ot": Operational technology logs (1.3% distribution)
                - "all": Generate logs across all categories with realistic distribution
            count: Number of log entries to generate (default: 100, max: 10000)
            time_range: Time range for events (default: "24h", examples: "1h", "24h", "7d")
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
            destination: Destination for logs - "file" or "victorialogs" (default: "file")
        
        Returns:
            JSON string containing generated SIEM priority log events with realistic patterns,
            attack indicators, and security context.
        
        Examples:
            - "Generate 100 EDR logs" → generate_siem_priority_logs("edr", 100)
            - "Create 200 Active Directory logs for 7 days" → generate_siem_priority_logs("ad", 200, "7d")
            - "Generate 500 network device logs and ingest to VictoriaLogs" → generate_siem_priority_logs("network", 500, "24h", ingest=True, destination="victorialogs")
            - "Generate comprehensive SIEM logs across all categories" → generate_siem_priority_logs("all", 1000, "24h")
        """
        try:
            logger.info(f"Generating {count} SIEM priority logs for category: {category}")
            
            # Generate SIEM logs using enhanced generator
            siem_logs = enhanced_generator.generate_logs(
                pillar=CyberdefensePillar.SIEM_LOGS,
                count=count,
                time_range=time_range
            )
            
            # Filter by category if specified
            if category.lower() != "all":
                filtered_logs = []
                for log in siem_logs:
                    if category.lower() in log.tags or category.lower() in log.log_type:
                        filtered_logs.append(log)
                siem_logs = filtered_logs
            
            # Convert to dictionary format
            logs_data = []
            for log in siem_logs:
                log_dict = log.dict() if hasattr(log, 'dict') else log
                logs_data.append(log_dict)
            
            # Ingest to VictoriaLogs if requested
            if ingest and destination == "victorialogs":
                success = ingest_logs_to_victorialogs(logs_data)
                if success:
                    logger.info(f"Successfully ingested {len(logs_data)} SIEM logs to VictoriaLogs")
                else:
                    logger.warning("Failed to ingest some logs to VictoriaLogs")
            
            result = {
                "success": True,
                "category": category,
                "count": len(logs_data),
                "time_range": time_range,
                "ingested": ingest and destination == "victorialogs",
                "logs": logs_data
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating SIEM priority logs: {str(e)}")
            return f"Error generating SIEM priority logs: {str(e)}"

    @server.tool()
    def get_siem_categories() -> str:
        """Get list of all 13 SIEM priority categories.
        
        This tool returns comprehensive information about all SIEM priority categories
        as defined in the National Cyber Security Agency guidance document.
        
        Returns:
            JSON string containing all supported SIEM categories with their descriptions,
            log sources, attack patterns, and priority levels.
            
        Examples:
            - "What SIEM categories are supported?" → get_siem_categories()
            - "Show me all available SIEM log types" → get_siem_categories()
        """
        try:
            categories = {
                "edr": {
                    "name": "Endpoint Detection and Response (EDR) Logs",
                    "description": "EDR logs including antivirus detection, process creation, file access, network connections, registry modifications, and scheduled tasks",
                    "priority": "High",
                    "distribution": "20%",
                    "log_sources": ["antivirus_logs", "edr_logs", "endpoint_security"],
                    "attack_patterns": ["malware_detection", "process_injection", "file_quarantine", "network_anomaly"],
                    "examples": ["Malware detected: trojan.exe", "Process created: suspicious.exe", "File quarantined: malware.zip"]
                },
                "network": {
                    "name": "Network Device Logs",
                    "description": "Firewall, router, switch, IDS/IPS, proxy, and VPN logs with traffic patterns and security events",
                    "priority": "High",
                    "distribution": "15.5%",
                    "log_sources": ["firewall_logs", "ids_logs", "network_logs", "proxy_logs"],
                    "attack_patterns": ["intrusion_detection", "traffic_anomaly", "port_scan", "brute_force"],
                    "examples": ["Firewall DROP: 192.168.1.100 -> 10.0.0.1 port 22", "IDS Alert: Port scan detected", "VPN connection: user@domain.com"]
                },
                "ad": {
                    "name": "Active Directory and Domain Service Security Logs",
                    "description": "AD authentication, authorization, account management, and Kerberos logs with privilege escalation detection",
                    "priority": "Critical",
                    "distribution": "11.4%",
                    "log_sources": ["ad_logs", "domain_controller_logs", "security_logs"],
                    "attack_patterns": ["privilege_escalation", "dcsync", "golden_ticket", "pass_the_hash"],
                    "examples": ["Failed logon: user@domain.com from 192.168.1.100", "DCSync detected: unauthorized replication", "Privilege escalation: user added to Domain Admins"]
                },
                "windows": {
                    "name": "Microsoft Windows Endpoint Logs",
                    "description": "Windows security, system, application, Sysmon, PowerShell, and WMI logs with persistence and lateral movement detection",
                    "priority": "High",
                    "distribution": "10.1%",
                    "log_sources": ["windows_event_logs", "sysmon_logs", "powershell_logs"],
                    "attack_patterns": ["persistence", "lateral_movement", "credential_access", "defense_evasion"],
                    "examples": ["Scheduled task created: suspicious_task", "PowerShell script executed: malicious.ps1", "Registry modified: Run key"]
                },
                "cloud": {
                    "name": "Cloud Platform Logs",
                    "description": "AWS, Azure, GCP, and Office 365 audit and activity logs with privilege escalation and data exfiltration detection",
                    "priority": "High",
                    "distribution": "8%",
                    "log_sources": ["cloud_audit_logs", "azure_logs", "aws_cloudtrail", "office365_logs"],
                    "attack_patterns": ["privilege_escalation", "data_exfiltration", "misconfiguration", "unauthorized_access"],
                    "examples": ["AWS S3 bucket accessed: sensitive-data", "Azure AD login: user@domain.com", "Office 365 email sent: suspicious attachment"]
                },
                "container": {
                    "name": "Container and Orchestration Logs",
                    "description": "Docker, Kubernetes, and container orchestration logs with container escape and privilege escalation detection",
                    "priority": "Medium",
                    "distribution": "5.7%",
                    "log_sources": ["container_logs", "kubernetes_logs", "docker_logs"],
                    "attack_patterns": ["container_escape", "privilege_escalation", "image_tampering", "runtime_anomaly"],
                    "examples": ["Container started: suspicious-image:latest", "Pod created: malicious-pod", "Image pulled: vulnerable-image:v1.0"]
                },
                "database": {
                    "name": "Database Logs",
                    "description": "Database access, query, and administrative logs with SQL injection and privilege escalation detection",
                    "priority": "Medium",
                    "distribution": "5.1%",
                    "log_sources": ["database_logs", "sql_logs", "audit_logs"],
                    "attack_patterns": ["sql_injection", "privilege_escalation", "data_exfiltration", "unauthorized_access"],
                    "examples": ["Database query: SELECT * FROM users", "Privilege escalation: user granted admin rights", "Data export: sensitive table accessed"]
                },
                "mobile": {
                    "name": "Mobile Device Management Logs",
                    "description": "MDM, mobile device enrollment, app management, and compliance logs with jailbreak and malicious app detection",
                    "priority": "Medium",
                    "distribution": "4.6%",
                    "log_sources": ["mdm_logs", "mobile_security_logs", "device_logs"],
                    "attack_patterns": ["jailbreak_detection", "malicious_app", "data_exfiltration", "policy_violation"],
                    "examples": ["Device enrolled: iPhone 14 Pro", "App installed: suspicious-app", "Jailbreak detected: device compromised"]
                },
                "dns": {
                    "name": "DNS Server Logs",
                    "description": "DNS query, response, zone transfer, and cache logs with DNS tunneling and C2 communication detection",
                    "priority": "Medium",
                    "distribution": "4.6%",
                    "log_sources": ["dns_logs", "network_logs", "infrastructure_logs"],
                    "attack_patterns": ["dns_tunneling", "domain_generation", "c2_communication", "data_exfiltration"],
                    "examples": ["DNS query: malicious-domain.com", "Zone transfer: unauthorized access", "DNS tunneling: data exfiltration detected"]
                },
                "linux": {
                    "name": "Linux Endpoint Auditing Logs",
                    "description": "Linux audit, system, and security logs with privilege escalation and lateral movement detection",
                    "priority": "High",
                    "distribution": "7.3%",
                    "log_sources": ["linux_audit_logs", "syslog", "security_logs"],
                    "attack_patterns": ["privilege_escalation", "lateral_movement", "persistence", "defense_evasion"],
                    "examples": ["Sudo command: user executed root command", "SSH connection: user@192.168.1.100", "File access: sensitive file accessed"]
                },
                "macos": {
                    "name": "Apple macOS Endpoint Logs",
                    "description": "macOS system, security, and application logs with persistence and privilege escalation detection",
                    "priority": "Medium",
                    "distribution": "4.7%",
                    "log_sources": ["macos_logs", "unified_logs", "security_logs"],
                    "attack_patterns": ["persistence", "privilege_escalation", "defense_evasion", "credential_access"],
                    "examples": ["Application launched: suspicious.app", "Gatekeeper blocked: unsigned application", "XProtect detected: malware"]
                },
                "virtualization": {
                    "name": "Virtualization System Logs",
                    "description": "VMware, Hyper-V, and virtualization platform logs with VM escape and hypervisor attack detection",
                    "priority": "Medium",
                    "distribution": "1.2%",
                    "log_sources": ["virtualization_logs", "hypervisor_logs", "vm_logs"],
                    "attack_patterns": ["vm_escape", "hypervisor_attack", "resource_abuse", "lateral_movement"],
                    "examples": ["VM created: suspicious-vm", "VM escape detected: container breakout", "Hypervisor attack: privilege escalation"]
                },
                "ot": {
                    "name": "Operational Technology Logs",
                    "description": "ICS, SCADA, and industrial control system logs with industrial malware and protocol anomaly detection",
                    "priority": "High",
                    "distribution": "1.3%",
                    "log_sources": ["ot_logs", "ics_logs", "scada_logs"],
                    "attack_patterns": ["industrial_malware", "protocol_anomaly", "safety_system_bypass", "process_disruption"],
                    "examples": ["SCADA alert: process anomaly detected", "Industrial malware: Stuxnet variant", "Safety system bypass: unauthorized access"]
                }
            }
            
            result = {
                "success": True,
                "categories": categories,
                "total_categories": len(categories),
                "description": "SIEM Priority Logs covering all 13 categories from National Cyber Security Agency guidance",
                "usage_examples": [
                    "generate_siem_priority_logs('edr', 100) - Generate 100 EDR logs",
                    "generate_siem_priority_logs('ad', 200, '7d') - Generate 200 Active Directory logs for 7 days",
                    "generate_siem_priority_logs('all', 1000) - Generate 1000 logs across all categories"
                ]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting SIEM categories: {str(e)}")
            return f"Error getting SIEM categories: {str(e)}"

    @server.tool()
    def generate_comprehensive_siem_logs(count: int = 1000, time_range: str = "24h", 
                                       ingest: bool = False, destination: str = "file") -> str:
        """Generate comprehensive SIEM logs across all 13 priority categories.
        
        This tool generates a realistic mix of SIEM priority logs across all categories
        with proper distribution and correlation patterns.
        
        Args:
            count: Total number of log entries to generate (default: 1000, max: 50000)
            time_range: Time range for events (default: "24h", examples: "1h", "24h", "7d")
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
            destination: Destination for logs - "file" or "victorialogs" (default: "file")
        
        Returns:
            JSON string containing comprehensive SIEM logs with realistic distribution
            across all 13 priority categories.
        
        Examples:
            - "Generate 1000 comprehensive SIEM logs" → generate_comprehensive_siem_logs(1000)
            - "Create 500 SIEM logs for 7 days and ingest to VictoriaLogs" → generate_comprehensive_siem_logs(500, "7d", ingest=True)
            - "Generate 2000 SIEM logs across all categories" → generate_comprehensive_siem_logs(2000)
        """
        try:
            logger.info(f"Generating {count} comprehensive SIEM logs across all categories")
            
            # Generate comprehensive SIEM logs
            siem_logs = enhanced_generator.generate_logs(
                pillar=CyberdefensePillar.SIEM_LOGS,
                count=count,
                time_range=time_range
            )
            
            # Convert to dictionary format
            logs_data = []
            category_counts = {}
            
            for log in siem_logs:
                log_dict = log.dict() if hasattr(log, 'dict') else log
                logs_data.append(log_dict)
                
                # Count by category
                for tag in log.tags:
                    if tag in ['edr', 'network', 'ad', 'windows', 'cloud', 'container', 'database', 'mobile', 'dns', 'linux', 'macos', 'virtualization', 'ot']:
                        category_counts[tag] = category_counts.get(tag, 0) + 1
                        break
            
            # Ingest to VictoriaLogs if requested
            if ingest and destination == "victorialogs":
                success = ingest_logs_to_victorialogs(logs_data)
                if success:
                    logger.info(f"Successfully ingested {len(logs_data)} comprehensive SIEM logs to VictoriaLogs")
                else:
                    logger.warning("Failed to ingest some logs to VictoriaLogs")
            
            result = {
                "success": True,
                "total_logs": len(logs_data),
                "time_range": time_range,
                "ingested": ingest and destination == "victorialogs",
                "category_distribution": category_counts,
                "logs": logs_data
            }
            
            return json.dumps(result, cls=DateTimeEncoder, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating comprehensive SIEM logs: {str(e)}")
            return f"Error generating comprehensive SIEM logs: {str(e)}"

    # Information and Analysis Tools
    @server.tool()
    def get_supported_log_types() -> str:
        """Get list of supported log types.
        
        This tool returns all supported log types with their descriptions and use cases.
        
        Returns:
            JSON string containing supported log types with descriptions and examples.
        
        Examples:
            - "What log types are supported?" → get_supported_log_types()
            - "Show me all available log types" → get_supported_log_types()
        """
        try:
            log_types = {
                "ids": {
                    "name": "Intrusion Detection System",
                    "description": "IDS logs with attack patterns, signatures, and security events",
                    "use_cases": ["Threat detection", "Attack analysis", "Security monitoring"],
                    "examples": ["Port scan detected", "SQL injection attempt", "Brute force attack"]
                },
                "web_access": {
                    "name": "Web Application Access",
                    "description": "Web server access logs with HTTP requests, responses, and security events",
                    "use_cases": ["Web security monitoring", "Access pattern analysis", "Attack detection"],
                    "examples": ["GET /admin/login HTTP/1.1 200", "POST /api/data HTTP/1.1 403", "Suspicious user agent detected"]
                },
                "endpoint": {
                    "name": "Endpoint Detection and Response",
                    "description": "EDR logs with process creation, file access, and malware detection",
                    "use_cases": ["Endpoint security", "Malware detection", "Process monitoring"],
                    "examples": ["Process created: suspicious.exe", "File quarantined: malware.zip", "Registry modified: Run key"]
                },
                "windows_event": {
                    "name": "Windows Event Logs",
                    "description": "Windows security, system, and application event logs",
                    "use_cases": ["Windows security monitoring", "System event analysis", "Audit trail"],
                    "examples": ["Event ID 4624: Successful logon", "Event ID 4625: Failed logon", "Event ID 4688: Process creation"]
                },
                "linux_syslog": {
                    "name": "Linux Syslog",
                    "description": "Linux system logs with authentication, system events, and security events",
                    "use_cases": ["Linux security monitoring", "System event analysis", "Audit trail"],
                    "examples": ["SSH login: user@192.168.1.100", "Sudo command executed", "File access: /etc/passwd"]
                },
                "firewall": {
                    "name": "Firewall Logs",
                    "description": "Firewall logs with traffic patterns, blocked connections, and security events",
                    "use_cases": ["Network security", "Traffic analysis", "Attack detection"],
                    "examples": ["Firewall DROP: 192.168.1.100 -> 10.0.0.1 port 22", "Firewall ALLOW: 192.168.1.100 -> 10.0.0.1 port 80", "Port scan detected"]
                }
            }
            
            result = {
                "success": True,
                "log_types": log_types,
                "total_types": len(log_types),
                "description": "Supported log types for cybersecurity log generation"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting supported log types: {str(e)}")
            return f"Error getting supported log types: {str(e)}"

    @server.tool()
    def get_supported_pillars() -> str:
        """Get list of all 24 supported cyberdefense pillars.
        
        This tool returns comprehensive information about all 24 cyberdefense pillars
        with their descriptions, attack patterns, and use cases.
        
        Returns:
            JSON string containing all supported cyberdefense pillars with their descriptions,
            attack patterns, and use cases.
            
        Examples:
            - "What pillars are supported?" → get_supported_pillars()
            - "Show me all available pillars" → get_supported_pillars()
        """
        try:
            pillars = {
                "vendor_risk": {
                    "name": "Vendor Risk Management",
                    "description": "Vendor risk assessment, third-party security, and supply chain security logs",
                    "attack_patterns": ["supply_chain_attack", "third_party_breach", "vendor_compromise"],
                    "use_cases": ["Vendor security monitoring", "Supply chain risk assessment", "Third-party compliance"]
                },
                "api_security": {
                    "name": "API Security",
                    "description": "API authentication, authorization, and security logs with OAuth, JWT, and API abuse detection",
                    "attack_patterns": ["api_abuse", "oauth_attack", "jwt_manipulation", "rate_limiting_bypass"],
                    "use_cases": ["API security monitoring", "Authentication analysis", "Authorization tracking"]
                },
                "endpoint_security": {
                    "name": "Endpoint Security",
                    "description": "Endpoint detection and response logs with malware detection, process monitoring, and file analysis",
                    "attack_patterns": ["malware_detection", "process_injection", "file_quarantine", "lateral_movement"],
                    "use_cases": ["Endpoint protection", "Malware analysis", "Process monitoring"]
                },
                "authentication": {
                    "name": "Authentication",
                    "description": "Authentication logs with login attempts, MFA, and credential validation",
                    "attack_patterns": ["brute_force", "credential_stuffing", "mfa_bypass", "session_hijacking"],
                    "use_cases": ["Authentication monitoring", "Login analysis", "Credential security"]
                },
                "authorization": {
                    "name": "Authorization",
                    "description": "Authorization logs with permission changes, role assignments, and access control",
                    "attack_patterns": ["privilege_escalation", "role_manipulation", "access_abuse", "permission_creep"],
                    "use_cases": ["Authorization monitoring", "Permission analysis", "Access control"]
                },
                "application_security": {
                    "name": "Application Security",
                    "description": "Application security logs with vulnerability detection, code analysis, and security testing",
                    "attack_patterns": ["sql_injection", "xss_attack", "csrf_attack", "code_injection"],
                    "use_cases": ["Application security", "Vulnerability management", "Code security"]
                },
                "audit_compliance": {
                    "name": "Audit and Compliance",
                    "description": "Audit and compliance logs with regulatory requirements, compliance monitoring, and audit trails",
                    "attack_patterns": ["compliance_violation", "audit_tampering", "regulatory_breach"],
                    "use_cases": ["Compliance monitoring", "Audit trail analysis", "Regulatory reporting"]
                },
                "cloud_security": {
                    "name": "Cloud Security",
                    "description": "Cloud platform security logs with AWS, Azure, GCP, and Office 365 security events",
                    "attack_patterns": ["cloud_privilege_escalation", "data_exfiltration", "misconfiguration", "unauthorized_access"],
                    "use_cases": ["Cloud security monitoring", "Cloud compliance", "Cloud threat detection"]
                },
                "container_security": {
                    "name": "Container Security",
                    "description": "Container and orchestration security logs with Docker, Kubernetes, and container security events",
                    "attack_patterns": ["container_escape", "image_tampering", "orchestration_attack", "runtime_anomaly"],
                    "use_cases": ["Container security", "Orchestration monitoring", "Container compliance"]
                },
                "data_privacy": {
                    "name": "Data Privacy",
                    "description": "Data privacy logs with GDPR, CCPA, and privacy regulation compliance",
                    "attack_patterns": ["data_breach", "privacy_violation", "unauthorized_access", "data_leakage"],
                    "use_cases": ["Privacy compliance", "Data protection", "Privacy monitoring"]
                },
                "data_protection": {
                    "name": "Data Protection",
                    "description": "Data protection logs with encryption, data loss prevention, and data security events",
                    "attack_patterns": ["data_exfiltration", "encryption_bypass", "dlp_violation", "data_theft"],
                    "use_cases": ["Data protection", "Encryption monitoring", "Data loss prevention"]
                },
                "detection_correlation": {
                    "name": "Detection and Correlation",
                    "description": "Detection and correlation logs with SIEM, SOAR, and security orchestration events",
                    "attack_patterns": ["correlation_attack", "detection_bypass", "orchestration_abuse"],
                    "use_cases": ["Security orchestration", "Threat correlation", "Detection analysis"]
                },
                "disaster_recovery": {
                    "name": "Disaster Recovery",
                    "description": "Disaster recovery logs with backup, recovery, and business continuity events",
                    "attack_patterns": ["backup_compromise", "recovery_attack", "business_disruption"],
                    "use_cases": ["Disaster recovery", "Business continuity", "Backup security"]
                },
                "due_diligence": {
                    "name": "Due Diligence",
                    "description": "Due diligence logs with risk assessment, security evaluation, and compliance verification",
                    "attack_patterns": ["assessment_bypass", "compliance_violation", "risk_manipulation"],
                    "use_cases": ["Risk assessment", "Security evaluation", "Compliance verification"]
                },
                "encryption": {
                    "name": "Encryption",
                    "description": "Encryption logs with key management, certificate management, and cryptographic events",
                    "attack_patterns": ["key_compromise", "certificate_attack", "encryption_bypass", "crypto_attack"],
                    "use_cases": ["Encryption monitoring", "Key management", "Certificate security"]
                },
                "ai_security": {
                    "name": "AI Security",
                    "description": "AI and machine learning security logs with model security, data poisoning, and AI attack detection",
                    "attack_patterns": ["model_poisoning", "adversarial_attack", "ai_bypass", "data_poisoning"],
                    "use_cases": ["AI security", "Model protection", "ML security"]
                },
                "governance_risk": {
                    "name": "Governance and Risk",
                    "description": "Governance and risk management logs with risk assessment, governance compliance, and risk monitoring",
                    "attack_patterns": ["governance_violation", "risk_manipulation", "compliance_bypass"],
                    "use_cases": ["Risk management", "Governance compliance", "Risk monitoring"]
                },
                "identity_governance": {
                    "name": "Identity Governance",
                    "description": "Identity governance logs with identity management, access governance, and identity security events",
                    "attack_patterns": ["identity_theft", "access_abuse", "identity_bypass", "governance_violation"],
                    "use_cases": ["Identity management", "Access governance", "Identity security"]
                },
                "incident_response": {
                    "name": "Incident Response",
                    "description": "Incident response logs with security incidents, forensics, and incident management events",
                    "attack_patterns": ["incident_escalation", "forensic_tampering", "response_bypass"],
                    "use_cases": ["Incident management", "Forensic analysis", "Response coordination"]
                },
                "network_security": {
                    "name": "Network Security",
                    "description": "Network security logs with firewall, IDS/IPS, and network monitoring events",
                    "attack_patterns": ["network_intrusion", "traffic_anomaly", "network_bypass", "lateral_movement"],
                    "use_cases": ["Network monitoring", "Traffic analysis", "Network protection"]
                },
                "ot_physical_security": {
                    "name": "OT and Physical Security",
                    "description": "Operational technology and physical security logs with ICS, SCADA, and physical security events",
                    "attack_patterns": ["ot_attack", "physical_breach", "ics_compromise", "safety_bypass"],
                    "use_cases": ["OT security", "Physical security", "ICS protection"]
                },
                "security_awareness": {
                    "name": "Security Awareness",
                    "description": "Security awareness logs with training, phishing simulation, and security education events",
                    "attack_patterns": ["phishing_attack", "social_engineering", "awareness_bypass"],
                    "use_cases": ["Security training", "Phishing simulation", "Security education"]
                },
                "threat_intelligence": {
                    "name": "Threat Intelligence",
                    "description": "Threat intelligence logs with IOCs, threat feeds, and intelligence analysis events",
                    "attack_patterns": ["intelligence_compromise", "feed_manipulation", "ioc_bypass"],
                    "use_cases": ["Threat intelligence", "IOC analysis", "Intelligence sharing"]
                },
                "vulnerability_management": {
                    "name": "Vulnerability Management",
                    "description": "Vulnerability management logs with vulnerability scanning, patch management, and vulnerability assessment events",
                    "attack_patterns": ["vulnerability_exploit", "patch_bypass", "scan_evasion"],
                    "use_cases": ["Vulnerability scanning", "Patch management", "Vulnerability assessment"]
                },
                "siem_logs": {
                    "name": "SIEM Priority Logs",
                    "description": "SIEM priority logs covering all 13 categories from National Cyber Security Agency guidance",
                    "attack_patterns": ["comprehensive_attack", "multi_category_attack", "siem_bypass"],
                    "use_cases": ["SIEM testing", "Security monitoring", "Threat detection"]
                }
            }
            
            result = {
                "success": True,
                "pillars": pillars,
                "total_pillars": len(pillars),
                "description": "All 24 cyberdefense pillars plus SIEM priority logs",
                "usage_examples": [
                    "generate_pillar_logs('authentication', 100) - Generate 100 authentication logs",
                    "generate_pillar_logs('siem_logs', 1000) - Generate 1000 SIEM priority logs",
                    "get_pillar_attack_patterns('endpoint_security') - Get attack patterns for endpoint security"
                ]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting supported pillars: {str(e)}")
            return f"Error getting supported pillars: {str(e)}"

    # Export and Analysis Tools
    @server.tool()
    def export_logs(events_json: str, format: str = "json", output_path: str = "exported_logs") -> str:
        """Export generated logs to files.
        
        This tool exports logs in various formats for analysis, integration, and reporting.
        
        Args:
            events_json: JSON string containing events to export
            format: Export format. Supported formats:
                - "json": JSON format (default)
                - "csv": CSV format for spreadsheet analysis
                - "syslog": Syslog format for log aggregation
                - "cef": Common Event Format for SIEM integration
                - "leef": Log Event Extended Format for SIEM integration
            output_path: Path for output file (default: "exported_logs")
        
        Returns:
            Success message with file path and export statistics.
        
        Examples:
            - "Export logs to JSON" → export_logs(logs_json, "json", "logs.json")
            - "Export logs to CSV" → export_logs(logs_json, "csv", "logs.csv")
            - "Export logs to Syslog" → export_logs(logs_json, "syslog", "logs.syslog")
            - "Export logs to CEF" → export_logs(logs_json, "cef", "logs.cef")
        """
        try:
            # Parse events JSON
            events = json.loads(events_json)
            
            # Create output file path
            if format == "json":
                file_path = f"{output_path}.json"
            elif format == "csv":
                file_path = f"{output_path}.csv"
            elif format == "syslog":
                file_path = f"{output_path}.syslog"
            elif format == "cef":
                file_path = f"{output_path}.cef"
            elif format == "leef":
                file_path = f"{output_path}.leef"
            else:
                return f"Error: Unsupported format '{format}'. Supported formats: json, csv, syslog, cef, leef"
            
            # Export based on format
            if format == "json":
                with open(file_path, 'w') as f:
                    json.dump(events, f, indent=2, cls=DateTimeEncoder)
            elif format == "csv":
                import csv
                with open(file_path, 'w', newline='') as f:
                    if events and len(events) > 0:
                        writer = csv.DictWriter(f, fieldnames=events[0].keys())
                        writer.writeheader()
                        writer.writerows(events)
            elif format == "syslog":
                with open(file_path, 'w') as f:
                    for event in events:
                        timestamp = event.get('timestamp', datetime.now().isoformat())
                        severity = event.get('severity', 'INFO')
                        message = event.get('message', '')
                        f.write(f"{timestamp} {severity} {message}\n")
            elif format == "cef":
                with open(file_path, 'w') as f:
                    for event in events:
                        timestamp = event.get('timestamp', datetime.now().isoformat())
                        severity = event.get('severity', 'INFO')
                        message = event.get('message', '')
                        f.write(f"CEF:0|CybersecurityLogGenerator|1.0|{severity}|{message}|{timestamp}\n")
            elif format == "leef":
                with open(file_path, 'w') as f:
                    for event in events:
                        timestamp = event.get('timestamp', datetime.now().isoformat())
                        severity = event.get('severity', 'INFO')
                        message = event.get('message', '')
                        f.write(f"LEEF:1.0|CybersecurityLogGenerator|1.0|{severity}|{message}|{timestamp}\n")
            
            result = {
                "success": True,
                "format": format,
                "file_path": file_path,
                "event_count": len(events),
                "message": f"Successfully exported {len(events)} events to {file_path}"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting logs: {str(e)}")
            return f"Error exporting logs: {str(e)}"

    @server.tool()
    def analyze_log_patterns(events_json: str, analysis_type: str = "summary") -> str:
        """Analyze log patterns and provide insights.
        
        This tool analyzes generated logs to provide insights into patterns, anomalies, and security events.
        
        Args:
            events_json: JSON string containing events to analyze
            analysis_type: Type of analysis. Supported types:
                - "summary": Basic summary statistics
                - "security": Security-focused analysis with threat detection
                - "performance": Performance analysis with timing and throughput
                - "anomalies": Anomaly detection and outlier analysis
            analysis_type: Type of analysis (summary, security, performance, anomalies) (default: "summary")
            
        Returns:
            JSON string containing analysis results with insights and recommendations.
            
        Examples:
            - "Analyze logs for security patterns" → analyze_log_patterns(logs_json, "security")
            - "Analyze logs for performance" → analyze_log_patterns(logs_json, "performance")
            - "Detect anomalies in logs" → analyze_log_patterns(logs_json, "anomalies")
        """
        try:
            # Parse events JSON
            events = json.loads(events_json)
            
            if not events:
                return json.dumps({"success": False, "error": "No events to analyze"})
            
            # Basic statistics
            total_events = len(events)
            time_range = "Unknown"
            if events:
                timestamps = [event.get('timestamp') for event in events if event.get('timestamp')]
                if timestamps:
                    min_time = min(timestamps)
                    max_time = max(timestamps)
                    time_range = f"{min_time} to {max_time}"
            
            # Analyze based on type
            if analysis_type == "summary":
                # Count by severity
                severity_counts = {}
                for event in events:
                    severity = event.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Count by log type
                log_type_counts = {}
                for event in events:
                    log_type = event.get('log_type', 'unknown')
                    log_type_counts[log_type] = log_type_counts.get(log_type, 0) + 1
                
                analysis = {
                    "total_events": total_events,
                    "time_range": time_range,
                    "severity_distribution": severity_counts,
                    "log_type_distribution": log_type_counts
                }
                
            elif analysis_type == "security":
                # Security analysis
                high_severity_events = [e for e in events if e.get('severity') == 'high' or e.get('severity') == 'critical']
                attack_events = [e for e in events if 'attack' in e.get('message', '').lower() or 'malware' in e.get('message', '').lower()]
                
                analysis = {
                    "total_events": total_events,
                    "high_severity_events": len(high_severity_events),
                    "attack_events": len(attack_events),
                    "security_ratio": len(high_severity_events) / total_events if total_events > 0 else 0,
                    "threat_level": "High" if len(high_severity_events) > total_events * 0.1 else "Medium" if len(high_severity_events) > total_events * 0.05 else "Low"
                }
                
            elif analysis_type == "performance":
                # Performance analysis
                if events:
                    timestamps = [event.get('timestamp') for event in events if event.get('timestamp')]
                    if timestamps:
                        # Calculate events per second
                        time_span = (max(timestamps) - min(timestamps)).total_seconds() if len(timestamps) > 1 else 1
                        events_per_second = total_events / time_span if time_span > 0 else total_events
                    else:
                        events_per_second = 0
                else:
                    events_per_second = 0
                
                analysis = {
                    "total_events": total_events,
                    "events_per_second": events_per_second,
                    "time_range": time_range,
                    "performance_level": "High" if events_per_second > 100 else "Medium" if events_per_second > 10 else "Low"
                }
                
            elif analysis_type == "anomalies":
                # Anomaly detection
                severity_counts = {}
                for event in events:
                    severity = event.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Find anomalies (unusual patterns)
                total_events = len(events)
                anomaly_threshold = 0.1  # 10% threshold
                anomalies = []
                
                for severity, count in severity_counts.items():
                    ratio = count / total_events if total_events > 0 else 0
                    if ratio > anomaly_threshold and severity in ['high', 'critical']:
                        anomalies.append(f"High ratio of {severity} events: {ratio:.2%}")
                
                analysis = {
                    "total_events": total_events,
                    "anomalies_detected": len(anomalies),
                    "anomalies": anomalies,
                    "anomaly_level": "High" if len(anomalies) > 2 else "Medium" if len(anomalies) > 0 else "Low"
                }
            
            else:
                return f"Error: Unsupported analysis type '{analysis_type}'. Supported types: summary, security, performance, anomalies"
            
            result = {
                "success": True,
                "analysis_type": analysis_type,
                "analysis": analysis,
                "recommendations": [
                    "Review high severity events for security threats",
                    "Monitor log patterns for anomalies",
                    "Ensure proper log rotation and storage",
                    "Consider correlation with other data sources"
                ]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing log patterns: {str(e)}")
            return f"Error analyzing log patterns: {str(e)}"

      # Add prompts for cybersecurity log generation
    @server.prompt()
    def generate_security_analysis_prompt(log_type: str, count: int = 100) -> str:
        """Generate a prompt for creating cybersecurity log analysis.
        
        Args:
            log_type: Type of logs to analyze (ids, firewall, web_access, endpoint)
            count: Number of logs to analyze
        """
        return f"""Please analyze {count} {log_type} cybersecurity logs and provide:

1. **Security Summary**: Key security events and their severity levels
2. **Threat Analysis**: Identified attack patterns and threat actors
3. **Risk Assessment**: High-risk events requiring immediate attention
4. **Recommendations**: Specific actions to improve security posture
5. **Trends**: Patterns in attack methods and timing

Focus on actionable insights that security teams can use to strengthen defenses."""

    @server.prompt()
    def create_incident_response_prompt(incident_type: str, severity: str = "high") -> str:
        """Generate a prompt for incident response procedures.
        
        Args:
            incident_type: Type of security incident (malware, intrusion, data_breach, etc.)
            severity: Severity level (low, medium, high, critical)
        """
        return f"""You are a cybersecurity incident response analyst. A {severity.upper()} severity {incident_type} incident has been detected.

Please provide a comprehensive incident response plan including:

1. **Immediate Actions** (0-1 hour):
   - Containment steps
   - Evidence preservation
   - Stakeholder notification

2. **Investigation Phase** (1-24 hours):
   - Forensic analysis requirements
   - Log collection priorities
   - Threat intelligence gathering

3. **Recovery Phase** (24-72 hours):
   - System restoration steps
   - Security hardening measures
   - Monitoring enhancements

4. **Post-Incident** (72+ hours):
   - Lessons learned documentation
   - Process improvements
   - Training recommendations

Prioritize actions based on the {severity} severity level."""

    @server.prompt()
    def generate_threat_hunting_prompt(threat_actor: str, attack_technique: str) -> str:
        """Generate a prompt for threat hunting activities.
        
        Args:
            threat_actor: Known threat actor (APT29, APT28, Lazarus, etc.)
            attack_technique: MITRE ATT&CK technique (T1055, T1071, etc.)
        """
        return f"""Conduct proactive threat hunting for {threat_actor} using {attack_technique} techniques.

**Hunting Objectives:**
1. **IOC Analysis**: Search for known indicators of compromise
2. **Behavioral Patterns**: Identify anomalous network and system behaviors
3. **Lateral Movement**: Detect signs of internal network traversal
4. **Data Exfiltration**: Look for unauthorized data transfers
5. **Persistence**: Find evidence of long-term access establishment

**Search Queries Needed:**
- Network traffic patterns consistent with {threat_actor} TTPs
- Process execution anomalies
- Registry modifications
- File system changes
- Authentication anomalies

**Success Criteria:**
- Zero false positives
- Actionable intelligence
- Clear remediation steps
- Documentation for future hunts

Focus on high-confidence indicators that require immediate investigation."""

    @server.prompt()
    def create_security_report_prompt(report_type: str, time_period: str = "24h") -> str:
        """Generate a prompt for creating security reports.
        
        Args:
            report_type: Type of report (executive, technical, compliance)
            time_period: Time period for the report (24h, 7d, 30d)
        """
        return f"""Create a comprehensive {report_type} security report covering the last {time_period}.

**Report Structure:**

1. **Executive Summary** (for executive reports):
   - Key security metrics
   - Risk level assessment
   - Critical incidents summary
   - Business impact analysis

2. **Technical Analysis** (for technical reports):
   - Detailed log analysis
   - Attack vector breakdown
   - System vulnerabilities
   - Performance metrics

3. **Compliance Status** (for compliance reports):
   - Regulatory requirement coverage
   - Audit findings
   - Remediation status
   - Policy adherence

4. **Recommendations**:
   - Immediate actions required
   - Strategic improvements
   - Resource allocation needs
   - Timeline for implementation

5. **Appendices**:
   - Raw data references
   - Technical details
   - Supporting evidence

Tailor the content and technical depth based on the {report_type} audience."""

    logger.info("Enhanced MCP server setup completed successfully")
    return server



def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    print(f"\n🛑 Server shutdown requested (signal {signum})")
    print("👋 Goodbye!")
    shutdown_requested = True
    sys.exit(0)


def run_as_http(host, port, mcp:FastMCP):
    """Run the MCP server as an HTTP server using uvicorn"""
    import uvicorn
    
    # Load environment variables only for HTTP mode
    load_dotenv(override=True)
    
    logger.info(f"Starting HTTP server on {host}:{port}")
    
    try:
        # Create ASGI application
        app = mcp.http_app()
        
        # Run the ASGI application with uvicorn
        # Configure uvicorn to handle signals properly
        config = uvicorn.Config(
            app, 
            host=host, 
            port=port, 
            log_level="info",
            access_log=True,
            # Enable graceful shutdown
            lifespan="on"
        )
        server = uvicorn.Server(config)
        
        # Set up signal handlers for graceful shutdown
        def shutdown_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down HTTP server...")
            print(f"\n🛑 HTTP server shutdown requested (signal {signum})")
            print("👋 Goodbye!")
            server.should_exit = True
            
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        
        # Run the server
        server.run()
        
    except KeyboardInterrupt:
        logger.info("HTTP server interrupted by user")
        print("\n🛑 HTTP server shutdown requested by user (Ctrl+C)")
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"HTTP server error: {str(e)}")
        raise




def main():
    
    logger.info("Starting Cybersecurity Log Generator MCP Server")
    mcp = create_proper_mcp_server()
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        parser = argparse.ArgumentParser()
       
        parser.add_argument(
            "--transport",
            "-t",
            choices=["stdio", "http"],
            default="stdio",
            help="Transport protocol to use. Defaults to stdio.",
        )
        parser.add_argument(
            "--host",
            default="0.0.0.0",
            help="Host to bind the server to. Defaults to 0.0.0.0.",
        )
        parser.add_argument(
            "--port",
            "-p",
            type=int,
            default=8003,
            help="Port to bind the server to. Defaults to 8003.",
        )

        args = parser.parse_args()
              # Create enhanced MCP server
 
        
        # Override with environment variables if provided
        if os.getenv("MCP_HOST"):
            args.host = os.getenv("MCP_HOST")
            logger.info(f"Overriding host with MCP_HOST: {args.host}")
        
        if os.getenv("MCP_PORT"):
            args.port = int(os.getenv("MCP_PORT"))
            logger.info(f"Overriding port with MCP_PORT: {args.port}")
        
        if os.getenv("MCP_TRANSPORT"):
            args.transport = os.getenv("MCP_TRANSPORT")
            logger.info(f"Overriding transport with MCP_TRANSPORT: {args.transport}")
        
        logger.info(f"Transport: {args.transport}")
        if args.transport == "http":
            logger.info(f"Host: {args.host}, Port: {args.port}")

        # Run server with specified transport
        if args.transport == "http":
            logger.info("Starting MCP server with HTTP transport")
            run_as_http(args.host, args.port, mcp)
        else:
            logger.info("Starting MCP server with stdio transport")
            try:
                mcp.run(transport="stdio")
            except KeyboardInterrupt:
                logger.info("STDIO server interrupted by user")
                print("\n🛑 STDIO server shutdown requested by user (Ctrl+C)")
                print("👋 Goodbye!")
                sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt (Ctrl+C), shutting down gracefully...")
        print("\n🛑 Server shutdown requested by user (Ctrl+C)")
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()

