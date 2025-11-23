"""
Proctor Agent Module

This module implements the ProctorAgent class responsible for real-time
audio/video analysis and behavioral monitoring during online exams.
"""

import cv2
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import logging
import os

# Conditional imports for optional dependencies
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    logging.warning("speech_recognition not available. Audio analysis disabled.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("numpy not available. Some video processing features disabled.")

from src.integrations import analyze_behavior_with_gemini

from ..session_manager import SessionManager

logger = logging.getLogger(__name__)

class ProctorAgent:
    """
    AI Agent for real-time exam proctoring and behavioral analysis.

    This agent handles:
    - Video stream analysis for suspicious behavior
    - Audio monitoring and analysis
    - Facial recognition and gaze tracking
    - Real-time alert generation
    - Integration with AI analysis services
    """

    def __init__(self, session_manager: SessionManager, disable_face_filtering: bool = False, debug_mode: bool = False):
        """
        Initialize the Proctor Agent.

        Args:
            session_manager: Session manager for tracking student sessions
            disable_face_filtering: If True, skip filtering overlapping face detections
            debug_mode: If True, draw bounding boxes on detected faces for debugging
        """
        self.session_manager = session_manager
        self.is_monitoring = False
        self.current_session = None
        self.video_capture = None
        self.audio_recognizer = None
        self.monitoring_thread = None
        self.disable_face_filtering = disable_face_filtering
        self.debug_mode = debug_mode

        # Configuration
        self.alert_thresholds = {
            'face_not_visible': 5,  # seconds
            'multiple_faces': 1,    # count (lowered for faster detection)
            'gaze_abnormal': 10,    # seconds
            'audio_anomaly': 3      # detections
        }

        # State tracking
        self.face_last_seen = None
        self.multiple_faces_count = 0
        self.gaze_abnormal_start = None
        self.audio_anomalies = []

        # Callbacks
        self.alert_callbacks: List[Callable] = []

        logger.info("ProctorAgent initialized")

    def start_session(self, student_id: str, exam_id: str = None) -> bool:
        """
        Start proctoring for a student session.

        Args:
            student_id: Unique identifier for the student
            exam_id: Unique identifier for the exam (optional)

        Returns:
            bool: True if session started successfully
        """
        try:
            if self.is_monitoring:
                logger.warning("Proctoring session already active")
                return False

            # Start session in database
            session_id = self.session_manager.start_session(student_id, exam_id or "unknown")
            if not session_id:
                logger.error("Failed to create session in database")
                return False

            self.current_session = {
                'session_id': session_id,
                'student_id': student_id,
                'exam_id': exam_id,
                'start_time': datetime.now()
            }

            # Initialize video capture
            if not self._initialize_video_capture():
                logger.error("Failed to initialize video capture")
                return False

            # Initialize audio recognition
            if SPEECH_AVAILABLE:
                self.audio_recognizer = sr.Recognizer()

            # Start monitoring thread
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()

            logger.info(f"Proctoring session started for student: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start proctoring session: {e}")
            self._cleanup()
            return False

    def stop_session(self) -> bool:
        """
        Stop the current proctoring session.

        Returns:
            bool: True if session stopped successfully
        """
        try:
            if not self.is_monitoring:
                logger.warning("No active proctoring session")
                return False

            self.is_monitoring = False

            # Wait for monitoring thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)

            # End session in database
            if self.current_session:
                duration = int((datetime.now() - self.current_session['start_time']).total_seconds() / 60)
                self.session_manager.end_session(self.current_session['session_id'], duration)

            # Cleanup resources
            self._cleanup()

            logger.info("Proctoring session stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop proctoring session: {e}")
            return False

    def add_alert_callback(self, callback: Callable):
        """
        Add a callback function to be called when alerts are generated.

        Args:
            callback: Function to call with alert data
        """
        self.alert_callbacks.append(callback)

    def _initialize_video_capture(self) -> bool:
        """
        Initialize video capture device.

        Returns:
            bool: True if video capture initialized successfully
        """
        try:
            # Try to open default camera (index 0)
            self.video_capture = cv2.VideoCapture(0)

            if not self.video_capture.isOpened():
                logger.error("Could not open video capture device")
                return False

            # Set video properties for better performance
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.video_capture.set(cv2.CAP_PROP_FPS, 30)

            logger.info("Video capture initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Video capture initialization failed: {e}")
            return False

    def _monitoring_loop(self):
        """
        Main monitoring loop that runs in a separate thread.
        """
        logger.info("Starting monitoring loop")

        frame_count = 0
        last_analysis_time = time.time()

        consecutive_failures = 0
        max_consecutive_failures = 5

        try:
            while self.is_monitoring and self.video_capture and self.video_capture.isOpened():
                ret, frame = self.video_capture.read()

                if not ret or frame is None:
                    consecutive_failures += 1
                    logger.warning(f"Failed to read frame from video capture (EOF or camera disconnected) - failure {consecutive_failures}/{max_consecutive_failures}")

                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("Maximum consecutive frame read failures reached, attempting camera reinitialization")
                        # Try to reinitialize camera
                        if not self._initialize_video_capture():
                            logger.error("Failed to reinitialize camera, stopping monitoring")
                            self._generate_alert('camera_failure', 'Camera disconnected and could not be recovered', 'critical')
                            self.is_monitoring = False
                            break
                        else:
                            consecutive_failures = 0
                            logger.info("Camera successfully reinitialized")
                    else:
                        time.sleep(1)
                    continue

                # Reset failure counter on successful read
                consecutive_failures = 0
                frame_count += 1

                # Process frame for behavioral analysis
                self._process_video_frame(frame)

                # Periodic AI analysis (every 30 seconds)
                current_time = time.time()
                if current_time - last_analysis_time > 30:
                    self._perform_ai_analysis(frame)
                    last_analysis_time = current_time

                # Audio monitoring (if available)
                if SPEECH_AVAILABLE and frame_count % 150 == 0:  # Every 5 seconds at 30fps
                    self._monitor_audio()

                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            logger.info("Monitoring loop ended")

    def _process_video_frame(self, frame):
        """
        Process a video frame for behavioral analysis.

        Args:
            frame: Video frame from camera
        """
        try:
            # Basic face detection using OpenCV
            if not hasattr(cv2, 'CascadeClassifier'):
                return

            # Load face cascade (this would be cached in production)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces with adjusted parameters for better filtering
            detected_faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,        # Increase scaleFactor for more robust detection
                minNeighbors=5,         # Increase minNeighbors to reduce false positives
                minSize=(50, 50)        # Ignore small detections (filter by face size)
            )

            # Debug: log detected faces count before filtering
            logger.debug(f"Detected faces count before filtering: {len(detected_faces)}")

            # Apply filtering to merge overlapping or duplicate face detections (if not disabled)
            if self.disable_face_filtering:
                faces = detected_faces
            else:
                faces = self._filter_overlapping_faces(detected_faces)

            # Debug: log detected faces count after filtering
            logger.debug(f"Detected faces count after filtering: {len(faces)}")

            # If debug mode enabled, draw rectangles around detected faces
            if self.debug_mode:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Show debug frame window
                cv2.imshow("Debug - Detected Faces", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.is_monitoring = False

            # Analyze face detection results
            self._analyze_face_detection(faces, frame.shape)

        except Exception as e:
            logger.error(f"Frame processing failed: {e}")

    def _analyze_face_detection(self, faces, frame_shape):
        """
        Analyze face detection results and generate alerts.

        Args:
            faces: Detected faces from OpenCV
            frame_shape: Shape of the video frame
        """
        current_time = datetime.now()

        if len(faces) == 0:
            # No face detected
            if self.face_last_seen is None:
                self.face_last_seen = current_time
            elif (current_time - self.face_last_seen).seconds > self.alert_thresholds['face_not_visible']:
                self._generate_alert('face_not_visible',
                                   f"No face detected for {self.alert_thresholds['face_not_visible']} seconds",
                                   'medium')

        elif len(faces) == 1:
            # Single face detected - reset counters
            self.face_last_seen = None
            self.multiple_faces_count = 0

            # Check face position (basic gaze estimation)
            face = faces[0]
            frame_center_x = frame_shape[1] / 2
            face_center_x = face[0] + face[2] / 2

            # Simple gaze check - face should be roughly centered
            if abs(face_center_x - frame_center_x) > frame_shape[1] * 0.3:  # 30% deviation
                if self.gaze_abnormal_start is None:
                    self.gaze_abnormal_start = current_time
                elif (current_time - self.gaze_abnormal_start).seconds > self.alert_thresholds['gaze_abnormal']:
                    self._generate_alert('gaze_abnormal',
                                       f"Unusual gaze direction for {self.alert_thresholds['gaze_abnormal']} seconds",
                                       'low')
            else:
                self.gaze_abnormal_start = None

        else:
            # Multiple faces detected
            self.multiple_faces_count += 1
            # Alert immediately on first multiple face detection frame
            if self.multiple_faces_count >= self.alert_thresholds['multiple_faces']:  
                self._generate_alert('multiple_faces',
                                   f"Multiple faces detected ({len(faces)} faces)",
                                   'high')

    def _monitor_audio(self):
        """
        Monitor audio for suspicious activity.
        """
        if not SPEECH_AVAILABLE or not self.audio_recognizer:
            return

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise to improve recognition
                self.audio_recognizer.adjust_for_ambient_noise(source, duration=1)
                # Listen for 5 seconds
                audio = self.audio_recognizer.listen(source, timeout=5, phrase_time_limit=5)

                # Attempt to recognize speech
                try:
                    text = self.audio_recognizer.recognize_google(audio)

                    # Check for suspicious keywords
                    suspicious_keywords = ['help', 'answer', 'look', 'someone', 'phone', 'whisper']
                    detected_keywords = [word for word in suspicious_keywords if word.lower() in text.lower()]

                    if detected_keywords:
                        self.audio_anomalies.append({
                            'text': text,
                            'keywords': detected_keywords,
                            'timestamp': datetime.now().isoformat()
                        })

                        if len(self.audio_anomalies) >= self.alert_thresholds['audio_anomaly']:
                            self._generate_alert('audio_anomaly',
                                               f"Suspicious audio detected: '{text}'",
                                               'high')

                except sr.UnknownValueError:
                    # No speech detected - this is normal
                    pass
                except sr.RequestError as e:
                    logger.error(f"Speech recognition request failed: {e}")

        except sr.WaitTimeoutError:
            logger.info("Audio monitoring: No audio input detected within timeout")
        except Exception as e:
            logger.error(f"Audio monitoring failed: {e}")

    def _perform_ai_analysis(self, frame):
        """
        Perform AI-powered analysis of the current frame.

        Args:
            frame: Current video frame
        """
        try:
            # Convert frame to description for AI analysis
            # In production, this would use more sophisticated computer vision
            frame_description = self._describe_frame(frame)

            # Analyze with Gemini
            analysis = analyze_behavior_with_gemini(frame_description)

            # Process analysis results
            if analysis.get('risk_level') in ['high', 'critical']:
                self._generate_alert('ai_behavior_analysis',
                                   f"AI detected suspicious behavior: {analysis.get('concerns', ['Unknown'])}",
                                   analysis.get('risk_level', 'medium'))

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")

    def _describe_frame(self, frame) -> str:
        """
        Generate a text description of the video frame.

        Args:
            frame: Video frame

        Returns:
            str: Text description of the frame
        """
        # Basic frame description
        # In production, this would use computer vision models
        height, width = frame.shape[:2]

        description = f"Video frame {width}x{height} pixels"

        # Add basic analysis
        if self.face_last_seen:
            seconds_since_face = (datetime.now() - self.face_last_seen).seconds
            description += f", no face visible for {seconds_since_face} seconds"
        else:
            description += ", face visible"

        if self.multiple_faces_count > 0:
            description += f", multiple faces detected (count: {self.multiple_faces_count})"

        return description

    def _generate_alert(self, alert_type: str, description: str, severity: str):
        """
        Generate an alert and notify callbacks.

        Args:
            alert_type: Type of alert
            description: Alert description
            severity: Alert severity
        """
        try:
            alert_data = {
                'type': alert_type,
                'description': description,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.current_session['session_id'] if self.current_session else None,
                'student_id': self.current_session['student_id'] if self.current_session else None
            }

            # Add alert to session
            if self.current_session:
                self.session_manager.add_alert(
                    self.current_session['session_id'],
                    alert_type,
                    description,
                    severity
                )

            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert_data)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")

            logger.warning(f"Alert generated: {alert_type} - {description}")

        except Exception as e:
            logger.error(f"Failed to generate alert: {e}")

    def _cleanup(self):
        """
        Clean up resources.
        """
        try:
            self.is_monitoring = False
            self.current_session = None

            if self.video_capture and self.video_capture.isOpened():
                self.video_capture.release()

            self.video_capture = None
            self.audio_recognizer = None
            self.monitoring_thread = None

            # Reset state
            self.face_last_seen = None
            self.multiple_faces_count = 0
            self.gaze_abnormal_start = None
            self.audio_anomalies = []

            logger.info("ProctorAgent resources cleaned up")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def _filter_overlapping_faces(self, faces):
        """
        Filter overlapping or duplicate face detections to reduce false multiple faces.

        Args:
            faces: List or array of face bounding boxes (x, y, w, h)

        Returns:
            List of filtered face bounding boxes
        """
        if len(faces) == 0:
            return faces

        filtered_faces = []
        for i, (x1, y1, w1, h1) in enumerate(faces):
            overlap = False
            for j, (x2, y2, w2, h2) in enumerate(faces):
                if i == j:
                    continue
                # Calculate overlap area
                dx = min(x1 + w1, x2 + w2) - max(x1, x2)
                dy = min(y1 + h1, y2 + h2) - max(y1, y2)
                if dx > 0 and dy > 0:
                    overlap_area = dx * dy
                    area1 = w1 * h1
                    area2 = w2 * h2
                    # If overlap is significant (e.g., more than 50% of either face), mark as overlapping
                    if overlap_area / area1 > 0.5 or overlap_area / area2 > 0.5:
                        overlap = True
                        break
            # Add face only if no significant overlap found against others processed so far
            if not overlap:
                filtered_faces.append((x1, y1, w1, h1))

        return filtered_faces

    def get_session_status(self) -> Dict:
        """
        Get the current session status.

        Returns:
            Dict: Session status information
        """
        if not self.current_session:
            return {'status': 'inactive'}

        return {
            'status': 'active' if self.is_monitoring else 'inactive',
            'session_id': self.current_session['session_id'],
            'student_id': self.current_session['student_id'],
            'exam_id': self.current_session['exam_id'],
            'start_time': self.current_session['start_time'].isoformat(),
            'duration': (datetime.now() - self.current_session['start_time']).total_seconds() / 60,
            'alerts_count': len(self.audio_anomalies),  # Simplified
            'video_capture_active': self.video_capture is not None and self.video_capture.isOpened()
        }

    def __del__(self):
        """
        Destructor to ensure cleanup.
        """
        self._cleanup()
