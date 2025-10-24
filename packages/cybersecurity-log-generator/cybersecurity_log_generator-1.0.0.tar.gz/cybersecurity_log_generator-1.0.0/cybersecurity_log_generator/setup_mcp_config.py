#!/usr/bin/env python3
"""
MCP Configuration Setup Script
Helps users set up MCP configuration for Claude Desktop and Cursor.
"""

import os
import json
import sys
import platform
from pathlib import Path

class MCPConfigSetup:
    """Setup MCP configuration for different applications."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.system = platform.system().lower()
        self.home = Path.home()
        
    def get_config_paths(self):
        """Get configuration file paths for different applications."""
        if self.system == "darwin":  # macOS
            return {
                "claude_desktop": self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
                "cursor": self.home / "Library" / "Application Support" / "Cursor" / "mcp_config.json"
            }
        elif self.system == "windows":
            return {
                "claude_desktop": self.home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
                "cursor": self.home / "AppData" / "Roaming" / "Cursor" / "mcp_config.json"
            }
        else:  # Linux
            return {
                "claude_desktop": self.home / ".config" / "claude" / "claude_desktop_config.json",
                "cursor": self.home / ".config" / "cursor" / "mcp_config.json"
            }
    
    def create_basic_config(self, use_virtual_env=True):
        """Create basic MCP configuration."""
        if use_virtual_env:
            config = {
                "mcpServers": {
                    "cybersecurity-log-generator": {
                        "command": str(self.project_root / "venv" / "bin" / "python"),
                        "args": [str(self.project_root / "server.py")]
                    }
                }
            }
        else:
            config = {
                "mcpServers": {
                    "cybersecurity-log-generator": {
                        "command": "python",
                        "args": [str(self.project_root / "server.py")],
                        "env": {
                            "PYTHONPATH": str(self.project_root)
                        }
                    }
                }
            }
        return config
    
    def create_advanced_config(self, log_level="INFO", config_file=None):
        """Create advanced MCP configuration with additional options."""
        args = [str(self.project_root / "server.py")]
        
        if log_level:
            args.extend(["--log-level", log_level])
        
        if config_file:
            args.extend(["--config", str(config_file)])
        
        config = {
            "mcpServers": {
                "cybersecurity-log-generator": {
                    "command": str(self.project_root / "venv" / "bin" / "python"),
                    "args": args,
                    "env": {
                        "PYTHONPATH": str(self.project_root),
                        "LOG_LEVEL": log_level
                    }
                }
            }
        }
        return config
    
    def setup_claude_desktop(self, use_virtual_env=True, log_level=None):
        """Setup Claude Desktop configuration."""
        print("🔧 Setting up Claude Desktop MCP configuration...")
        
        config_paths = self.get_config_paths()
        config_path = config_paths["claude_desktop"]
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create configuration
        if log_level:
            config = self.create_advanced_config(log_level=log_level)
        else:
            config = self.create_basic_config(use_virtual_env=use_virtual_env)
        
        # Write configuration file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Claude Desktop configuration created at: {config_path}")
        print("📝 Next steps:")
        print("   1. Restart Claude Desktop")
        print("   2. Open a new conversation")
        print("   3. Test with: 'Generate 100 IDS logs'")
        
        return config_path
    
    def setup_cursor(self, use_virtual_env=True, log_level=None):
        """Setup Cursor MCP configuration."""
        print("🔧 Setting up Cursor MCP configuration...")
        
        config_paths = self.get_config_paths()
        config_path = config_paths["cursor"]
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create configuration
        if log_level:
            config = self.create_advanced_config(log_level=log_level)
        else:
            config = self.create_basic_config(use_virtual_env=use_virtual_env)
        
        # Write configuration file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Cursor configuration created at: {config_path}")
        print("📝 Next steps:")
        print("   1. Restart Cursor")
        print("   2. Open a new chat")
        print("   3. Test with: 'Create an APT29 attack campaign'")
        
        return config_path
    
    def test_configuration(self):
        """Test the MCP server configuration."""
        print("🧪 Testing MCP server configuration...")
        
        try:
            # Test server creation
            sys.path.insert(0, str(self.project_root))
            from mcp.server import create_mcp_server
            
            server = create_mcp_server()
            print(f"✅ MCP server created successfully: {server.name}")
            
            # Test basic functionality
            print("✅ Server is ready for use")
            return True
            
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            print("🔧 Troubleshooting steps:")
            print("   1. Check if virtual environment is activated")
            print("   2. Install dependencies: pip install -r requirements.txt")
            print("   3. Verify server.py exists and is executable")
            return False
    
    def show_configuration_info(self):
        """Show configuration information."""
        print("📋 MCP Configuration Information")
        print("=" * 50)
        
        config_paths = self.get_config_paths()
        
        print(f"System: {self.system}")
        print(f"Project Root: {self.project_root}")
        print(f"Virtual Environment: {self.project_root / 'venv'}")
        print(f"Server Script: {self.project_root / 'server.py'}")
        print()
        
        print("Configuration File Paths:")
        for app, path in config_paths.items():
            print(f"  {app}: {path}")
        print()
        
        print("Available Configuration Options:")
        print("  1. Basic configuration (recommended)")
        print("  2. Advanced configuration with logging")
        print("  3. Custom configuration")
        print()
        
        print("Test Commands:")
        print("  python test_mcp_server.py")
        print("  python test_llm_mcp_integration.py")
        print("  python test_complete_mcp_demo.py")
    
    def interactive_setup(self):
        """Interactive setup process."""
        print("🚀 MCP Configuration Setup")
        print("=" * 50)
        
        # Show current information
        self.show_configuration_info()
        
        # Test current configuration
        if not self.test_configuration():
            print("❌ Current configuration has issues. Please fix them first.")
            return False
        
        print("\n📝 Setup Options:")
        print("1. Setup Claude Desktop")
        print("2. Setup Cursor")
        print("3. Setup Both")
        print("4. Show configuration info only")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            self.setup_claude_desktop()
        elif choice == "2":
            self.setup_cursor()
        elif choice == "3":
            self.setup_claude_desktop()
            print()
            self.setup_cursor()
        elif choice == "4":
            self.show_configuration_info()
        else:
            print("❌ Invalid choice")
            return False
        
        print("\n🎉 Setup complete!")
        return True


def main():
    """Main function."""
    setup = MCPConfigSetup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "claude":
            setup.setup_claude_desktop()
        elif command == "cursor":
            setup.setup_cursor()
        elif command == "both":
            setup.setup_claude_desktop()
            setup.setup_cursor()
        elif command == "test":
            setup.test_configuration()
        elif command == "info":
            setup.show_configuration_info()
        else:
            print("❌ Unknown command. Use: claude, cursor, both, test, or info")
            return 1
    else:
        setup.interactive_setup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
