import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Tuple
import json


class PoseExtractionService:
    def __init__(self):
        """Initialize MediaPipe Pose model"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # 0, 1, or 2 (2 is most accurate)
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def extract_poses_from_video(self, video_path: str, focus_areas: List[str] = None) -> Dict:
        """
        Extract pose keypoints from video

        Args:
            video_path: Path to video file
            focus_areas: List of body parts to focus on (e.g., ['upper_body', 'arms', 'legs'])
                       If None, tracks all body parts

        Returns:
            Dict containing frames, poses, fps, and metadata
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        poses = []
        frame_numbers = []
        timestamps = []

        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process frame
            results = self.pose.process(rgb_frame)

            if results.pose_landmarks:
                # Extract keypoints
                keypoints = self._extract_keypoints(
                    results.pose_landmarks,
                    focus_areas
                )
                poses.append(keypoints)
                frame_numbers.append(frame_idx)
                timestamps.append(frame_idx / fps)
            else:
                # If no pose detected, add None
                poses.append(None)
                frame_numbers.append(frame_idx)
                timestamps.append(frame_idx / fps)

            frame_idx += 1

        cap.release()

        return {
            'poses': poses,
            'frame_numbers': frame_numbers,
            'timestamps': timestamps,
            'fps': fps,
            'total_frames': frame_count,
            'duration': duration,
            'focus_areas': focus_areas or ['full_body']
        }

    def _extract_keypoints(self, landmarks, focus_areas: List[str] = None) -> Dict:
        """
        Extract keypoint coordinates from MediaPipe landmarks

        Returns dict with x, y, z, visibility for each landmark
        """
        keypoints = {}

        # MediaPipe provides 33 landmarks
        landmark_names = [
            'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
            'right_eye_inner', 'right_eye', 'right_eye_outer',
            'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
            'left_index', 'right_index', 'left_thumb', 'right_thumb',
            'left_hip', 'right_hip', 'left_knee', 'right_knee',
            'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
            'left_foot_index', 'right_foot_index'
        ]

        for idx, landmark in enumerate(landmarks.landmark):
            if idx < len(landmark_names):
                name = landmark_names[idx]

                # Filter based on focus areas
                if focus_areas and not self._is_in_focus(name, focus_areas):
                    continue

                keypoints[name] = {
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                }

        # Calculate joint angles
        angles = self._calculate_joint_angles(keypoints)
        keypoints['angles'] = angles

        return keypoints

    def _is_in_focus(self, landmark_name: str, focus_areas: List[str]) -> bool:
        """Check if landmark is in the specified focus areas"""
        if not focus_areas or 'full_body' in focus_areas:
            return True

        upper_body_parts = [
            'shoulder', 'elbow', 'wrist', 'eye', 'ear', 'nose', 'mouth'
        ]
        lower_body_parts = [
            'hip', 'knee', 'ankle', 'heel', 'foot'
        ]
        arm_parts = [
            'shoulder', 'elbow', 'wrist', 'pinky', 'index', 'thumb'
        ]

        for area in focus_areas:
            if area == 'upper_body':
                if any(part in landmark_name for part in upper_body_parts):
                    return True
            elif area == 'lower_body':
                if any(part in landmark_name for part in lower_body_parts):
                    return True
            elif area == 'arms':
                if any(part in landmark_name for part in arm_parts):
                    return True
            elif area == 'legs':
                if any(part in landmark_name for part in lower_body_parts):
                    return True

        return False

    def _calculate_joint_angles(self, keypoints: Dict) -> Dict:
        """Calculate angles at major joints"""
        angles = {}

        def calculate_angle(p1, p2, p3):
            """Calculate angle between three points"""
            if not all([p1, p2, p3]):
                return None

            v1 = np.array([p1['x'] - p2['x'], p1['y'] - p2['y']])
            v2 = np.array([p3['x'] - p2['x'], p3['y'] - p2['y']])

            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            return np.degrees(angle)

        # Left elbow angle
        if all(k in keypoints for k in ['left_shoulder', 'left_elbow', 'left_wrist']):
            angles['left_elbow'] = calculate_angle(
                keypoints['left_shoulder'],
                keypoints['left_elbow'],
                keypoints['left_wrist']
            )

        # Right elbow angle
        if all(k in keypoints for k in ['right_shoulder', 'right_elbow', 'right_wrist']):
            angles['right_elbow'] = calculate_angle(
                keypoints['right_shoulder'],
                keypoints['right_elbow'],
                keypoints['right_wrist']
            )

        # Left knee angle
        if all(k in keypoints for k in ['left_hip', 'left_knee', 'left_ankle']):
            angles['left_knee'] = calculate_angle(
                keypoints['left_hip'],
                keypoints['left_knee'],
                keypoints['left_ankle']
            )

        # Right knee angle
        if all(k in keypoints for k in ['right_hip', 'right_knee', 'right_ankle']):
            angles['right_knee'] = calculate_angle(
                keypoints['right_hip'],
                keypoints['right_knee'],
                keypoints['right_ankle']
            )

        # Left shoulder angle
        if all(k in keypoints for k in ['left_elbow', 'left_shoulder', 'left_hip']):
            angles['left_shoulder'] = calculate_angle(
                keypoints['left_elbow'],
                keypoints['left_shoulder'],
                keypoints['left_hip']
            )

        # Right shoulder angle
        if all(k in keypoints for k in ['right_elbow', 'right_shoulder', 'right_hip']):
            angles['right_shoulder'] = calculate_angle(
                keypoints['right_elbow'],
                keypoints['right_shoulder'],
                keypoints['right_hip']
            )

        # Left hip angle
        if all(k in keypoints for k in ['left_shoulder', 'left_hip', 'left_knee']):
            angles['left_hip'] = calculate_angle(
                keypoints['left_shoulder'],
                keypoints['left_hip'],
                keypoints['left_knee']
            )

        # Right hip angle
        if all(k in keypoints for k in ['right_shoulder', 'right_hip', 'right_knee']):
            angles['right_hip'] = calculate_angle(
                keypoints['right_shoulder'],
                keypoints['right_hip'],
                keypoints['right_knee']
            )

        return angles

    def save_pose_data(self, pose_data: Dict, output_path: str):
        """Save extracted pose data to JSON file"""
        # Convert numpy types to native Python types for JSON serialization
        serializable_data = self._make_serializable(pose_data)

        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    def _make_serializable(self, obj):
        """Convert numpy types to native Python types"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'pose'):
            self.pose.close()
