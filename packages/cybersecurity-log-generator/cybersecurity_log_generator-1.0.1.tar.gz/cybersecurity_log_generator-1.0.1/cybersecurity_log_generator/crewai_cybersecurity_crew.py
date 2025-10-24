#!/usr/bin/env python3
"""
CrewAI Cybersecurity Crew with MCP Integration
Advanced CrewAI implementation using CrewBase for cybersecurity log generation and analysis.
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets")

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from crewai import CrewBase, Agent, Task, Crew, Process
    from crewai_tools import MCPServerAdapter
    from mcp import StdioServerParameters
    print("✓ CrewAI and MCP imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Please install: pip install 'crewai-tools[mcp]'")
    sys.exit(1)


@CrewBase
class CybersecurityCrew:
    """CrewAI crew for cybersecurity log generation and analysis using MCP servers."""
    
    # Configure MCP server parameters
    mcp_server_params = [
        StdioServerParameters(
            command=sys.executable,
            args=[str(Path(__file__).parent / "mcp_server" / "server.py")],
            env={"PYTHONPATH": str(Path(__file__).parent), **os.environ}
        )
    ]
    
    # Set connection timeout
    mcp_connect_timeout = 60
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = []
    
    @agent
    def log_generator_agent(self):
        """Agent specialized in generating cybersecurity logs."""
        return Agent(
            role="Cybersecurity Log Generator",
            goal="Generate high-quality synthetic cybersecurity logs for testing and analysis",
            backstory="Expert in creating realistic security logs that accurately represent real-world scenarios including normal activities and attack patterns",
            tools=self.get_mcp_tools("generate_logs", "generate_attack_campaign", "generate_pillar_logs"),
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def log_analyzer_agent(self):
        """Agent specialized in analyzing cybersecurity logs."""
        return Agent(
            role="Cybersecurity Log Analyzer",
            goal="Analyze cybersecurity logs for threats, patterns, and security insights",
            backstory="Expert in log analysis, threat detection, and security pattern recognition with deep knowledge of attack signatures and normal behavior patterns",
            tools=self.get_mcp_tools("analyze_log_patterns", "export_logs"),
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def siem_specialist_agent(self):
        """Agent specialized in SIEM log generation and analysis."""
        return Agent(
            role="SIEM Specialist",
            goal="Generate and analyze SIEM priority logs for comprehensive security monitoring",
            backstory="Expert in SIEM systems, security event correlation, and priority log analysis with deep understanding of security operations center workflows",
            tools=self.get_mcp_tools("generate_siem_priority_logs", "get_siem_categories", "generate_comprehensive_siem_logs"),
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def threat_intelligence_agent(self):
        """Agent specialized in threat intelligence and attack campaigns."""
        return Agent(
            role="Threat Intelligence Analyst",
            goal="Generate and analyze threat intelligence data and attack campaigns",
            backstory="Expert in threat intelligence, attack campaign analysis, and threat actor profiling with deep knowledge of APT groups and attack techniques",
            tools=self.get_mcp_tools("generate_campaign_logs", "get_threat_actors", "get_correlation_rules"),
            verbose=True,
            allow_delegation=False
        )
    
    @task
    def generate_basic_logs_task(self):
        """Task to generate basic cybersecurity logs."""
        return Task(
            description="Generate 100 IDS logs and 50 web access logs for the last 24 hours",
            agent=self.log_generator_agent(),
            expected_output="Generated IDS and web access logs with realistic patterns and timestamps"
        )
    
    @task
    def generate_siem_logs_task(self):
        """Task to generate SIEM priority logs."""
        return Task(
            description="Generate 200 SIEM priority logs across all categories (EDR, network, AD, Windows, cloud) for the last 12 hours",
            agent=self.siem_specialist_agent(),
            expected_output="Generated SIEM priority logs with proper category distribution and realistic security events"
        )
    
    @task
    def generate_attack_campaign_task(self):
        """Task to generate attack campaign logs."""
        return Task(
            description="Generate an APT29 attack campaign with 50 events over 72 hours",
            agent=self.threat_intelligence_agent(),
            expected_output="Generated APT29 attack campaign with coordinated events and realistic attack progression"
        )
    
    @task
    def analyze_logs_task(self):
        """Task to analyze generated logs."""
        return Task(
            description="Analyze all generated logs for security threats, patterns, and anomalies. Export the analysis results to files.",
            agent=self.log_analyzer_agent(),
            context=[self.generate_basic_logs_task(), self.generate_siem_logs_task(), self.generate_attack_campaign_task()],
            expected_output="Comprehensive security analysis report with threat assessment and exported log files"
        )
    
    @task
    def generate_correlated_events_task(self):
        """Task to generate correlated events across multiple pillars."""
        return Task(
            description="Generate 150 correlated events across authentication, network security, and endpoint security pillars",
            agent=self.log_generator_agent(),
            expected_output="Generated correlated security events with cross-pillar relationships and attack chains"
        )
    
    @crew
    def cybersecurity_crew(self):
        """Main cybersecurity crew."""
        return Crew(
            agents=[
                self.log_generator_agent(),
                self.log_analyzer_agent(),
                self.siem_specialist_agent(),
                self.threat_intelligence_agent()
            ],
            tasks=[
                self.generate_basic_logs_task(),
                self.generate_siem_logs_task(),
                self.generate_attack_campaign_task(),
                self.generate_correlated_events_task(),
                self.analyze_logs_task()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            planning=True
        )
    
    def run_cybersecurity_analysis(self):
        """Run the complete cybersecurity analysis crew."""
        print("🚀 Starting Cybersecurity Analysis Crew")
        print("=" * 60)
        
        try:
            # Get available MCP tools
            mcp_tools = self.get_mcp_tools()
            print(f"✓ Available MCP tools: {[tool.name for tool in mcp_tools]}")
            
            # Execute the crew
            print("🔄 Executing cybersecurity crew...")
            result = self.cybersecurity_crew().kickoff()
            
            print("✅ Cybersecurity analysis completed successfully!")
            print(f"📊 Result: {str(result)[:200]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ Cybersecurity analysis failed: {e}")
            raise
    
    def run_specialized_analysis(self, analysis_type="siem"):
        """Run specialized analysis based on type."""
        print(f"🎯 Starting Specialized {analysis_type.upper()} Analysis")
        print("=" * 60)
        
        try:
            if analysis_type == "siem":
                # SIEM-focused crew
                crew = Crew(
                    agents=[self.siem_specialist_agent(), self.log_analyzer_agent()],
                    tasks=[self.generate_siem_logs_task(), self.analyze_logs_task()],
                    process=Process.sequential,
                    verbose=True
                )
            elif analysis_type == "threat":
                # Threat intelligence-focused crew
                crew = Crew(
                    agents=[self.threat_intelligence_agent(), self.log_analyzer_agent()],
                    tasks=[self.generate_attack_campaign_task(), self.analyze_logs_task()],
                    process=Process.sequential,
                    verbose=True
                )
            else:
                # Basic log generation crew
                crew = Crew(
                    agents=[self.log_generator_agent(), self.log_analyzer_agent()],
                    tasks=[self.generate_basic_logs_task(), self.analyze_logs_task()],
                    process=Process.sequential,
                    verbose=True
                )
            
            print(f"🔄 Executing {analysis_type} analysis crew...")
            result = crew.kickoff()
            
            print(f"✅ {analysis_type.title()} analysis completed successfully!")
            print(f"📊 Result: {str(result)[:200]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ {analysis_type.title()} analysis failed: {e}")
            raise


def main():
    """Main entry point for the cybersecurity crew."""
    print("🔧 CrewAI Cybersecurity Crew with MCP Integration")
    print("Advanced cybersecurity log generation and analysis")
    
    # Check if CrewAI is available
    try:
        import crewai
        import crewai_tools
        print(f"✓ CrewAI version: {crewai.__version__}")
        print(f"✓ CrewAI Tools available")
    except ImportError as e:
        print(f"✗ CrewAI not available: {e}")
        print("Please install: pip install 'crewai-tools[mcp]'")
        return
    
    # Create and run the cybersecurity crew
    crew_instance = CybersecurityCrew()
    
    # Run different types of analysis
    try:
        print("\n" + "=" * 60)
        print("🎯 RUNNING SPECIALIZED SIEM ANALYSIS")
        print("=" * 60)
        siem_result = crew_instance.run_specialized_analysis("siem")
        
        print("\n" + "=" * 60)
        print("🎯 RUNNING SPECIALIZED THREAT ANALYSIS")
        print("=" * 60)
        threat_result = crew_instance.run_specialized_analysis("threat")
        
        print("\n" + "=" * 60)
        print("🎯 RUNNING COMPREHENSIVE CYBERSECURITY ANALYSIS")
        print("=" * 60)
        comprehensive_result = crew_instance.run_cybersecurity_analysis()
        
        print("\n🎉 All cybersecurity analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("Check the MCP server is running and accessible")


if __name__ == "__main__":
    main()

