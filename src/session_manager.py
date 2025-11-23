"""
Session Manager Module

This module implements the SessionManager class responsible for managing
student sessions, profiles, and long-term tracking for the EduGuard system.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages student sessions, profiles, and persistent data storage.

    This class handles:
    - Student profile management
    - Session tracking and storage
    - Alert logging and retrieval
    - Performance history
    - Risk assessment and flagging
    """

    def __init__(self, db_path: str = "eduguard.db"):
        """
        Initialize the session manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._initialize_database()
        logger.info(f"SessionManager initialized with database: {db_path}")

    def _initialize_database(self):
        """Initialize the database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Students table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS students (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        profile_data TEXT,
                        risk_level TEXT DEFAULT 'low',
                        created_date TEXT,
                        last_updated TEXT
                    )
                ''')

                # Sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        student_id TEXT,
                        exam_id TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration INTEGER,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (student_id) REFERENCES students (id)
                    )
                ''')

                # Alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        student_id TEXT,
                        alert_type TEXT,
                        description TEXT,
                        severity TEXT,
                        timestamp TEXT,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                        FOREIGN KEY (student_id) REFERENCES students (id)
                    )
                ''')

                # Performance records table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT,
                        exam_id TEXT,
                        score REAL,
                        max_score REAL,
                        duration INTEGER,
                        weak_areas TEXT,
                        timestamp TEXT,
                        FOREIGN KEY (student_id) REFERENCES students (id)
                    )
                ''')

                # Remedial content table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS remedial_content (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT,
                        topic TEXT,
                        content TEXT,
                        difficulty TEXT,
                        generated_date TEXT,
                        FOREIGN KEY (student_id) REFERENCES students (id)
                    )
                ''')

                # Feedback reports table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT,
                        exam_id TEXT,
                        report_data TEXT,
                        generated_date TEXT,
                        FOREIGN KEY (student_id) REFERENCES students (id)
                    )
                ''')

                # Incident reports table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incident_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT,
                        incident_data TEXT,
                        severity TEXT,
                        status TEXT DEFAULT 'open',
                        created_date TEXT,
                        resolved_date TEXT,
                        FOREIGN KEY (student_id) REFERENCES students (id)
                    )
                ''')

                conn.commit()
                logger.info("Database schema initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def create_student_profile(self, student_id: str, name: str = "",
                             email: str = "", profile_data: Dict = None) -> bool:
        """
        Create a new student profile.

        Args:
            student_id: Unique identifier for the student
            name: Student's name
            email: Student's email
            profile_data: Additional profile information

        Returns:
            bool: True if profile created successfully
        """
        try:
            profile_data = profile_data or {}
            profile_data.update({
                'learning_style': profile_data.get('learning_style', 'visual'),
                'previous_experience': profile_data.get('previous_experience', 'beginner'),
                'subjects_of_interest': profile_data.get('subjects_of_interest', [])
            })

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO students
                    (id, name, email, profile_data, created_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    student_id,
                    name,
                    email,
                    json.dumps(profile_data),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()

            logger.info(f"Student profile created for: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create student profile: {e}")
            return False

    def get_student_profile(self, student_id: str) -> Dict:
        """
        Retrieve a student's profile.

        Args:
            student_id: Unique identifier for the student

        Returns:
            Dict: Student profile data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
                row = cursor.fetchone()

                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'email': row[2],
                        'profile_data': json.loads(row[3]) if row[3] else {},
                        'risk_level': row[4],
                        'created_date': row[5],
                        'last_updated': row[6]
                    }
                else:
                    return {}

        except Exception as e:
            logger.error(f"Failed to get student profile: {e}")
            return {}

    def update_student_profile(self, student_id: str, updates: Dict) -> bool:
        """
        Update a student's profile with new information.

        Args:
            student_id: Unique identifier for the student
            updates: Dictionary of fields to update

        Returns:
            bool: True if profile updated successfully
        """
        try:
            # Get current profile
            current_profile = self.get_student_profile(student_id)
            if not current_profile:
                logger.warning(f"Student profile not found: {student_id}")
                return False

            # Update profile data
            profile_data = current_profile.get('profile_data', {})
            profile_data.update(updates.get('profile_data', {}))

            # Update risk level if provided
            risk_level = updates.get('risk_level', current_profile.get('risk_level', 'low'))

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE students
                    SET profile_data = ?, risk_level = ?, last_updated = ?
                    WHERE id = ?
                ''', (
                    json.dumps(profile_data),
                    risk_level,
                    datetime.now().isoformat(),
                    student_id
                ))
                conn.commit()

            logger.info(f"Student profile updated for: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update student profile: {e}")
            return False

    def start_session(self, student_id: str, exam_id: str = None) -> Optional[str]:
        """
        Start a new proctoring session for a student.

        Args:
            student_id: Unique identifier for the student
            exam_id: Unique identifier for the exam

        Returns:
            Optional[str]: Session ID if created successfully, None otherwise
        """
        try:
            session_id = f"session_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sessions
                    (session_id, student_id, exam_id, start_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    student_id,
                    exam_id,
                    datetime.now().isoformat(),
                    'active'
                ))
                conn.commit()

            logger.info(f"Session started: {session_id} for student: {student_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return None

    def end_session(self, session_id: str, duration: int = None) -> bool:
        """
        End a proctoring session.

        Args:
            session_id: Unique identifier for the session
            duration: Session duration in minutes

        Returns:
            bool: True if session ended successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions
                    SET end_time = ?, duration = ?, status = ?
                    WHERE session_id = ?
                ''', (
                    datetime.now().isoformat(),
                    duration,
                    'completed',
                    session_id
                ))
                conn.commit()

            logger.info(f"Session ended: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False

    def add_alert(self, session_id: str, alert_type: str, description: str,
                  severity: str) -> bool:
        """
        Add an alert to a session.

        Args:
            session_id: Unique identifier for the session
            alert_type: Type of alert
            description: Alert description
            severity: Alert severity level

        Returns:
            bool: True if alert added successfully
        """
        try:
            # Get student_id from session
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT student_id FROM sessions WHERE session_id = ?',
                             (session_id,))
                row = cursor.fetchone()
                student_id = row[0] if row else None

                if not student_id:
                    logger.warning(f"Session not found: {session_id}")
                    return False

                cursor.execute('''
                    INSERT INTO alerts
                    (session_id, student_id, alert_type, description, severity, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    student_id,
                    alert_type,
                    description,
                    severity,
                    datetime.now().isoformat()
                ))
                conn.commit()

            # Update student's risk level based on alerts
            self._update_risk_level(student_id)

            logger.info(f"Alert added to session {session_id}: {alert_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to add alert: {e}")
            return False

    def get_session_data(self, student_id: str) -> Dict:
        """
        Get session data for a student.

        Args:
            student_id: Unique identifier for the student

        Returns:
            Dict: Session data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get active session
                cursor.execute('''
                    SELECT * FROM sessions
                    WHERE student_id = ? AND status = 'active'
                    ORDER BY start_time DESC LIMIT 1
                ''', (student_id,))
                session_row = cursor.fetchone()

                # Get alert count for active session
                alerts_count = 0
                if session_row:
                    cursor.execute('''
                        SELECT COUNT(*) FROM alerts WHERE session_id = ?
                    ''', (session_row[0],))
                    alerts_count = cursor.fetchone()[0]

                session_data = {
                    'current_exam': session_row[2] if session_row else None,
                    'session_duration': None,  # Would calculate from start time
                    'alerts_count': alerts_count,
                    'status': session_row[6] if session_row else 'inactive'
                }

                return session_data

        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return {}

    def get_student_history(self, student_id: str) -> Dict:
        """
        Get a student's complete history.

        Args:
            student_id: Unique identifier for the student

        Returns:
            Dict: Student history data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get all sessions
                cursor.execute('''
                    SELECT * FROM sessions WHERE student_id = ?
                    ORDER BY start_time DESC
                ''', (student_id,))
                sessions = cursor.fetchall()

                # Get all alerts
                cursor.execute('''
                    SELECT * FROM alerts WHERE student_id = ?
                    ORDER BY timestamp DESC
                ''', (student_id,))
                alerts = cursor.fetchall()

                # Get performance records
                cursor.execute('''
                    SELECT * FROM performance_records WHERE student_id = ?
                    ORDER BY timestamp DESC
                ''', (student_id,))
                performances = cursor.fetchall()

                return {
                    'sessions': [{
                        'session_id': s[0],
                        'exam_id': s[2],
                        'start_time': s[3],
                        'end_time': s[4],
                        'duration': s[5],
                        'status': s[6]
                    } for s in sessions],
                    'alerts': [{
                        'id': a[0],
                        'session_id': a[1],
                        'alert_type': a[3],
                        'description': a[4],
                        'severity': a[5],
                        'timestamp': a[6]
                    } for a in alerts],
                    'performances': [{
                        'id': p[0],
                        'exam_id': p[2],
                        'score': p[3],
                        'max_score': p[4],
                        'duration': p[5],
                        'weak_areas': json.loads(p[6]) if p[6] else [],
                        'timestamp': p[7]
                    } for p in performances]
                }

        except Exception as e:
            logger.error(f"Failed to get student history: {e}")
            return {}

    def add_performance_record(self, student_id: str, exam_id: str, score: float,
                             max_score: float, duration: int, weak_areas: List[str]) -> bool:
        """
        Add a performance record for a student.

        Args:
            student_id: Unique identifier for the student
            exam_id: Unique identifier for the exam
            score: Student's score
            max_score: Maximum possible score
            duration: Time taken in minutes
            weak_areas: List of weak subject areas

        Returns:
            bool: True if record added successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO performance_records
                    (student_id, exam_id, score, max_score, duration, weak_areas, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    student_id,
                    exam_id,
                    score,
                    max_score,
                    duration,
                    json.dumps(weak_areas),
                    datetime.now().isoformat()
                ))
                conn.commit()

            logger.info(f"Performance record added for student: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add performance record: {e}")
            return False

    def add_remedial_content(self, student_id: str, content: Dict) -> bool:
        """
        Add remedial content for a student.

        Args:
            student_id: Unique identifier for the student
            content: Remedial content data

        Returns:
            bool: True if content added successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO remedial_content
                    (student_id, topic, content, difficulty, generated_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    student_id,
                    content.get('topic', ''),
                    content.get('content', ''),
                    content.get('difficulty', 'intermediate'),
                    content.get('generated_date', datetime.now().isoformat())
                ))
                conn.commit()

            logger.info(f"Remedial content added for student: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add remedial content: {e}")
            return False

    def add_feedback_report(self, student_id: str, report: Dict) -> bool:
        """
        Add a feedback report for a student.

        Args:
            student_id: Unique identifier for the student
            report: Feedback report data

        Returns:
            bool: True if report added successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO feedback_reports
                    (student_id, exam_id, report_data, generated_date)
                    VALUES (?, ?, ?, ?)
                ''', (
                    student_id,
                    report.get('exam_id', ''),
                    json.dumps(report),
                    report.get('generated_date', datetime.now().isoformat())
                ))
                conn.commit()

            logger.info(f"Feedback report added for student: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add feedback report: {e}")
            return False

    def add_incident_report(self, student_id: str, report: Dict) -> bool:
        """
        Add an incident report.

        Args:
            student_id: Unique identifier for the student
            report: Incident report data

        Returns:
            bool: True if report added successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO incident_reports
                    (student_id, incident_data, severity, created_date)
                    VALUES (?, ?, ?, ?)
                ''', (
                    student_id,
                    json.dumps(report),
                    report.get('severity', 'low'),
                    report.get('timestamp', datetime.now().isoformat())
                ))
                conn.commit()

            logger.info(f"Incident report added for student: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add incident report: {e}")
            return False

    def _update_risk_level(self, student_id: str):
        """
        Update a student's risk level based on their alert history.

        Args:
            student_id: Unique identifier for the student
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Count alerts in the last 30 days
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute('''
                    SELECT COUNT(*) FROM alerts
                    WHERE student_id = ? AND timestamp > ?
                ''', (student_id, thirty_days_ago))
                recent_alerts = cursor.fetchone()[0]

                # Count high/critical severity alerts
                cursor.execute('''
                    SELECT COUNT(*) FROM alerts
                    WHERE student_id = ? AND severity IN ('high', 'critical')
                ''', (student_id,))
                severe_alerts = cursor.fetchone()[0]

                # Determine risk level
                if severe_alerts >= 5 or recent_alerts >= 15:
                    risk_level = 'critical'
                elif severe_alerts >= 2 or recent_alerts >= 8:
                    risk_level = 'high'
                elif recent_alerts >= 3:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'

                # Update risk level
                cursor.execute('''
                    UPDATE students SET risk_level = ?, last_updated = ?
                    WHERE id = ?
                ''', (risk_level, datetime.now().isoformat(), student_id))
                conn.commit()

                logger.info(f"Risk level updated for student {student_id}: {risk_level}")

        except Exception as e:
            logger.error(f"Failed to update risk level: {e}")

    def get_system_stats(self) -> Dict:
        """
        Get system-wide statistics.

        Returns:
            Dict: System statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Count total students
                cursor.execute('SELECT COUNT(*) FROM students')
                total_students = cursor.fetchone()[0]

                # Count active sessions
                cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
                active_sessions = cursor.fetchone()[0]

                # Count total alerts today
                today = datetime.now().date().isoformat()
                cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp LIKE ?", (f"{today}%",))
                alerts_today = cursor.fetchone()[0]

                # Count high-risk students
                cursor.execute("SELECT COUNT(*) FROM students WHERE risk_level IN ('high', 'critical')")
                high_risk_students = cursor.fetchone()[0]

                return {
                    'total_students': total_students,
                    'active_sessions': active_sessions,
                    'alerts_today': alerts_today,
                    'high_risk_students': high_risk_students,
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 365):
        """
        Clean up old data from the database.

        Args:
            days_to_keep: Number of days of data to keep
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete old alerts
                cursor.execute('DELETE FROM alerts WHERE timestamp < ?', (cutoff_date,))

                # Delete old performance records
                cursor.execute('DELETE FROM performance_records WHERE timestamp < ?', (cutoff_date,))

                # Delete old feedback reports
                cursor.execute('DELETE FROM feedback_reports WHERE generated_date < ?', (cutoff_date,))

                conn.commit()

            logger.info(f"Cleaned up data older than {days_to_keep} days")

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
