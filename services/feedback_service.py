import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from typing import Dict, List

load_dotenv()


class FeedbackService:
    def __init__(self):
        """Initialize OpenAI client for generating natural language feedback"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_enhanced_feedback(self, comparison_result: Dict) -> str:
        """
        Use AI to generate natural, actionable feedback from technical metrics

        Args:
            comparison_result: Dict containing similarity scores and technical feedback

        Returns:
            Natural language feedback string
        """
        similarity = comparison_result['overall_similarity']
        breakdown = comparison_result['similarity_breakdown']
        feedback_points = comparison_result['feedback_points']

        prompt = f"""You are a dance instructor reviewing a student's choreography performance.
Generate constructive, encouraging, and specific feedback based on these metrics:

Overall Match: {similarity}%

Performance Breakdown:
- Pose Accuracy: {breakdown['pose_accuracy']}%
- Timing Accuracy: {breakdown['timing_accuracy']}%
- Movement Smoothness: {breakdown['movement_smoothness']}%
- Angle Accuracy: {breakdown['angle_accuracy']}%

Specific Issues Found:
{json.dumps(feedback_points, indent=2)}

Generate feedback that:
1. Starts with a brief overall assessment
2. Highlights what they did well
3. Provides 3-5 specific, actionable improvements with timestamps
4. Ends with encouragement

Keep the tone supportive and motivating. Be specific about what movements need work."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a supportive dance instructor providing constructive feedback to students."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            return self._generate_fallback_feedback(comparison_result)

    def _generate_fallback_feedback(self, comparison_result: Dict) -> str:
        """Generate basic feedback if AI service fails"""
        similarity = comparison_result['overall_similarity']
        feedback_points = comparison_result['feedback_points']

        feedback = f"Overall Performance: {similarity}%\n\n"

        if similarity >= 80:
            feedback += "Excellent work! Your choreography closely matches the example.\n\n"
        elif similarity >= 65:
            feedback += "Good effort! You're on the right track with some areas to improve.\n\n"
        else:
            feedback += "Keep practicing! There are several areas that need attention.\n\n"

        feedback += "Areas for Improvement:\n"
        for point in feedback_points:
            if point['issue'] != 'None':
                feedback += f"- [{point['timestamp']}] {point['issue']}: {point['suggestion']}\n"

        return feedback
