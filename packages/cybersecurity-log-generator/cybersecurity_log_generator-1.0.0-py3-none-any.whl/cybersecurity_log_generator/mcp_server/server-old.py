#!/usr/bin/env python3
"""
Proper MCP server implementation following MCP specification.
This server exposes cybersecurity log generation tools to Cursor.
"""

import asyncio
import json
import sys
import requests
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.generator import LogGenerator
from core.models import LogType, ThreatActor

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

# Import MCP server
from mcp.server import FastMCP
# from .enhanced_server import create_enhanced_mcp_server  # Not needed - functionality is in this file

def create_proper_mcp_server() -> FastMCP:
    """Create a proper MCP server following MCP specification."""
    logger.info("Creating Proper Cybersecurity Log Generator MCP Server")
    
    # Initialize the log generator
    generator = LogGenerator()
    
    # Create MCP server with proper configuration
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
    
    @server.tool()
    def generate_logs(log_type: str, count: int = 100, time_range: str = "24h", ingest: bool = False, destination: str = "file") -> str:
        """Generate synthetic cybersecurity logs.
        
        Args:
            log_type: Type of logs to generate (ids, web_access, endpoint, windows_event, linux_syslog, firewall)
            count: Number of events to generate
            time_range: Time range for events (e.g., "24h", "7d", "1h")
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
            destination: Destination for logs (file, victorialogs) (default: file)
        
        Returns:
            JSON string containing generated log events
        """
        logger.info(f"generate_logs called with log_type={log_type}, count={count}, time_range={time_range}, ingest={ingest}, destination={destination}")
        
        try:
            # Convert string to LogType enum
            log_type_enum = LogType(log_type.lower())
            
            # Generate logs
            logger.info(f"Generating {count} {log_type} logs for time range {time_range}")
            start_time = datetime.now()
            
            events = generator.generate_logs(
                log_type=log_type_enum,
                count=count,
                time_range=time_range
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully generated {len(events)} events in {generation_time:.2f} seconds")
            
            # Convert to JSON
            events_data = [event.dict() for event in events]
            
            # Handle ingestion to VictoriaLogs if requested
            if ingest or destination == "victorialogs":
                logger.info(f"Ingesting {len(events_data)} logs to VictoriaLogs")
                ingest_success = ingest_logs_to_victorialogs(events_data)
                if ingest_success:
                    logger.info("Successfully ingested logs to VictoriaLogs")
                    return f"Generated and ingested {len(events)} {log_type} logs to VictoriaLogs successfully"
                else:
                    logger.error("Failed to ingest logs to VictoriaLogs")
                    return f"Generated {len(events)} {log_type} logs but failed to ingest to VictoriaLogs"
            
            # Default behavior - return JSON with datetime handling
            json_result = json.dumps(events_data, indent=2, cls=DateTimeEncoder)
            logger.info(f"Generated {len(events)} {log_type} logs successfully")
            return json_result
            
        except ValueError as e:
            logger.error(f"Invalid log_type '{log_type}': {str(e)}")
            return f"Error: Invalid log_type '{log_type}'. Supported types: ids, web_access, endpoint, windows_event, linux_syslog, firewall"
        except Exception as e:
            logger.error(f"Error generating logs: {str(e)}")
            return f"Error generating logs: {str(e)}"
    
    @server.tool()
    def ingest_logs_to_victorialogs_tool(logs_json: str, victorialogs_url: str = "http://localhost:9428") -> str:
        """Ingest logs into VictoriaLogs.
        
        Args:
            logs_json: JSON string containing logs to ingest
            victorialogs_url: VictoriaLogs endpoint URL (default: http://localhost:9428)
        
        Returns:
            Status message indicating success or failure
        """
        logger.info(f"ingest_logs_to_victorialogs_tool called with victorialogs_url={victorialogs_url}")
        
        try:
            # Parse JSON logs
            logs_data = json.loads(logs_json)
            if not isinstance(logs_data, list):
                return "Error: logs_json must be a JSON array of log objects"
            
            logger.info(f"Ingesting {len(logs_data)} logs to VictoriaLogs")
            
            # Ingest logs
            success = ingest_logs_to_victorialogs(logs_data, victorialogs_url)
            
            if success:
                logger.info(f"Successfully ingested {len(logs_data)} logs to VictoriaLogs")
                return f"Successfully ingested {len(logs_data)} logs to VictoriaLogs at {victorialogs_url}"
            else:
                logger.error("Failed to ingest logs to VictoriaLogs")
                return f"Failed to ingest logs to VictoriaLogs at {victorialogs_url}"
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in logs_json: {str(e)}")
            return f"Error: Invalid JSON format in logs_json: {str(e)}"
        except Exception as e:
            logger.error(f"Error ingesting logs to VictoriaLogs: {str(e)}")
            return f"Error ingesting logs to VictoriaLogs: {str(e)}"
    
    @server.tool()
    def generate_attack_campaign(threat_actor: str, duration: str = "24h", target_count: int = 50) -> str:
        """Generate a coordinated attack campaign.
        
        Args:
            threat_actor: Threat actor to simulate (APT29, APT28, Lazarus, etc.)
            duration: Duration of the campaign (e.g., "24h", "7d")
            target_count: Number of target events to generate
        
        Returns:
            JSON string containing the attack campaign
        """
        logger.info(f"generate_attack_campaign called with threat_actor={threat_actor}, duration={duration}, target_count={target_count}")
        
        try:
            # Convert string to ThreatActor enum
            threat_actor_enum = ThreatActor(threat_actor.upper())
            
            # Generate campaign
            logger.info(f"Generating {threat_actor} attack campaign with {target_count} events over {duration}")
            start_time = datetime.now()
            
            campaign = generator.generate_security_campaign(
                threat_actor=threat_actor_enum,
                duration=duration,
                target_count=target_count
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully generated {threat_actor} campaign with {len(campaign.events)} events in {generation_time:.2f} seconds")
            
            # Convert to JSON
            campaign_data = campaign.dict()
            json_result = json.dumps(campaign_data, indent=2, default=str)
            
            logger.info(f"Generated {threat_actor} attack campaign successfully")
            return json_result
            
        except ValueError as e:
            logger.error(f"Invalid threat_actor '{threat_actor}': {str(e)}")
            return f"Error: Invalid threat_actor '{threat_actor}'. Supported actors: APT29, APT28, Lazarus, Carbon Spider, FIN7"
        except Exception as e:
            logger.error(f"Error generating attack campaign: {str(e)}")
            return f"Error generating attack campaign: {str(e)}"
    
    @server.tool()
    def get_supported_log_types() -> str:
        """Get list of supported log types.
        
        Returns:
            JSON string containing supported log types
        """
        logger.info("get_supported_log_types called")
        
        try:
            log_types = [log_type.value for log_type in LogType]
            result = {"supported_log_types": log_types}
            json_result = json.dumps(result, indent=2)
            
            logger.info(f"Returned {len(log_types)} supported log types")
            return json_result
            
        except Exception as e:
            logger.error(f"Error getting supported log types: {str(e)}")
            return f"Error getting supported log types: {str(e)}"
    
    @server.tool()
    def get_supported_threat_actors() -> str:
        """Get list of supported threat actors.
        
        Returns:
            JSON string containing supported threat actors
        """
        logger.info("get_supported_threat_actors called")
        
        try:
            threat_actors = [actor.value for actor in ThreatActor]
            result = {"supported_threat_actors": threat_actors}
            json_result = json.dumps(result, indent=2)
            
            logger.info(f"Returned {len(threat_actors)} supported threat actors")
            return json_result
            
        except Exception as e:
            logger.error(f"Error getting supported threat actors: {str(e)}")
            return f"Error getting supported threat actors: {str(e)}"
    
    @server.tool()
    def generate_correlated_events(log_types: str, count: int = 100, correlation_strength: float = 0.7) -> str:
        """Generate correlated events across multiple log types.
        
        Args:
            log_types: Comma-separated list of log types (e.g., "ids,firewall,web_access")
            count: Number of events to generate
            correlation_strength: Strength of correlation between events (0.0-1.0)
        
        Returns:
            JSON string containing correlated events
        """
        logger.info(f"generate_correlated_events called with log_types={log_types}, count={count}, correlation_strength={correlation_strength}")
        
        try:
            # Parse log types
            log_type_list = [lt.strip() for lt in log_types.split(',')]
            
            # Generate correlated events
            logger.info(f"Generating {count} correlated events across {len(log_type_list)} log types")
            start_time = datetime.now()
            
            events = generator.generate_correlated_events(
                log_types=[LogType(lt.lower()) for lt in log_type_list],
                count=count,
                correlation_strength=correlation_strength
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully generated {len(events)} correlated events in {generation_time:.2f} seconds")
            
            # Convert to JSON
            events_data = [event.dict() for event in events]
            json_result = json.dumps(events_data, indent=2, default=str)
            
            logger.info(f"Generated {len(events)} correlated events successfully")
            return json_result
            
        except Exception as e:
            logger.error(f"Error generating correlated events: {str(e)}")
            return f"Error generating correlated events: {str(e)}"
    
    @server.tool()
    def export_logs(events_json: str, format: str = "json", output_path: str = "exported_logs") -> str:
        """Export generated logs to files.
        
        Args:
            events_json: JSON string containing events to export
            format: Export format (json, csv, syslog, cef, leef)
            output_path: Path for output file
        
        Returns:
            Success message with file path
        """
        logger.info(f"export_logs called with format={format}, output_path={output_path}")
        
        try:
            # Parse events JSON
            events_data = json.loads(events_json)
            
            # Create output file path with proper extension
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
            logger.info(f"Exporting {len(events_data)} events to {format} format")
            
            if format == "json":
                with open(file_path, 'w') as f:
                    json.dump(events_data, f, indent=2, default=str)
            elif format == "csv":
                import csv
                with open(file_path, 'w', newline='') as f:
                    if events_data and len(events_data) > 0:
                        writer = csv.DictWriter(f, fieldnames=events_data[0].keys())
                        writer.writeheader()
                        writer.writerows(events_data)
            elif format == "syslog":
                with open(file_path, 'w') as f:
                    for event in events_data:
                        timestamp = event.get('timestamp', datetime.now().isoformat())
                        severity = event.get('severity', 'INFO')
                        message = event.get('message', '')
                        f.write(f"{timestamp} {severity} {message}\n")
            elif format == "cef":
                with open(file_path, 'w') as f:
                    for event in events_data:
                        # CEF format: CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|Extension
                        timestamp = event.get('timestamp', datetime.now().isoformat())
                        severity = event.get('severity', 'INFO')
                        message = event.get('message', '')
                        source_ip = event.get('source', {}).get('ip_address', '0.0.0.0')
                        dest_ip = event.get('destination', {}).get('ip_address', '0.0.0.0') if event.get('destination') else '0.0.0.0'
                        user = event.get('user', 'unknown')
                        
                        cef_line = f"CEF:0|CybersecurityLogGenerator|MCP|1.0|{event.get('log_type', 'security')}|{message}|{severity}|src={source_ip} dst={dest_ip} suser={user} msg={message}\n"
                        f.write(cef_line)
            elif format == "leef":
                with open(file_path, 'w') as f:
                    for event in events_data:
                        # LEEF format: LEEF:Version|Vendor|Product|Version|EventID|Name|Severity|Extension
                        timestamp = event.get('timestamp', datetime.now().isoformat())
                        severity = event.get('severity', 'INFO')
                        message = event.get('message', '')
                        source_ip = event.get('source', {}).get('ip_address', '0.0.0.0')
                        dest_ip = event.get('destination', {}).get('ip_address', '0.0.0.0') if event.get('destination') else '0.0.0.0'
                        user = event.get('user', 'unknown')
                        
                        leef_line = f"LEEF:2.0|CybersecurityLogGenerator|MCP|1.0|{event.get('log_type', 'security')}|{message}|{severity}|src={source_ip} dst={dest_ip} usr={user} msg={message}\n"
                        f.write(leef_line)
            
            logger.info(f"Successfully exported logs to {file_path}")
            return f"Successfully exported {len(events_data)} events to {file_path}"
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {str(e)}")
            return f"Error: Invalid JSON format - {str(e)}"
        except Exception as e:
            logger.error(f"Error exporting logs: {str(e)}")
            return f"Error exporting logs: {str(e)}"
    
    @server.tool()
    def analyze_log_patterns(events_json: str, analysis_type: str = "summary") -> str:
        """Analyze log patterns and provide insights.
        
        Args:
            events_json: JSON string containing events to analyze
            analysis_type: Type of analysis (summary, security, performance, anomalies)
        
        Returns:
            JSON string containing analysis results
        """
        logger.info(f"analyze_log_patterns called with analysis_type={analysis_type}")
        
        try:
            # Parse events JSON
            events_data = json.loads(events_json)
            
            # Analyze patterns
            logger.info(f"Analyzing {len(events_data)} events with {analysis_type} analysis")
            start_time = datetime.now()
            
            analysis_result = generator.analyze_log_patterns(events_data, analysis_type)
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully completed {analysis_type} analysis in {analysis_time:.2f} seconds")
            
            # Convert to JSON
            json_result = json.dumps(analysis_result, indent=2, default=str)
            
            logger.info(f"Analysis completed successfully")
            return json_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {str(e)}")
            return f"Error: Invalid JSON format - {str(e)}"
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

    # ============================================================================
    # ENHANCED 24-PILLAR TOOLS
    # ============================================================================
    
    # Initialize enhanced generator for 24-pillar support
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from core.enhanced_generator import EnhancedLogGenerator
        from core.models import CyberdefensePillar, ThreatActor
        enhanced_generator = EnhancedLogGenerator()
        logger.info("Enhanced 24-pillar generator initialized successfully")
    except Exception as e:
        logger.warning(f"Enhanced generator not available: {str(e)}")
        enhanced_generator = None

    @server.tool()
    def generate_pillar_logs(pillar: str, count: int = 100, time_range: str = "24h", 
                           ingest: bool = False, destination: str = "file") -> str:
        """Generate logs for a specific cyberdefense pillar with realistic attack patterns.
        
        This tool generates logs for any of the 24 cyberdefense pillars with pillar-specific
        attack patterns, threat indicators, and mitigation controls.
        
        Args:
            pillar: Cyberdefense pillar name (vendor_risk, api_security, endpoint_security, 
                   application_security, audit_compliance, authentication, authorization,
                   cloud_security, container_security, data_privacy, data_protection,
                   detection_correlation, disaster_recovery, due_diligence, encryption,
                   endpoint_security, ai_security, governance_risk, identity_governance,
                   incident_response, network_security, ot_physical_security,
                   security_awareness, threat_intelligence, vulnerability_management)
            count: Number of events to generate (default: 100)
            time_range: Time range for events (e.g., "24h", "7d", "1h") (default: "24h")
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
            destination: Destination for logs (file, victorialogs) (default: "file")
        
        Returns:
            JSON string containing generated log events with pillar-specific attack patterns,
            threat indicators, and mitigation controls.
        
        Examples:
            - "Generate 100 vendor risk logs" → generate_pillar_logs("vendor_risk", 100)
            - "Create 50 API security logs and ingest to VictoriaLogs" → generate_pillar_logs("api_security", 50, ingest=True)
            - "Generate endpoint security logs for 7 days" → generate_pillar_logs("endpoint_security", 200, "7d")
        """
        logger.info(f"generate_pillar_logs called with pillar={pillar}, count={count}, time_range={time_range}, ingest={ingest}")
        
        if not enhanced_generator:
            return "Error: Enhanced 24-pillar generator not available. Please check installation."
        
        try:
            # Convert string to pillar enum
            pillar_enum = CyberdefensePillar(pillar.lower())
            
            # Generate logs
            logger.info(f"Generating {count} {pillar} logs for time range {time_range}")
            start_time = datetime.now()
            
            events = enhanced_generator.generate_logs(
                pillar=pillar_enum,
                count=count,
                time_range=time_range
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully generated {len(events)} {pillar} events in {generation_time:.2f} seconds")
            
            # Convert to JSON
            events_data = [event.dict() for event in events]
            
            # Handle ingestion to VictoriaLogs if requested
            if ingest or destination == "victorialogs":
                logger.info(f"Ingesting {len(events_data)} {pillar} logs to VictoriaLogs")
                ingest_success = ingest_logs_to_victorialogs(events_data)
                if ingest_success:
                    logger.info("Successfully ingested logs to VictoriaLogs")
                    return f"Generated and ingested {len(events)} {pillar} logs to VictoriaLogs successfully"
                else:
                    logger.error("Failed to ingest logs to VictoriaLogs")
                    return f"Generated {len(events)} {pillar} logs but failed to ingest to VictoriaLogs"
            
            # Default behavior - return JSON with datetime handling
            json_result = json.dumps(events_data, indent=2, default=str)
            logger.info(f"Generated {len(events)} {pillar} logs successfully")
            return json_result
            
        except ValueError as e:
            logger.error(f"Invalid pillar '{pillar}': {str(e)}")
            return f"Error: Invalid pillar '{pillar}'. Supported pillars: {', '.join([p.value for p in CyberdefensePillar])}"
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
            threat_actor: Threat actor name (APT29, APT28, Lazarus, Carbon Spider, FIN7, 
                         UNC2452, Wizard Spider, Ryuk, Conti, Maze)
            duration: Campaign duration (e.g., "24h", "72h", "7d") (default: "24h")
            target_count: Number of target events to generate (default: 50)
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
        
        Returns:
            JSON string containing the attack campaign with coordinated events,
            threat actor attribution, and campaign objectives.
        
        Examples:
            - "Create APT29 attack campaign" → generate_campaign_logs("APT29", "72h", 100)
            - "Generate Lazarus campaign and ingest to VictoriaLogs" → generate_campaign_logs("Lazarus", "24h", 50, ingest=True)
            - "Create 7-day APT28 campaign" → generate_campaign_logs("APT28", "7d", 200)
        """
        logger.info(f"generate_campaign_logs called with threat_actor={threat_actor}, duration={duration}, target_count={target_count}, ingest={ingest}")
        
        if not enhanced_generator:
            return "Error: Enhanced 24-pillar generator not available. Please check installation."
        
        try:
            # Convert string to threat actor enum
            actor_enum = ThreatActor(threat_actor.upper())
            
            # Generate campaign
            logger.info(f"Generating {threat_actor} campaign with {target_count} events over {duration}")
            start_time = datetime.now()
            
            campaign = enhanced_generator.generate_campaign(
                threat_actor=actor_enum,
                duration=duration,
                target_count=target_count
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully generated {len(campaign.events)} campaign events in {generation_time:.2f} seconds")
            
            # Convert to JSON
            campaign_data = campaign.dict()
            
            # Handle ingestion if requested
            if ingest:
                events_data = [event.dict() for event in campaign.events]
                logger.info(f"Ingesting {len(events_data)} campaign events to VictoriaLogs")
                ingest_success = ingest_logs_to_victorialogs(events_data)
                if ingest_success:
                    logger.info("Successfully ingested campaign events to VictoriaLogs")
                    return f"Generated and ingested {len(campaign.events)} {threat_actor} campaign events to VictoriaLogs successfully"
                else:
                    logger.error("Failed to ingest campaign events to VictoriaLogs")
                    return f"Generated {len(campaign.events)} {threat_actor} campaign events but failed to ingest to VictoriaLogs"
            
            # Return JSON with datetime handling
            json_result = json.dumps(campaign_data, indent=2, default=str)
            logger.info(f"Generated {len(campaign.events)} {threat_actor} campaign events successfully")
            return json_result
            
        except ValueError as e:
            logger.error(f"Invalid threat_actor '{threat_actor}': {str(e)}")
            return f"Error: Invalid threat_actor '{threat_actor}'. Supported actors: {', '.join([t.value for t in ThreatActor])}"
        except Exception as e:
            logger.error(f"Error generating campaign: {str(e)}")
            return f"Error generating campaign: {str(e)}"

    @server.tool()
    def generate_correlated_logs(log_types: str, count: int = 100, 
                               correlation_strength: float = 0.7, ingest: bool = False) -> str:
        """Generate correlated events across multiple cyberdefense pillars.
        
        This tool generates correlated security events that span multiple pillars,
        simulating realistic attack chains and coordinated threats.
        
        Args:
            log_types: Comma-separated list of pillar names (e.g., "endpoint_security,network_security,data_protection")
            count: Number of events to generate (default: 100)
            correlation_strength: Strength of correlation between events (0.0-1.0) (default: 0.7)
            ingest: Whether to ingest logs into VictoriaLogs (default: False)
        
        Returns:
            JSON string containing correlated events with correlation IDs,
            cross-pillar attack patterns, and coordinated threat indicators.
        
        Examples:
            - "Generate correlated endpoint and network security events" → generate_correlated_logs("endpoint_security,network_security", 50, 0.8)
            - "Create correlated events across 3 pillars" → generate_correlated_logs("vendor_risk,api_security,endpoint_security", 100, 0.9)
            - "Generate correlated events and ingest to VictoriaLogs" → generate_correlated_logs("endpoint_security,data_protection", 75, 0.6, ingest=True)
        """
        logger.info(f"generate_correlated_logs called with log_types={log_types}, count={count}, correlation_strength={correlation_strength}, ingest={ingest}")
        
        if not enhanced_generator:
            return "Error: Enhanced 24-pillar generator not available. Please check installation."
        
        try:
            # Generate correlated events
            logger.info(f"Generating {count} correlated events across {log_types} with correlation strength {correlation_strength}")
            start_time = datetime.now()
            
            events = enhanced_generator.generate_correlated_events(
                log_types=log_types,
                count=count,
                correlation_strength=correlation_strength
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully generated {len(events)} correlated events in {generation_time:.2f} seconds")
            
            # Convert to JSON
            events_data = [event.dict() for event in events]
            
            # Handle ingestion if requested
            if ingest:
                logger.info(f"Ingesting {len(events_data)} correlated events to VictoriaLogs")
                ingest_success = ingest_logs_to_victorialogs(events_data)
                if ingest_success:
                    logger.info("Successfully ingested correlated events to VictoriaLogs")
                    return f"Generated and ingested {len(events)} correlated events to VictoriaLogs successfully"
                else:
                    logger.error("Failed to ingest correlated events to VictoriaLogs")
                    return f"Generated {len(events)} correlated events but failed to ingest to VictoriaLogs"
            
            # Return JSON with datetime handling
            json_result = json.dumps(events_data, indent=2, default=str)
            logger.info(f"Generated {len(events)} correlated events successfully")
            return json_result
            
        except Exception as e:
            logger.error(f"Error generating correlated logs: {str(e)}")
            return f"Error generating correlated logs: {str(e)}"

    @server.tool()
    def get_supported_pillars() -> str:
        """Get list of all 24 supported cyberdefense pillars.
        
        Returns:
            JSON string containing all supported cyberdefense pillars with their descriptions.
        
        Examples:
            - "What pillars are supported?" → get_supported_pillars()
            - "Show me all available pillars" → get_supported_pillars()
        """
        logger.info("get_supported_pillars called")
        
        if not enhanced_generator:
            return "Error: Enhanced 24-pillar generator not available. Please check installation."
        
        try:
            pillars = enhanced_generator.get_supported_pillars()
            pillar_list = [pillar.value for pillar in pillars]
            
            # Add descriptions for each pillar
            pillar_descriptions = {
                "vendor_risk": "3rd-Party/Vendor Risk management",
                "api_security": "API Security and protection",
                "application_security": "Application Security (SDLC)",
                "audit_compliance": "Audit & Compliance",
                "authentication": "Authentication systems",
                "authorization": "Authorization controls",
                "cloud_security": "Cloud Security (CNAPP)",
                "container_security": "Container Security",
                "data_privacy": "Data Privacy & Sovereignty",
                "data_protection": "Data Protection & Backup",
                "detection_correlation": "Detection & Correlation",
                "disaster_recovery": "Disaster Recovery",
                "due_diligence": "Due Diligence",
                "encryption": "Encryption systems",
                "endpoint_security": "Endpoint Security",
                "ai_security": "Enterprise AI Security",
                "governance_risk": "Governance, Risk & Strategy",
                "identity_governance": "Identity Governance (IGA)",
                "incident_response": "Incident Response",
                "network_security": "Network Security",
                "ot_physical_security": "OT/ICS & Physical Security",
                "security_awareness": "Security Awareness & Training",
                "threat_intelligence": "Threat Intelligence",
                "vulnerability_management": "Vulnerability Management"
            }
            
            result = {
                "supported_pillars": pillar_list,
                "pillar_descriptions": pillar_descriptions,
                "total_pillars": len(pillar_list)
            }
            
            json_result = json.dumps(result, indent=2)
            logger.info(f"Returned {len(pillar_list)} supported pillars")
            return json_result
            
        except Exception as e:
            logger.error(f"Error getting supported pillars: {str(e)}")
            return f"Error getting supported pillars: {str(e)}"

    @server.tool()
    def get_pillar_attack_patterns(pillar: str) -> str:
        """Get specific attack patterns for a cyberdefense pillar.
        
        Args:
            pillar: Cyberdefense pillar name (vendor_risk, api_security, endpoint_security, etc.)
        
        Returns:
            JSON string containing attack patterns, severity levels, threat indicators,
            and mitigation controls for the specified pillar.
        
        Examples:
            - "Get attack patterns for vendor risk" → get_pillar_attack_patterns("vendor_risk")
            - "Show me API security attack patterns" → get_pillar_attack_patterns("api_security")
            - "What attacks target endpoint security?" → get_pillar_attack_patterns("endpoint_security")
        """
        logger.info(f"get_pillar_attack_patterns called with pillar={pillar}")
        
        if not enhanced_generator:
            return "Error: Enhanced 24-pillar generator not available. Please check installation."
        
        try:
            pillar_enum = CyberdefensePillar(pillar.lower())
            patterns = enhanced_generator.get_pillar_attack_patterns(pillar_enum)
            
            result = {
                "pillar": pillar,
                "attack_patterns": patterns,
                "total_patterns": len(patterns)
            }
            
            json_result = json.dumps(result, indent=2)
            logger.info(f"Returned {len(patterns)} attack patterns for {pillar}")
            return json_result
            
        except ValueError as e:
            logger.error(f"Invalid pillar '{pillar}': {str(e)}")
            return f"Error: Invalid pillar '{pillar}'. Supported pillars: {', '.join([p.value for p in CyberdefensePillar])}"
        except Exception as e:
            logger.error(f"Error getting attack patterns: {str(e)}")
            return f"Error getting attack patterns: {str(e)}"

    @server.tool()
    def get_threat_actors() -> str:
        """Get list of supported threat actors with their characteristics.
        
        Returns:
            JSON string containing threat actors with their sophistication levels,
            target industries, and attack tactics.
        
        Examples:
            - "What threat actors are supported?" → get_threat_actors()
            - "Show me all available threat actors" → get_threat_actors()
        """
        logger.info("get_threat_actors called")
        
        if not enhanced_generator:
            return "Error: Enhanced 24-pillar generator not available. Please check installation."
        
        try:
            actors = enhanced_generator.get_threat_actors()
            actor_list = [actor.value for actor in actors]
            
            # Add threat actor characteristics
            actor_characteristics = {
                "APT29": {
                    "sophistication": "high",
                    "targets": ["government", "healthcare", "finance"],
                    "tactics": ["initial_access", "persistence", "exfiltration"]
                },
                "APT28": {
                    "sophistication": "high",
                    "targets": ["government", "military", "energy"],
                    "tactics": ["execution", "lateral_movement", "collection"]
                },
                "Lazarus": {
                    "sophistication": "medium",
                    "targets": ["finance", "cryptocurrency"],
                    "tactics": ["initial_access", "exfiltration"]
                },
                "Carbon Spider": {
                    "sophistication": "medium",
                    "targets": ["finance", "retail"],
                    "tactics": ["credential_access", "impact"]
                },
                "FIN7": {
                    "sophistication": "medium",
                    "targets": ["finance", "retail"],
                    "tactics": ["credential_access", "collection"]
                }
            }
            
            result = {
                "supported_threat_actors": actor_list,
                "actor_characteristics": actor_characteristics,
                "total_actors": len(actor_list)
            }
            
            json_result = json.dumps(result, indent=2)
            logger.info(f"Returned {len(actor_list)} threat actors")
            return json_result
            
        except Exception as e:
            logger.error(f"Error getting threat actors: {str(e)}")
            return f"Error getting threat actors: {str(e)}"

    @server.tool()
    def get_correlation_rules() -> str:
        """Get available correlation rules for cross-pillar attacks.
        
        Returns:
            JSON string containing correlation rules that link events across
            multiple cyberdefense pillars for advanced attack detection.
        
        Examples:
            - "What correlation rules are available?" → get_correlation_rules()
            - "Show me cross-pillar correlation rules" → get_correlation_rules()
        """
        logger.info("get_correlation_rules called")
        
        if not enhanced_generator:
            return "Error: Enhanced 24-pillar generator not available. Please check installation."
        
        try:
            rules = enhanced_generator.get_correlation_rules()
            
            result = {
                "correlation_rules": rules,
                "total_rules": len(rules)
            }
            
            json_result = json.dumps(result, indent=2)
            logger.info(f"Returned {len(rules)} correlation rules")
            return json_result
            
        except Exception as e:
            logger.error(f"Error getting correlation rules: {str(e)}")
            return f"Error getting correlation rules: {str(e)}"

    logger.info("Enhanced 24-pillar tools added successfully")
    logger.info("Proper MCP server setup completed successfully")
    return server

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Proper Cybersecurity Log Generator MCP Server")
    
    try:
        # Create MCP server
        server = create_proper_mcp_server()
        
        # Run server with stdio transport
        logger.info("Starting MCP server with stdio transport")
        server.run(transport="stdio")
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise

if __name__ == "__main__":
    main()
