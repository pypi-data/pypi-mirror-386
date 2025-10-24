#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Entry Point for Universal Tester UI
Launches the Chainlit web interface
"""

import sys
import os
import subprocess
from pathlib import Path


def main():
    """Launch the Chainlit UI"""
    
    # Get the directory containing chainlit_ui.py
    ui_dir = Path(__file__).parent
    chainlit_ui_path = ui_dir / "chainlit_ui.py"
    
    if not chainlit_ui_path.exists():
        print("❌ Error: chainlit_ui.py not found!")
        print(f"Expected location: {chainlit_ui_path}")
        sys.exit(1)
    
    print("🚀 Starting Universal Tester Web UI...")
    print("📍 Access the UI at: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("")
    
    # Launch Chainlit
    try:
        subprocess.run([
            sys.executable, "-m", "chainlit", "run", 
            str(chainlit_ui_path),
            "--host", "0.0.0.0",
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n� Shutting down Universal Tester UI...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Chainlit: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Chainlit not found!")
        print("Please install it with: pip install chainlit")
        sys.exit(1)


if __name__ == "__main__":
    main()
