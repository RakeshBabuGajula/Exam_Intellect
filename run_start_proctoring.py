#!/usr/bin/env python3
"""
Script to run start_proctoring command non-interactively.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.agents.proctor_agent import ProctorAgent
from src.session_manager import SessionManager
from src.integrations import initialize_integrations

def main():
    print("🚀 Starting EduGuard AI Proctoring System...")

    # Initialize integrations
    print("🔗 Initializing API integrations...")
    initialize_integrations()

    # Initialize session manager
    print("📊 Initializing session manager...")
    session_manager = SessionManager()

    # Initialize proctor agent
    print("🤖 Initializing Proctor Agent...")
    proctor = ProctorAgent(session_manager)

    print("✅ System initialized successfully!")

    # Start proctoring session
    print("🎥 Starting proctoring session...")
    success = proctor.start_session("demo_student_001")

    if success:
        print("✅ Proctoring session started successfully!")
        print("Press Ctrl+C to stop the session.")
        try:
            # Keep running until interrupted
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopping proctoring session...")
            proctor.stop_session()
            print("✅ Session stopped.")
    else:
        print("❌ Failed to start proctoring session.")

if __name__ == "__main__":
    main()
