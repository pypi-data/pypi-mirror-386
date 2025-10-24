"""
MCP client example for the Cybersecurity Log Generator.
"""

import asyncio
import json
from fastmcp import Client


async def mcp_client_example():
    """Example of using the MCP client to interact with the log generator."""
    
    print("=== MCP Client Example ===")
    
    # Connect to the MCP server
    async with Client("http://localhost:8000/mcp") as client:
        print("Connected to MCP server")
        
        # Get supported log types
        print("\nGetting supported log types...")
        log_types = await client.call_tool("get_supported_log_types")
        print("Supported log types:")
        print(log_types.content[0].text)
        
        # Get supported threat actors
        print("\nGetting supported threat actors...")
        threat_actors = await client.call_tool("get_supported_threat_actors")
        print("Supported threat actors:")
        print(threat_actors.content[0].text)
        
        # Generate IDS logs
        print("\nGenerating IDS logs...")
        ids_logs = await client.call_tool("generate_logs", {
            "log_type": "ids",
            "count": 100,
            "time_range": "24h"
        })
        print(f"Generated IDS logs: {len(ids_logs.content[0].text)} characters")
        
        # Generate attack campaign
        print("\nGenerating APT29 attack campaign...")
        campaign = await client.call_tool("generate_attack_campaign", {
            "threat_actor": "APT29",
            "duration": "24h",
            "target_count": 50
        })
        print(f"Generated attack campaign: {len(campaign.content[0].text)} characters")
        
        # Generate correlated events
        print("\nGenerating correlated events...")
        correlated_events = await client.call_tool("generate_correlated_events", {
            "log_types": ["ids", "endpoint", "web_access"],
            "correlation_strength": 0.8,
            "time_window": "1h"
        })
        print(f"Generated correlated events: {len(correlated_events.content[0].text)} characters")
        
        # Analyze log patterns
        print("\nAnalyzing log patterns...")
        analysis = await client.call_tool("analyze_log_patterns", {
            "events_json": ids_logs.content[0].text
        })
        print("Log pattern analysis:")
        print(analysis.content[0].text)
        
        # Export logs
        print("\nExporting logs...")
        export_result = await client.call_tool("export_logs", {
            "events_json": ids_logs.content[0].text,
            "format": "csv"
        })
        print(f"Export result: {export_result.content[0].text}")
        
        # Generate network topology events
        print("\nGenerating network topology events...")
        topology_events = await client.call_tool("generate_network_topology_events", {
            "subnets": ["10.0.0.0/8", "192.168.0.0/16"],
            "internet_facing_ips": ["1.2.3.4", "5.6.7.8"],
            "event_count": 200
        })
        print(f"Generated network topology events: {len(topology_events.content[0].text)} characters")
        
        print("\nMCP client example completed successfully!")


async def main():
    """Main function."""
    try:
        await mcp_client_example()
    except Exception as e:
        print(f"Error in MCP client example: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
