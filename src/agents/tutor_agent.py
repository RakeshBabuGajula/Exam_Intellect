"""
Tutor Agent Module

This module implements the TutorAgent class responsible for post-exam analysis,
personalized learning plan generation, and remedial content creation for struggling students.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from ..integrations import call_gemini_llm, fact_check_with_openai

from ..session_manager import SessionManager

logger = logging.getLogger(__name__)

class TutorAgent:
    """
    AI Agent for personalized educational support and remedial help.

    This agent handles:
    - Post-exam performance analysis
    - Personalized learning plan generation
    - Tailored resource recommendations
    - Adaptive remedial content creation
    """

    def __init__(self, session_manager: SessionManager):
        """
        Initialize the Tutor Agent.

        Args:
            session_manager: Session manager for student tracking
        """
        self.session_manager = session_manager
        logger.info("TutorAgent initialized")

    def analyze_performance(self, student_id: str, exam_results: Dict) -> Dict:
        """
        Analyze student's exam performance and identify areas for improvement.

        Args:
            student_id: Unique identifier for the student
            exam_results: Dictionary containing exam scores and answers

        Returns:
            Dict: Performance analysis results
        """
        try:
            # Get student's historical data
            student_history = self.session_manager.get_student_history(student_id)

            # Calculate performance metrics
            analysis = self._calculate_performance_metrics(exam_results)

            # Identify weak areas
            weak_areas = self._identify_weak_areas(analysis)

            # Generate learning recommendations
            recommendations = self._generate_learning_recommendations(weak_areas, student_history)

            # Update student profile
            self.session_manager.update_student_profile(student_id, {
                'last_exam_score': analysis['overall_score'],
                'weak_areas': weak_areas,
                'learning_recommendations': recommendations
            })

            result = {
                'student_id': student_id,
                'analysis': analysis,
                'weak_areas': weak_areas,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Performance analysis completed for student: {student_id}")
            return result

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}

    def generate_learning_plan(self, student_id: str, weak_areas: List[str]) -> Dict:
        """
        Generate a personalized learning plan for the student.

        Args:
            student_id: Unique identifier for the student
            weak_areas: List of weak subject areas

        Returns:
            Dict: Personalized learning plan
        """
        try:
            # Get student profile
            student_profile = self.session_manager.get_student_profile(student_id)

            # Use LLM to generate comprehensive learning plan
            prompt = f"""
            Create a personalized learning plan for a student with the following profile:

            Student ID: {student_id}
            Weak Areas: {', '.join(weak_areas)}
            Previous Performance: {student_profile.get('last_exam_score', 'N/A')}
            Learning Style: {student_profile.get('learning_style', 'Not specified')}

            Generate a detailed 4-week learning plan including:
            1. Weekly objectives
            2. Daily study schedule
            3. Recommended resources and materials
            4. Practice exercises
            5. Assessment methods

            Format the response as a structured JSON object.
            """

            llm_response = call_gemini_llm(prompt)

            # Parse and structure the learning plan
            learning_plan = self._parse_learning_plan(llm_response)

            # Store the learning plan
            self.session_manager.update_student_profile(student_id, {
                'current_learning_plan': learning_plan,
                'plan_generated_date': datetime.now().isoformat()
            })

            logger.info(f"Learning plan generated for student: {student_id}")
            return learning_plan

        except Exception as e:
            logger.error(f"Learning plan generation failed: {e}")
            return {"error": str(e)}

    def create_remedial_content(self, student_id: str, topic: str, difficulty: str = "intermediate") -> Dict:
        """
        Create tailored remedial content for a specific topic.

        Args:
            student_id: Unique identifier for the student
            topic: The topic to create content for
            difficulty: Difficulty level (beginner/intermediate/advanced)

        Returns:
            Dict: Remedial content package
        """
        try:
            # Get student profile for personalization
            student_profile = self.session_manager.get_student_profile(student_id)

            prompt = f"""
            Create remedial educational content for the topic: {topic}

            Student Profile:
            - Difficulty Level: {difficulty}
            - Learning Style: {student_profile.get('learning_style', 'visual')}
            - Previous Weak Areas: {', '.join(student_profile.get('weak_areas', []))}

            Generate:
            1. A clear explanation of the topic
            2. Step-by-step examples
            3. Practice problems with solutions
            4. Common mistakes to avoid
            5. Additional resources for further study

            Make the content engaging and adapted to the student's needs.
            """

            content = call_gemini_llm(prompt)

            # Structure the content
            remedial_content = {
                'topic': topic,
                'difficulty': difficulty,
                'content': content,
                'generated_date': datetime.now().isoformat(),
                'student_id': student_id
            }

            # Store content for future reference
            self.session_manager.add_remedial_content(student_id, remedial_content)

            logger.info(f"Remedial content created for student {student_id} on topic: {topic}")
            return remedial_content

        except Exception as e:
            logger.error(f"Remedial content creation failed: {e}")
            return {"error": str(e)}

    def recommend_resources(self, student_id: str, topics: List[str]) -> List[Dict]:
        """
        Recommend learning resources based on student's needs.

        Args:
            student_id: Unique identifier for the student
            topics: List of topics to find resources for

        Returns:
            List[Dict]: List of recommended resources
        """
        try:
            resources = []

            for topic in topics:
                prompt = f"""
                Recommend high-quality learning resources for the topic: {topic}

                Include:
                - Online courses (Coursera, edX, Udemy)
                - YouTube channels/playlists
                - Books and textbooks
                - Interactive websites
                - Practice platforms

                Provide 3-5 recommendations with brief descriptions and URLs if available.
                """

                recommendations = call_gemini_llm(prompt)

                # Parse recommendations
                parsed_resources = self._parse_resource_recommendations(recommendations, topic)
                resources.extend(parsed_resources)

            # Store recommendations
            self.session_manager.update_student_profile(student_id, {
                'recommended_resources': resources,
                'resources_updated_date': datetime.now().isoformat()
            })

            logger.info(f"Resources recommended for student {student_id}")
            return resources

        except Exception as e:
            logger.error(f"Resource recommendation failed: {e}")
            return []

    def _calculate_performance_metrics(self, exam_results: Dict) -> Dict:
        """
        Calculate detailed performance metrics from exam results.

        Args:
            exam_results: Raw exam results data

        Returns:
            Dict: Calculated performance metrics
        """
        total_questions = len(exam_results.get('answers', []))
        correct_answers = sum(1 for answer in exam_results.get('answers', []) if answer.get('correct', False))

        overall_score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # Calculate scores by topic/category
        topic_scores = {}
        for answer in exam_results.get('answers', []):
            topic = answer.get('topic', 'General')
            if topic not in topic_scores:
                topic_scores[topic] = {'correct': 0, 'total': 0}
            topic_scores[topic]['total'] += 1
            if answer.get('correct', False):
                topic_scores[topic]['correct'] += 1

        # Calculate percentages
        for topic in topic_scores:
            correct = topic_scores[topic]['correct']
            total = topic_scores[topic]['total']
            topic_scores[topic]['percentage'] = (correct / total) * 100 if total > 0 else 0

        return {
            'overall_score': overall_score,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'topic_scores': topic_scores,
            'exam_duration': exam_results.get('duration', 0),
            'completion_rate': (len(exam_results.get('answers', [])) / total_questions) * 100 if total_questions > 0 else 0
        }

    def _identify_weak_areas(self, analysis: Dict) -> List[str]:
        """
        Identify weak areas based on performance analysis.

        Args:
            analysis: Performance analysis results

        Returns:
            List[str]: List of weak areas/topics
        """
        weak_areas = []

        # Topics with score below 70%
        for topic, scores in analysis.get('topic_scores', {}).items():
            if scores.get('percentage', 100) < 70:
                weak_areas.append(topic)

        # Overall performance indicators
        if analysis.get('overall_score', 100) < 60:
            weak_areas.append('General Knowledge')
        if analysis.get('completion_rate', 100) < 80:
            weak_areas.append('Time Management')

        return weak_areas

    def _generate_learning_recommendations(self, weak_areas: List[str], student_history: Dict) -> List[str]:
        """
        Generate learning recommendations based on weak areas and history.

        Args:
            weak_areas: List of weak subject areas
            student_history: Student's historical performance data

        Returns:
            List[str]: List of learning recommendations
        """
        recommendations = []

        for area in weak_areas:
            if area == 'Time Management':
                recommendations.extend([
                    "Practice time management techniques",
                    "Take regular breaks during study sessions",
                    "Use timers for practice exams"
                ])
            elif area == 'General Knowledge':
                recommendations.extend([
                    "Review fundamental concepts",
                    "Focus on understanding rather than memorization",
                    "Create concept maps for complex topics"
                ])
            else:
                recommendations.extend([
                    f"Dedicate extra time to studying {area}",
                    f"Find additional resources for {area}",
                    f"Practice more problems in {area}"
                ])

        # Personalized recommendations based on history
        if student_history.get('previous_weak_areas'):
            persistent_areas = set(weak_areas) & set(student_history['previous_weak_areas'])
            if persistent_areas:
                recommendations.append(f"Focus on persistent weak areas: {', '.join(persistent_areas)}")

        return recommendations

    def _parse_learning_plan(self, llm_response: str) -> Dict:
        """
        Parse LLM response into structured learning plan.

        Args:
            llm_response: Raw LLM response

        Returns:
            Dict: Structured learning plan
        """
        try:
            # Attempt to parse as JSON
            return json.loads(llm_response)
        except json.JSONDecodeError:
            # Fallback: structure manually
            return {
                'title': 'Personalized Learning Plan',
                'description': llm_response,
                'weeks': [],
                'generated_by': 'TutorAgent'
            }

    def _parse_resource_recommendations(self, recommendations: str, topic: str) -> List[Dict]:
        """
        Parse resource recommendations into structured format.

        Args:
            recommendations: Raw recommendations text
            topic: Topic the recommendations are for

        Returns:
            List[Dict]: List of structured resource recommendations
        """
        # Simple parsing - split by lines and create resource objects
        lines = recommendations.strip().split('\n')
        resources = []

        for line in lines:
            if line.strip() and not line.startswith('-'):
                resource = {
                    'topic': topic,
                    'title': line.strip(),
                    'type': 'General',
                    'description': 'Recommended resource'
                }
                resources.append(resource)

        return resources

    def get_student_progress(self, student_id: str) -> Dict:
        """
        Get student's learning progress and current status.

        Args:
            student_id: Unique identifier for the student

        Returns:
            Dict: Student progress information
        """
        try:
            profile = self.session_manager.get_student_profile(student_id)

            progress = {
                'student_id': student_id,
                'current_learning_plan': profile.get('current_learning_plan'),
                'completed_topics': profile.get('completed_topics', []),
                'upcoming_topics': profile.get('upcoming_topics', []),
                'recommended_resources': profile.get('recommended_resources', []),
                'last_updated': profile.get('last_updated')
            }

            return progress

        except Exception as e:
            logger.error(f"Failed to get student progress: {e}")
            return {"error": str(e)}
