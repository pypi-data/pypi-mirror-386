"""
Tests for the MCP server functionality.
"""

import pytest
from cybersecurity_log_generator.mcp_server.server import create_proper_mcp_server


def test_mcp_server_creation():
    """Test that MCP server can be created."""
    server = create_proper_mcp_server()
    assert server is not None


def test_mcp_server_tools():
    """Test that MCP server has the expected tools."""
    server = create_proper_mcp_server()
    
    # Check that server has tools
    assert hasattr(server, 'tools')
    assert len(server.tools) > 0
    
    # Check for specific tools
    tool_names = [tool.name for tool in server.tools]
    expected_tools = [
        "generate_logs",
        "generate_pillar_logs", 
        "generate_campaign_logs",
        "generate_correlated_logs",
        "export_logs",
        "analyze_log_patterns"
    ]
    
    for expected_tool in expected_tools:
        assert expected_tool in tool_names


def test_mcp_server_tool_execution():
    """Test that MCP server tools can be executed."""
    server = create_proper_mcp_server()
    
    # Find the generate_logs tool
    generate_tool = None
    for tool in server.tools:
        if tool.name == "generate_logs":
            generate_tool = tool
            break
    
    assert generate_tool is not None
    
    # Test tool execution
    result = generate_tool.func(
        log_type="ids",
        count=5,
        time_range="1h"
    )
    
    assert result is not None
    assert isinstance(result, str)  # Should return JSON string


def test_mcp_server_pillar_tool():
    """Test pillar log generation tool."""
    server = create_proper_mcp_server()
    
    # Find the generate_pillar_logs tool
    pillar_tool = None
    for tool in server.tools:
        if tool.name == "generate_pillar_logs":
            pillar_tool = tool
            break
    
    assert pillar_tool is not None
    
    # Test tool execution
    result = pillar_tool.func(
        pillar="authentication",
        count=5,
        time_range="1h"
    )
    
    assert result is not None
    assert isinstance(result, str)  # Should return JSON string


def test_mcp_server_campaign_tool():
    """Test campaign log generation tool."""
    server = create_proper_mcp_server()
    
    # Find the generate_campaign_logs tool
    campaign_tool = None
    for tool in server.tools:
        if tool.name == "generate_campaign_logs":
            campaign_tool = tool
            break
    
    assert campaign_tool is not None
    
    # Test tool execution
    result = campaign_tool.func(
        threat_actor="APT29",
        duration="24h",
        target_count=10
    )
    
    assert result is not None
    assert isinstance(result, str)  # Should return JSON string


def test_mcp_server_correlated_tool():
    """Test correlated events generation tool."""
    server = create_proper_mcp_server()
    
    # Find the generate_correlated_logs tool
    correlated_tool = None
    for tool in server.tools:
        if tool.name == "generate_correlated_logs":
            correlated_tool = tool
            break
    
    assert correlated_tool is not None
    
    # Test tool execution
    result = correlated_tool.func(
        log_types="authentication,network_security",
        count=10,
        correlation_strength=0.7
    )
    
    assert result is not None
    assert isinstance(result, str)  # Should return JSON string


def test_mcp_server_export_tool():
    """Test log export tool."""
    server = create_proper_mcp_server()
    
    # Find the export_logs tool
    export_tool = None
    for tool in server.tools:
        if tool.name == "export_logs":
            export_tool = tool
            break
    
    assert export_tool is not None
    
    # Test tool execution with sample data
    sample_logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING"}
    ]
    
    result = export_tool.func(
        events_json=str(sample_logs),
        format="json",
        output_path="test_export"
    )
    
    assert result is not None
    assert isinstance(result, str)  # Should return success message


def test_mcp_server_analysis_tool():
    """Test log analysis tool."""
    server = create_proper_mcp_server()
    
    # Find the analyze_log_patterns tool
    analysis_tool = None
    for tool in server.tools:
        if tool.name == "analyze_log_patterns":
            analysis_tool = tool
            break
    
    assert analysis_tool is not None
    
    # Test tool execution with sample data
    sample_logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING"}
    ]
    
    result = analysis_tool.func(
        events_json=str(sample_logs),
        analysis_type="summary"
    )
    
    assert result is not None
    assert isinstance(result, str)  # Should return JSON string
