#!/usr/bin/env python3
"""
ExamIntellect Main Entry Point

This script initializes and runs the ExamIntellect multi-agent AI system for online exam proctoring.
"""

import sys
import subprocess
from pathlib import Path
from flask import Flask

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.agents.proctor_agent import ProctorAgent
from src.agents.tutor_agent import TutorAgent
from src.agents.communication_agent import CommunicationAgent
from src.session_manager import SessionManager
from src.integrations import initialize_integrations

# Initialize Flask app for potential API endpoints
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

def main():
    """Main function to run ExamIntellect system."""
    print("🚀 Starting ExamIntellect AI Proctoring System...")

    # Initialize integrations
    print("🔗 Initializing API integrations...")
    initialize_integrations()

    # Initialize session manager
    print("📊 Initializing session manager...")
    session_manager = SessionManager()

    # Initialize agents
    print("🤖 Initializing AI agents...")
    # Added disable_face_filtering and debug_mode flags for proctor agent
    disable_face_filtering = False
    import argparse

    # Parse CLI arguments for debug_mode and disable_face_filtering
    parser = argparse.ArgumentParser(description="ExamIntellect CLI")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode with bounding boxes")
    parser.add_argument('--disable-face-filtering', action='store_true', help="Disable overlapping face filtering")
    args, unknown = parser.parse_known_args()

    debug_mode = args.debug
    disable_face_filtering = args.disable_face_filtering
    proctor = ProctorAgent(session_manager, disable_face_filtering=disable_face_filtering, debug_mode=debug_mode)
    tutor = TutorAgent(session_manager)
    communicator = CommunicationAgent(session_manager)

    print("✅ ExamIntellect system initialized successfully!")
    print("\nAvailable commands:")
    print("- start_proctoring: Begin exam monitoring")
    print("- generate_report: Generate session report")
    print("- dashboard: Launch Streamlit dashboard")
    print("- exit: Shutdown system")

    # Simple CLI interface for demo
    while True:
        try:
            command = input("\nEnter command: ").strip().lower()

            if command == 'start_proctoring':
                print("🎥 Starting proctoring session...")
                success = proctor.start_session("demo_student_001")
                if not success:
                    print("❌ Failed to start proctoring session")
                    continue

                print("▶️ Proctoring session started. Press 'q' to stop.")

                import cv2
                try:
                    while True:
                        if proctor.video_capture and proctor.video_capture.isOpened():
                            ret, frame = proctor.video_capture.read()
                            if not ret or frame is None:
                                print("⚠️ Failed to capture frame")
                                continue
                            cv2.imshow("Live Proctoring - demo_student_001", frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                print("🛑 'q' pressed, stopping proctoring session...")
                                break
                        else:
                            print("⚠️ Video capture device not initialized or closed")
                            break
                except KeyboardInterrupt:
                    print("\n🛑 KeyboardInterrupt received, stopping proctoring session...")
                finally:
                    proctor.stop_session()
                    cv2.destroyAllWindows()

            elif command == 'generate_report':
                print("📋 Generating session report...")
                # Get session data for the report
                session_data = session_manager.get_session_data("demo_student_001")

                # Create dummy exam results for demo
                exam_results = {
                    'exam_id': session_data.get('current_exam', 'demo_exam'),
                    'score': 85.0,
                    'total_questions': 20,
                    'correct_answers': 17,
                    'weak_areas': ['algebra', 'geometry']
                }

                # Create proctoring data from session
                proctoring_data = {
                    'duration': session_data.get('session_duration', 30),
                    'alerts_count': session_data.get('alerts_count', 0),
                    'suspicious_count': 0  # Would be calculated from alerts
                }

                report = communicator.generate_feedback_report("demo_student_001", exam_results, proctoring_data)
                print("📋 Session Report Generated:")
                print(f"Student ID: {report.get('student_id', 'N/A')}")
                print(f"Exam ID: {report.get('exam_id', 'N/A')}")
                print(f"Performance: {report.get('performance_summary', 'N/A')}")
                print(f"Proctoring: {report.get('proctoring_summary', 'N/A')}")
                print(f"Feedback: {report.get('feedback', 'N/A')}")

                # Send report via email
                email_sent = communicator.send_notification("grakesh2605@gmail.com", "feedback", report, "email")
                if email_sent:
                    print("📧 Report sent to grakesh2605@gmail.com")
                else:
                    print("❌ Failed to send report via email")

            elif command == 'dashboard':
                print("📊 Launching dashboard...")
                try:
                    subprocess.run(["streamlit", "run", "dashboard/app_final.py"], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to launch dashboard: {e}")
                except FileNotFoundError:
                    print("❌ Streamlit not found. Please install it with 'pip install streamlit'")

            elif command == 'exit':
                print("👋 Shutting down ExamIntellect...")
                break

            else:
                print("❓ Unknown command. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n👋 Shutting down ExamIntellect...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
