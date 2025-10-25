import numpy as np
from collections import deque
from typing import Optional
from .models import FaceData, PoseData

class FacePosePredictor:
    """
    Estima o estado atual do rosto com base na pose e posição.
    Detecta estados como: 'face_up', 'face_down', 'face_left', 'face_right', 'face_idle'.
    """

    def __init__(
        self,
        angle_threshold_up: float = 6.0,
        angle_threshold_down: float = 30.0,
        angle_threshold_side: float = 20.0,
        position_tolerance: float = 1.0,
        stability_frames: int = 5,
        debug: bool = False
    ):
        self.__debug = debug
        self.__angle_threshold_up = angle_threshold_up
        self.__angle_threshold_down = angle_threshold_down
        self.__angle_threshold_side = angle_threshold_side
        self.__position_tolerance = position_tolerance
        self.__history = deque(maxlen=stability_frames)
        self.__current_state: Optional[PoseData] = None

    def _compute_head_tilt(self, landmarks):
        """Calcula pitch (inclinação vertical) e yaw (rotação lateral)."""
        nose_tip = np.array(landmarks[30])
        chin = np.array(landmarks[8])
        left_eye = np.array(landmarks[36])
        right_eye = np.array(landmarks[45])

        eye_center = (left_eye + right_eye) / 2.0

        # Pitch = diferença vertical entre nariz e linha dos olhos
        pitch_angle = np.degrees(
            np.arctan2(nose_tip[1] - eye_center[1], np.linalg.norm(right_eye - left_eye))
        )

        # Yaw = deslocamento horizontal do nariz em relação ao centro dos olhos
        yaw_angle = np.degrees(
            np.arctan2(nose_tip[0] - eye_center[0], np.linalg.norm(right_eye - left_eye))
        )

        return pitch_angle, yaw_angle
    
    def _center_offset(self, frame_shape, bbox):
        frame_h, frame_w = frame_shape[:2]
        x, y, w, h = bbox
        face_center = (x + w / 2, y + h / 2)
        frame_center = (frame_w / 2, frame_h / 2)
        offset_x = (face_center[0] - frame_center[0]) / frame_w
        offset_y = (face_center[1] - frame_center[1]) / frame_h

        return offset_x, offset_y
    
    def _stabilize_state(self):
        if not self.__history:
            return PoseData(category="face_idle")
        
        states, counts = np.unique(self.__history, return_counts=True)
        return states[np.argmax(counts)]

    def predict(self, face: FaceData, frame_shape) -> PoseData:
        pitch, yaw = self._compute_head_tilt(face.landmarks)
        offset_x, offset_y = self._center_offset(frame_shape, face.bbox)
        state = PoseData(category='face_idle')

        if pitch < self.__angle_threshold_up:
            state.category = "face_up"
        elif pitch > self.__angle_threshold_down:
            state.category = "face_down"
        elif yaw < -self.__angle_threshold_side:
            state.category = "face_left"
        elif yaw > self.__angle_threshold_side:
            state.category = "face_right"
        else:
            if abs(offset_x) < self.__position_tolerance and abs(offset_y) < self.__position_tolerance:
                state.category = "face_idle"

        state.metadata = {"offset_x": offset_x, "offset_y": offset_y}
        
        self.__history.append(state)

        stable_state = self._stabilize_state()

        if self.__debug:
            print(f"[POSE] pitch={pitch:.2f} yaw={yaw:.2f} offset=({offset_x:.2f},{offset_y:.2f}) -> {stable_state.category}")

        self.__current_state = stable_state
        return stable_state
    
    @property
    def current_state(self):
        return self.__current_state