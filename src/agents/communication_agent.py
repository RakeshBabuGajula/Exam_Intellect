"""
Communication Agent Module

This module implements the CommunicationAgent class responsible for incident summarization,
feedback generation, automated reporting, and dispatching notifications via email/API.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
from typing import Dict, List
import logging
import os

from ..integrations import call_gemini_llm

from ..session_manager import SessionManager

logger = logging.getLogger(__name__)

class CommunicationAgent:
    """
    AI Agent for communication, reporting, and incident management.

    This agent handles:
    - Incident summarization and analysis
    - Automated report generation
    - Email and API notifications
    - Feedback generation and dispatch
    - Communication with stakeholders
    """

    def __init__(self, session_manager: SessionManager):
        """
        Initialize the Communication Agent.

        Args:
            session_manager: Session manager for student tracking
        """
        self.session_manager = session_manager

        # Email configuration (loaded from environment variables)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("EMAIL_USER", "examintelect@system.com")
        self.sender_password = os.getenv("EMAIL_PASS", "")

        # API endpoints (placeholders)
        self.api_endpoints = {
            'incident_report': 'https://api.examintelect.com/incidents',
            'notification': 'https://api.examintelect.com/notifications'
        }

        logger.info("CommunicationAgent initialized")

    def generate_incident_report(self, student_id: str, incident_data: Dict) -> Dict:
        """
        Generate a comprehensive incident report.

        Args:
            student_id: Unique identifier for the student
            incident_data: Details of the incident

        Returns:
            Dict: Structured incident report
        """
        try:
            # Get student profile and session data
            student_profile = self.session_manager.get_student_profile(student_id)
            session_data = self.session_manager.get_session_data(student_id)

            # Use AI to analyze and summarize the incident
            analysis = self._analyze_incident(incident_data, student_profile, session_data)

            # Generate detailed report
            report = {
                'incident_id': f"INC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'student_id': student_id,
                'timestamp': datetime.now().isoformat(),
                'incident_type': incident_data.get('type', 'unknown'),
                'severity': self._assess_severity(incident_data),
                'description': incident_data.get('description', ''),
                'evidence': incident_data.get('evidence', []),
                'analysis': analysis,
                'recommendations': self._generate_recommendations(incident_data, analysis),
                'student_profile': {
                    'name': student_profile.get('name', 'Unknown'),
                    'previous_incidents': student_profile.get('incident_count', 0),
                    'risk_level': student_profile.get('risk_level', 'low')
                },
                'session_context': {
                    'exam_id': session_data.get('current_exam'),
                    'session_duration': session_data.get('session_duration'),
                    'alerts_count': session_data.get('alerts_count', 0)
                }
            }

            # Store report
            self.session_manager.add_incident_report(student_id, report)

            logger.info(f"Incident report generated for student: {student_id}")
            return report

        except Exception as e:
            logger.error(f"Incident report generation failed: {e}")
            return {"error": str(e)}

    def send_notification(self, recipient: str, notification_type: str,
                         content: Dict, method: str = "email") -> bool:
        """
        Send notification to recipient via specified method.

        Args:
            recipient: Email address or API endpoint
            notification_type: Type of notification (alert, report, feedback)
            content: Notification content
            method: Communication method (email, api, sms)

        Returns:
            bool: True if notification sent successfully
        """
        try:
            if method == "email":
                return self._send_email_notification(recipient, notification_type, content)
            elif method == "api":
                return self._send_api_notification(recipient, notification_type, content)
            else:
                logger.error(f"Unsupported notification method: {method}")
                return False

        except Exception as e:
            logger.error(f"Notification sending failed: {e}")
            return False

    def generate_feedback_report(self, student_id: str, exam_results: Dict,
                               proctoring_data: Dict) -> Dict:
        """
        Generate comprehensive feedback report for student and stakeholders.

        Args:
            student_id: Unique identifier for the student
            exam_results: Exam performance data
            proctoring_data: Proctoring session data

        Returns:
            Dict: Comprehensive feedback report
        """
        try:
            # Get student profile
            student_profile = self.session_manager.get_student_profile(student_id)

            # Generate AI-powered feedback
            feedback = self._generate_ai_feedback(exam_results, proctoring_data, student_profile)

            # Structure the report
            report = {
                'student_id': student_id,
                'exam_id': exam_results.get('exam_id'),
                'generated_date': datetime.now().isoformat(),
                'performance_summary': self._summarize_performance(exam_results),
                'proctoring_summary': self._summarize_proctoring(proctoring_data),
                'feedback': feedback,
                'recommendations': self._generate_student_recommendations(exam_results, proctoring_data),
                'next_steps': self._suggest_next_steps(student_id, exam_results),
                'stakeholder_notifications': self._identify_notifications_needed(proctoring_data)
            }

            # Store feedback report
            self.session_manager.add_feedback_report(student_id, report)

            logger.info(f"Feedback report generated for student: {student_id}")
            return report

        except Exception as e:
            logger.error(f"Feedback report generation failed: {e}")
            return {"error": str(e)}

    def dispatch_reports(self, reports: List[Dict], recipients: List[str]) -> Dict:
        """
        Dispatch multiple reports to recipients.

        Args:
            reports: List of reports to dispatch
            recipients: List of recipient information

        Returns:
            Dict: Dispatch results
        """
        results = {
            'total_reports': len(reports),
            'successful_dispatches': 0,
            'failed_dispatches': 0,
            'details': []
        }

        for report in reports:
            for recipient in recipients:
                try:
                    success = self.send_notification(
                        recipient['contact'],
                        report['type'],
                        report,
                        recipient.get('method', 'email')
                    )

                    result_detail = {
                        'report_id': report.get('id', 'unknown'),
                        'recipient': recipient['contact'],
                        'method': recipient.get('method', 'email'),
                        'success': success
                    }

                    results['details'].append(result_detail)

                    if success:
                        results['successful_dispatches'] += 1
                    else:
                        results['failed_dispatches'] += 1

                except Exception as e:
                    logger.error(f"Failed to dispatch report to {recipient}: {e}")
                    results['failed_dispatches'] += 1
                    results['details'].append({
                        'report_id': report.get('id', 'unknown'),
                        'recipient': recipient['contact'],
                        'error': str(e),
                        'success': False
                    })

        logger.info(f"Report dispatch completed: {results['successful_dispatches']} successful, "
                   f"{results['failed_dispatches']} failed")
        return results

    def _analyze_incident(self, incident_data: Dict, student_profile: Dict,
                         session_data: Dict) -> str:
        """
        Use AI to analyze incident details and provide insights.

        Args:
            incident_data: Incident details
            student_profile: Student profile information
            session_data: Session context

        Returns:
            str: AI analysis of the incident
        """
        try:
            prompt = f"""
            Analyze this exam proctoring incident:

            Incident Type: {incident_data.get('type', 'unknown')}
            Description: {incident_data.get('description', '')}
            Severity: {self._assess_severity(incident_data)}
            Evidence: {', '.join(incident_data.get('evidence', []))}

            Student Profile:
            - Previous incidents: {student_profile.get('incident_count', 0)}
            - Risk level: {student_profile.get('risk_level', 'low')}

            Session Context:
            - Exam ID: {session_data.get('current_exam', 'unknown')}
            - Session duration: {session_data.get('session_duration', 'unknown')}
            - Alerts during session: {session_data.get('alerts_count', 0)}

            Provide a detailed analysis of this incident, including:
            1. Assessment of the situation
            2. Potential implications
            3. Recommended actions
            4. Risk assessment
            """

            return call_gemini_llm(prompt)

        except Exception as e:
            logger.error(f"Incident analysis failed: {e}")
            return "Analysis unavailable due to technical issues."

    def _assess_severity(self, incident_data: Dict) -> str:
        """
        Assess the severity of an incident.

        Args:
            incident_data: Incident details

        Returns:
            str: Severity level (low, medium, high, critical)
        """
        incident_type = incident_data.get('type', 'unknown')
        evidence_count = len(incident_data.get('evidence', []))
        description = incident_data.get('description', '').lower()

        # Severity assessment logic
        if 'multiple_faces' in incident_type or 'external_help' in description:
            return 'critical'
        elif 'no_face' in incident_type or evidence_count > 3:
            return 'high'
        elif 'gaze_abnormal' in incident_type or evidence_count > 1:
            return 'medium'
        else:
            return 'low'

    def _generate_recommendations(self, incident_data: Dict, analysis: str) -> List[str]:
        """
        Generate recommendations based on incident analysis.

        Args:
            incident_data: Incident details
            analysis: AI analysis text

        Returns:
            List[str]: List of recommendations
        """
        recommendations = []

        severity = self._assess_severity(incident_data)

        if severity == 'critical':
            recommendations.extend([
                "Immediately pause the exam",
                "Conduct manual verification",
                "Notify exam administrator",
                "Document incident with video evidence"
            ])
        elif severity == 'high':
            recommendations.extend([
                "Increase monitoring intensity",
                "Send warning to student",
                "Log incident for review",
                "Consider additional verification steps"
            ])
        elif severity == 'medium':
            recommendations.extend([
                "Monitor student closely",
                "Document the incident",
                "Review session recording",
                "Consider follow-up actions"
            ])
        else:
            recommendations.extend([
                "Log incident for records",
                "Monitor for patterns",
                "No immediate action required"
            ])

        return recommendations

    def _send_email_notification(self, recipient: str, notification_type: str,
                               content: Dict) -> bool:
        """
        Send email notification.

        Args:
            recipient: Email address
            notification_type: Type of notification
            content: Notification content

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = f"ExamIntellect {notification_type.title()} Notification"

            # Format email body
            body = self._format_email_body(notification_type, content)
            msg.attach(MIMEText(body, 'html'))

            # Send email using actual SMTP credentials
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email notification sent to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False

    def _send_api_notification(self, endpoint: str, notification_type: str,
                             content: Dict) -> bool:
        """
        Send API notification.

        Args:
            endpoint: API endpoint URL
            notification_type: Type of notification
            content: Notification content

        Returns:
            bool: True if API call successful
        """
        try:
            logger.info(f"API notification sent to {endpoint} (simulated)")
            return True

        except Exception as e:
            logger.error(f"API notification failed: {e}")
            return False

    def _format_email_body(self, notification_type: str, content: Dict) -> str:
        """
        Format email body based on notification type.

        Args:
            notification_type: Type of notification
            content: Notification content

        Returns:
            str: Formatted HTML email body
        """
        if notification_type == 'incident':
            return f"""
            <html>
            <body>
                <h2>ExamIntellect Incident Alert</h2>
                <p><strong>Incident ID:</strong> {content.get('incident_id', 'N/A')}</p>
                <p><strong>Student ID:</strong> {content.get('student_id', 'N/A')}</p>
                <p><strong>Type:</strong> {content.get('incident_type', 'N/A')}</p>
                <p><strong>Severity:</strong> {content.get('severity', 'N/A')}</p>
                <p><strong>Description:</strong> {content.get('description', 'N/A')}</p>
                <h3>Analysis:</h3>
                <p>{content.get('analysis', 'N/A')}</p>
                <h3>Recommendations:</h3>
                <ul>
                {"".join(f"<li>{rec}</li>" for rec in content.get('recommendations', []))}
                </ul>
            </body>
            </html>
            """
        elif notification_type == 'feedback':
            return f"""
            <html>
            <body>
                <h2>ExamIntellect Feedback Report</h2>
                <p><strong>Student ID:</strong> {content.get('student_id', 'N/A')}</p>
                <p><strong>Exam ID:</strong> {content.get('exam_id', 'N/A')}</p>
                <h3>Performance Summary:</h3>
                <p>{content.get('performance_summary', 'N/A')}</p>
                <h3>Feedback:</h3>
                <p>{content.get('feedback', 'N/A')}</p>
                <h3>Recommendations:</h3>
                <ul>
                {"".join(f"<li>{rec}</li>" for rec in content.get('recommendations', []))}
                </ul>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body>
                <h2>ExamIntellect Notification</h2>
                <pre>{json.dumps(content, indent=2)}</pre>
            </body>
            </html>
            """

    def _generate_ai_feedback(self, exam_results: Dict, proctoring_data: Dict,
                            student_profile: Dict) -> str:
        """
        Generate AI-powered feedback using Gemini LLM.

        Args:
            exam_results: Exam performance data
            proctoring_data: Proctoring session data
            student_profile: Student profile

        Returns:
            str: AI-generated feedback
        """
        try:
            prompt = f"""
            Generate constructive feedback for a student based on their exam performance and proctoring session:

            Exam Results:
            - Score: {exam_results.get('score', 'N/A')}%
            - Total Questions: {exam_results.get('total_questions', 'N/A')}
            - Correct Answers: {exam_results.get('correct_answers', 'N/A')}
            - Weak Areas: {', '.join(exam_results.get('weak_areas', []))}

            Proctoring Data:
            - Session Duration: {proctoring_data.get('duration', 'N/A')} minutes
            - Alerts: {proctoring_data.get('alerts_count', 0)}
            - Suspicious Activities: {proctoring_data.get('suspicious_count', 0)}

            Student Profile:
            - Previous Performance: {student_profile.get('average_score', 'N/A')}%
            - Risk Level: {student_profile.get('risk_level', 'low')}

            Provide encouraging, constructive feedback that:
            1. Acknowledges strengths and improvements
            2. Addresses areas for growth
            3. Offers specific recommendations
            4. Maintains a positive, supportive tone
            """

            return call_gemini_llm(prompt)

        except Exception as e:
            logger.error(f"AI feedback generation failed: {e}")
            return "Personalized feedback unavailable due to technical issues."

    def _summarize_performance(self, exam_results: Dict) -> str:
        """
        Create a summary of exam performance.

        Args:
            exam_results: Exam results data

        Returns:
            str: Performance summary
        """
        score = exam_results.get('score', 0)
        total = exam_results.get('total_questions', 0)
        correct = exam_results.get('correct_answers', 0)

        if score >= 90:
            grade = "Excellent"
        elif score >= 80:
            grade = "Good"
        elif score >= 70:
            grade = "Satisfactory"
        elif score >= 60:
            grade = "Needs Improvement"
        else:
            grade = "Requires Significant Improvement"

        return f"{grade} performance with {correct}/{total} correct answers ({score}%)."

    def _summarize_proctoring(self, proctoring_data: Dict) -> str:
        """
        Create a summary of proctoring session.

        Args:
            proctoring_data: Proctoring data

        Returns:
            str: Proctoring summary
        """
        duration = proctoring_data.get('duration', 0)
        alerts = proctoring_data.get('alerts_count', 0)
        suspicious = proctoring_data.get('suspicious_count', 0)

        if suspicious == 0 and alerts < 3:
            status = "Clean session"
        elif suspicious < 3 and alerts < 10:
            status = "Minor irregularities noted"
        else:
            status = "Significant irregularities detected"

        return f"{status}. Session lasted {duration} minutes with {alerts} alerts and {suspicious} suspicious activities."

    def _generate_student_recommendations(self, exam_results: Dict,
                                        proctoring_data: Dict) -> List[str]:
        """
        Generate recommendations for the student.

        Args:
            exam_results: Exam results
            proctoring_data: Proctoring data

        Returns:
            List[str]: Student recommendations
        """
        recommendations = []

        # Based on exam performance
        score = exam_results.get('score', 0)
        weak_areas = exam_results.get('weak_areas', [])

        if score < 70:
            recommendations.append("Focus on fundamental concepts in weak areas")
            recommendations.extend([f"Practice more problems in {area}" for area in weak_areas[:3]])

        # Based on proctoring data
        suspicious = proctoring_data.get('suspicious_count', 0)
        if suspicious > 0:
            recommendations.append("Ensure proper testing environment for future exams")
            recommendations.append("Review exam guidelines and procedures")

        if not recommendations:
            recommendations.append("Continue current study habits and maintain focus during exams")

        return recommendations

    def _suggest_next_steps(self, student_id: str, exam_results: Dict) -> List[str]:
        """
        Suggest next steps for the student.

        Args:
            student_id: Student ID
            exam_results: Exam results

        Returns:
            List[str]: Next steps suggestions
        """
        score = exam_results.get('score', 0)

        if score >= 90:
            return ["Consider advanced topics", "Mentor other students", "Take on leadership roles"]
        elif score >= 80:
            return ["Maintain current study routine", "Explore related subjects", "Participate in study groups"]
        elif score >= 70:
            return ["Schedule tutoring sessions", "Review weak areas thoroughly", "Practice with past exams"]
        else:
            return ["Seek immediate academic support", "Develop structured study plan", "Consider academic counseling"]

    def _identify_notifications_needed(self, proctoring_data: Dict) -> List[str]:
        """
        Identify which stakeholders need to be notified.

        Args:
            proctoring_data: Proctoring session data

        Returns:
            List[str]: List of stakeholders to notify
        """
        notifications = ["Student"]

        suspicious = proctoring_data.get('suspicious_count', 0)
        alerts = proctoring_data.get('alerts_count', 0)

        if suspicious > 5 or alerts > 15:
            notifications.extend(["Exam Administrator", "Academic Advisor", "Parents/Guardians"])
        elif suspicious > 2 or alerts > 8:
            notifications.extend(["Exam Administrator", "Academic Advisor"])
        elif suspicious > 0 or alerts > 3:
            notifications.append("Academic Advisor")

        return notifications
