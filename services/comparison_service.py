import numpy as np
from dtaidistance import dtw
from scipy.spatial.distance import cosine, euclidean
from typing import Dict, List, Tuple
import json


class ComparisonService:
    def __init__(self):
        """Initialize comparison service"""
        self.similarity_threshold = 0.7  # Threshold for determining good match

    def compare_videos(
        self,
        example_pose_data: Dict,
        assignment_pose_data: Dict,
        focus_areas: List[str] = None
    ) -> Dict:
        """
        Compare two videos using pose data

        Returns comprehensive comparison results with similarity scores and feedback points
        """
        example_poses = example_pose_data['poses']
        assignment_poses = assignment_pose_data['poses']

        # Filter out None poses
        example_poses_clean = [p for p in example_poses if p is not None]
        assignment_poses_clean = [p for p in assignment_poses if p is not None]

        if not example_poses_clean or not assignment_poses_clean:
            return {
                'error': 'Could not detect poses in one or both videos',
                'overall_similarity': 0
            }

        # Convert poses to feature vectors
        example_features = self._poses_to_features(example_poses_clean, focus_areas)
        assignment_features = self._poses_to_features(assignment_poses_clean, focus_areas)

        # Perform DTW alignment
        alignment = self._dtw_align(example_features, assignment_features)

        # Calculate similarity metrics
        similarities = self._calculate_similarities(
            example_features,
            assignment_features,
            alignment,
            example_pose_data['timestamps'],
            assignment_pose_data['timestamps']
        )

        # Analyze movement quality
        movement_analysis = self._analyze_movement_quality(
            example_poses_clean,
            assignment_poses_clean,
            alignment
        )

        # Generate detailed feedback points
        feedback_points = self._generate_feedback_points(
            similarities,
            movement_analysis,
            example_pose_data['timestamps'],
            assignment_pose_data['timestamps'],
            alignment
        )

        # Calculate overall score
        overall_similarity = self._calculate_overall_score(similarities, movement_analysis)

        return {
            'overall_similarity': round(overall_similarity * 100, 1),
            'similarity_breakdown': {
                'pose_accuracy': round(similarities['pose_similarity'] * 100, 1),
                'timing_accuracy': round(similarities['timing_similarity'] * 100, 1),
                'movement_smoothness': round(movement_analysis['smoothness_score'] * 100, 1),
                'angle_accuracy': round(similarities['angle_similarity'] * 100, 1)
            },
            'feedback_points': feedback_points,
            'alignment': alignment,
            'detailed_metrics': {
                'frame_similarities': similarities['frame_scores'],
                'movement_metrics': movement_analysis
            }
        }

    def _poses_to_features(self, poses: List[Dict], focus_areas: List[str] = None) -> np.ndarray:
        """Convert pose keypoints to feature vectors"""
        features = []

        for pose in poses:
            if pose is None:
                # Use zero vector for missing poses
                features.append(np.zeros(66))  # 33 landmarks * 2 (x, y)
                continue

            feature_vector = []

            # Extract x, y coordinates for each landmark
            for landmark_name in sorted(pose.keys()):
                if landmark_name == 'angles':
                    continue

                landmark = pose[landmark_name]
                feature_vector.extend([landmark['x'], landmark['y']])

            # Pad if necessary
            while len(feature_vector) < 66:
                feature_vector.append(0)

            features.append(feature_vector[:66])

        return np.array(features)

    def _dtw_align(self, example_features: np.ndarray, assignment_features: np.ndarray) -> Dict:
        """
        Perform Dynamic Time Warping to align two sequences

        Returns alignment mapping
        """
        # For multivariate sequences, calculate distance for each dimension and average
        # Or use Euclidean distance for each frame pair
        try:
            # Use DTW with Euclidean distance for each frame
            from scipy.spatial.distance import euclidean

            # Calculate distance matrix
            n, m = len(example_features), len(assignment_features)
            dist_matrix = np.zeros((n, m))

            for i in range(n):
                for j in range(m):
                    dist_matrix[i, j] = euclidean(example_features[i], assignment_features[j])

            # Use DTW to find optimal path
            # Simple DTW implementation
            dtw_matrix = np.zeros((n + 1, m + 1))
            dtw_matrix[0, :] = np.inf
            dtw_matrix[:, 0] = np.inf
            dtw_matrix[0, 0] = 0

            for i in range(1, n + 1):
                for j in range(1, m + 1):
                    cost = dist_matrix[i-1, j-1]
                    dtw_matrix[i, j] = cost + min(
                        dtw_matrix[i-1, j],    # insertion
                        dtw_matrix[i, j-1],    # deletion
                        dtw_matrix[i-1, j-1]   # match
                    )

            distance = dtw_matrix[n, m]

            # Backtrack to find path
            path = []
            i, j = n, m
            while i > 0 and j > 0:
                path.append((i-1, j-1))

                # Find minimum of three directions
                candidates = [
                    (dtw_matrix[i-1, j], i-1, j),      # up
                    (dtw_matrix[i, j-1], i, j-1),      # left
                    (dtw_matrix[i-1, j-1], i-1, j-1)   # diagonal
                ]
                min_val, i, j = min(candidates, key=lambda x: x[0])

            path.reverse()

            # Normalize distance
            max_len = max(len(example_features), len(assignment_features))
            normalized_distance = distance / (max_len * 10)  # Scale factor

            return {
                'distance': float(distance),
                'normalized_distance': float(min(normalized_distance, 1.0)),
                'path': path,
                'alignment_quality': max(0, 1 - normalized_distance)
            }
        except Exception as e:
            print(f"DTW error: {e}")
            # Fallback: simple linear alignment
            n, m = len(example_features), len(assignment_features)
            path = [(i, int(i * m / n)) for i in range(n)]
            return {
                'distance': 0.0,
                'normalized_distance': 0.5,
                'path': path,
                'alignment_quality': 0.5
            }

    def _calculate_similarities(
        self,
        example_features: np.ndarray,
        assignment_features: np.ndarray,
        alignment: Dict,
        example_timestamps: List[float],
        assignment_timestamps: List[float]
    ) -> Dict:
        """Calculate various similarity metrics"""

        path = alignment['path']
        frame_scores = []

        # Calculate similarity for each aligned frame pair
        for ex_idx, as_idx in path:
            if ex_idx < len(example_features) and as_idx < len(assignment_features):
                # Cosine similarity
                cos_sim = 1 - cosine(example_features[ex_idx], assignment_features[as_idx])
                frame_scores.append(max(0, cos_sim))
            else:
                frame_scores.append(0)

        pose_similarity = np.mean(frame_scores)

        # Timing similarity (based on DTW alignment quality)
        timing_similarity = alignment['alignment_quality']

        # Angle similarity (if angles available)
        angle_similarity = self._calculate_angle_similarity(
            example_features,
            assignment_features,
            path
        )

        return {
            'pose_similarity': float(pose_similarity),
            'timing_similarity': float(timing_similarity),
            'angle_similarity': float(angle_similarity),
            'frame_scores': frame_scores
        }

    def _calculate_angle_similarity(
        self,
        example_features: np.ndarray,
        assignment_features: np.ndarray,
        path: List[Tuple[int, int]]
    ) -> float:
        """Calculate similarity based on joint angles"""
        # This is a simplified version - ideally would compare actual angles
        # from the pose data
        angle_diffs = []

        for ex_idx, as_idx in path:
            if ex_idx < len(example_features) and as_idx < len(assignment_features):
                diff = euclidean(example_features[ex_idx], assignment_features[as_idx])
                angle_diffs.append(diff)

        if not angle_diffs:
            return 0.0

        avg_diff = np.mean(angle_diffs)
        # Normalize to 0-1 scale (lower diff = higher similarity)
        similarity = max(0, 1 - (avg_diff / 2))

        return float(similarity)

    def _analyze_movement_quality(
        self,
        example_poses: List[Dict],
        assignment_poses: List[Dict],
        alignment: Dict
    ) -> Dict:
        """Analyze movement smoothness, speed, and other qualities"""

        # Calculate velocities
        example_velocities = self._calculate_velocities(example_poses)
        assignment_velocities = self._calculate_velocities(assignment_poses)

        # Calculate smoothness (inverse of jerk/acceleration changes)
        example_smoothness = self._calculate_smoothness(example_poses)
        assignment_smoothness = self._calculate_smoothness(assignment_poses)

        # Compare velocities
        velocity_similarity = self._compare_velocities(example_velocities, assignment_velocities)

        # Smoothness score
        smoothness_score = 1 - abs(example_smoothness - assignment_smoothness)

        return {
            'example_velocities': example_velocities,
            'assignment_velocities': assignment_velocities,
            'velocity_similarity': float(velocity_similarity),
            'example_smoothness': float(example_smoothness),
            'assignment_smoothness': float(assignment_smoothness),
            'smoothness_score': float(smoothness_score),
            'is_too_stiff': bool(assignment_smoothness < 0.5),
            'is_too_fast': bool(np.mean(assignment_velocities) > np.mean(example_velocities) * 1.3),
            'is_too_slow': bool(np.mean(assignment_velocities) < np.mean(example_velocities) * 0.7)
        }

    def _calculate_velocities(self, poses: List[Dict]) -> List[float]:
        """Calculate movement velocity between frames"""
        velocities = []

        for i in range(1, len(poses)):
            if poses[i] is None or poses[i-1] is None:
                velocities.append(0)
                continue

            # Calculate displacement of key points
            displacement = 0
            count = 0

            for key in ['left_wrist', 'right_wrist', 'left_ankle', 'right_ankle']:
                if key in poses[i] and key in poses[i-1]:
                    dx = poses[i][key]['x'] - poses[i-1][key]['x']
                    dy = poses[i][key]['y'] - poses[i-1][key]['y']
                    displacement += np.sqrt(dx**2 + dy**2)
                    count += 1

            if count > 0:
                velocities.append(displacement / count)
            else:
                velocities.append(0)

        return velocities

    def _calculate_smoothness(self, poses: List[Dict]) -> float:
        """Calculate movement smoothness (0-1, higher is smoother)"""
        velocities = self._calculate_velocities(poses)

        if len(velocities) < 2:
            return 0.5

        # Calculate acceleration changes (jerk)
        accelerations = np.diff(velocities)
        jerks = np.diff(accelerations)

        if len(jerks) == 0:
            return 0.5

        # Lower jerk = smoother movement
        avg_jerk = np.mean(np.abs(jerks))
        smoothness = max(0, 1 - avg_jerk * 10)  # Scale appropriately

        return float(smoothness)

    def _compare_velocities(self, vel1: List[float], vel2: List[float]) -> float:
        """Compare velocity profiles"""
        if not vel1 or not vel2:
            return 0.0

        avg_vel1 = np.mean(vel1)
        avg_vel2 = np.mean(vel2)

        if avg_vel1 == 0:
            return 0.0

        ratio = min(avg_vel2, avg_vel1) / max(avg_vel2, avg_vel1)
        return float(ratio)

    def _generate_feedback_points(
        self,
        similarities: Dict,
        movement_analysis: Dict,
        example_timestamps: List[float],
        assignment_timestamps: List[float],
        alignment: Dict
    ) -> List[Dict]:
        """Generate specific feedback points with timestamps"""
        feedback = []

        # Find problem areas (low similarity frames)
        frame_scores = similarities['frame_scores']
        path = alignment['path']

        # Identify segments with low similarity
        problem_segments = []
        current_segment = None

        for i, score in enumerate(frame_scores):
            if score < 0.6:  # Threshold for problem areas
                if i < len(path):
                    ex_idx, as_idx = path[i]
                    timestamp = example_timestamps[ex_idx] if ex_idx < len(example_timestamps) else 0

                    if current_segment is None:
                        current_segment = {'start': timestamp, 'end': timestamp, 'scores': [score]}
                    else:
                        current_segment['end'] = timestamp
                        current_segment['scores'].append(score)
            else:
                if current_segment is not None:
                    problem_segments.append(current_segment)
                    current_segment = None

        if current_segment is not None:
            problem_segments.append(current_segment)

        # Generate feedback for problem segments
        for segment in problem_segments:
            avg_score = np.mean(segment['scores'])
            feedback.append({
                'timestamp': f"{self._format_time(segment['start'])} - {self._format_time(segment['end'])}",
                'issue': 'Pose mismatch',
                'severity': 'high' if avg_score < 0.4 else 'medium',
                'suggestion': f"Review your positioning during this segment. Pose accuracy: {int(avg_score * 100)}%"
            })

        # Movement speed feedback
        if movement_analysis['is_too_fast']:
            feedback.append({
                'timestamp': 'Overall',
                'issue': 'Movement speed too fast',
                'severity': 'medium',
                'suggestion': f"Slow down your movements by ~{int((1 - movement_analysis['velocity_similarity']) * 100)}% to match the example tempo"
            })
        elif movement_analysis['is_too_slow']:
            feedback.append({
                'timestamp': 'Overall',
                'issue': 'Movement speed too slow',
                'severity': 'medium',
                'suggestion': f"Speed up your movements by ~{int((1 - movement_analysis['velocity_similarity']) * 100)}% to match the example tempo"
            })

        # Smoothness feedback
        if movement_analysis['is_too_stiff']:
            feedback.append({
                'timestamp': 'Overall',
                'issue': 'Stiff or jerky movements',
                'severity': 'medium',
                'suggestion': 'Try to move more fluidly and smoothly. Focus on smooth transitions between poses.'
            })

        # If no major issues, give positive feedback
        if not feedback:
            feedback.append({
                'timestamp': 'Overall',
                'issue': 'None',
                'severity': 'none',
                'suggestion': 'Great job! Your choreography closely matches the example.'
            })

        return feedback

    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _calculate_overall_score(self, similarities: Dict, movement_analysis: Dict) -> float:
        """Calculate weighted overall similarity score"""
        weights = {
            'pose_similarity': 0.40,
            'timing_similarity': 0.25,
            'angle_similarity': 0.20,
            'smoothness': 0.15
        }

        score = (
            similarities['pose_similarity'] * weights['pose_similarity'] +
            similarities['timing_similarity'] * weights['timing_similarity'] +
            similarities['angle_similarity'] * weights['angle_similarity'] +
            movement_analysis['smoothness_score'] * weights['smoothness']
        )

        return float(score)
