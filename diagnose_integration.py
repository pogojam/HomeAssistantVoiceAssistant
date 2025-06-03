#!/usr/bin/env python3
"""Diagnostic script for OpenAI Realtime Assistant integration."""

import os
import sys
import json

def check_integration():
    """Check if the integration is properly installed."""
    
    print("OpenAI Realtime Assistant Integration Diagnostic")
    print("=" * 50)
    
    # Check custom components directory
    custom_components = "/config/custom_components"
    integration_path = os.path.join(custom_components, "openai_realtime_assistant")
    
    print(f"\n1. Checking integration directory...")
    if os.path.exists(integration_path):
        print(f"   ✓ Integration directory exists: {integration_path}")
        
        # List files
        print(f"\n2. Files in integration directory:")
        for file in os.listdir(integration_path):
            file_path = os.path.join(integration_path, file)
            size = os.path.getsize(file_path) if os.path.isfile(file_path) else "DIR"
            print(f"   - {file} ({size} bytes)" if isinstance(size, int) else f"   - {file} ({size})")
            
        # Check required files
        required_files = ["__init__.py", "manifest.json", "services.yaml"]
        print(f"\n3. Checking required files:")
        for file in required_files:
            file_path = os.path.join(integration_path, file)
            if os.path.exists(file_path):
                print(f"   ✓ {file} exists")
                if file == "manifest.json":
                    with open(file_path, 'r') as f:
                        manifest = json.load(f)
                        print(f"     - Domain: {manifest.get('domain')}")
                        print(f"     - Version: {manifest.get('version')}")
                        print(f"     - Config flow: {manifest.get('config_flow')}")
            else:
                print(f"   ✗ {file} missing!")
                
    else:
        print(f"   ✗ Integration directory NOT found at: {integration_path}")
        print(f"\n   Checking other locations:")
        
        # Check if it's elsewhere
        for root, dirs, files in os.walk("/config"):
            if "openai_realtime_assistant" in dirs:
                print(f"   Found at: {os.path.join(root, 'openai_realtime_assistant')}")
                
    # Check configuration.yaml
    print(f"\n4. Checking configuration.yaml:")
    config_path = "/config/configuration.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            content = f.read()
            if "openai_realtime_assistant" in content:
                print("   ✓ Integration found in configuration.yaml")
                # Extract the config section
                lines = content.split('\n')
                in_section = False
                for line in lines:
                    if "openai_realtime_assistant:" in line:
                        in_section = True
                    elif in_section and line and not line.startswith(' '):
                        break
                    if in_section:
                        print(f"     {line}")
            else:
                print("   - Integration not found in configuration.yaml")
                
    # Check Home Assistant log
    print(f"\n5. Checking recent logs for errors:")
    log_path = "/config/home-assistant.log"
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()
            errors = []
            for line in lines[-100:]:  # Last 100 lines
                if "openai_realtime_assistant" in line.lower():
                    errors.append(line.strip())
                    
            if errors:
                print("   Recent mentions in logs:")
                for error in errors[-10:]:  # Last 10 mentions
                    print(f"   - {error}")
            else:
                print("   - No recent mentions of openai_realtime_assistant in logs")
                
    print(f"\n6. Quick fixes to try:")
    print("   1. Add to configuration.yaml if missing:")
    print("      openai_realtime_assistant:")
    print("        api_key: 'your-api-key'")
    print("   2. Restart Home Assistant:")
    print("      ha core restart")
    print("   3. Check logs after restart:")
    print("      ha core logs | grep openai")
    print("   4. Try adding via UI instead:")
    print("      Settings -> Devices & Services -> Add Integration")

if __name__ == "__main__":
    check_integration()