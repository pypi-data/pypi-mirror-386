import numpy as np
from collections import deque
from typing import List, Dict
from .models import FaceData, MotionData
from .helpers import avg_distance, mouth_open_ratio, eye_aspect_ratio

class FaceMotionClassifier:
    """
    Classifica movimentos faciais com base em landmarks consecutivos.
    Detecta eventos como: piscadas, boca movendo, rotação lateral da face, etc.
    """

    def __init__(
        self, 
        mouth_thresh: float = 0.9,
        blink_thresh: float = 0.5,
        face_turn_thresh: float = 7.0,
        smoothing_window: int = 3,
        min_confidence_frames: int = 3,
        debug: bool = False
    ):
        self.prev_landmarks = None
        self.mouth_thresh = mouth_thresh
        self.blink_thresh = blink_thresh
        self.face_turn_thresh = face_turn_thresh
        self.debug = debug

        # Filtros de estabilidade
        self.motion_history: Dict[str, deque] = {
            "mouth_moved": deque(maxlen=smoothing_window),
            "eye_blink": deque(maxlen=smoothing_window),
            "face_left": deque(maxlen=smoothing_window),
            "face_right": deque(maxlen=smoothing_window),
        }
        self.min_confidence_frames = min_confidence_frames

    def classify(self, face: FaceData) -> List[MotionData]:
        """Analisa o movimento facial e retorna categorias detectadas."""
        if self.prev_landmarks is None:
            self.prev_landmarks = face.landmarks
            return []

        motions = []

        # Detectar movimento geral (face mexeu)
        delta = avg_distance(face.landmarks, self.prev_landmarks)
        if delta > self.face_turn_thresh:
            direction = "face_right" if np.mean(np.array(face.landmarks)[:,0]) > np.mean(np.array(self.prev_landmarks)[:,0]) else "face_left"
            motions.append(MotionData(category=direction))

        # Boca movendo (mudança vertical entre lábios)
        mouth_now = mouth_open_ratio(face.landmarks)
        mouth_prev = mouth_open_ratio(self.prev_landmarks)
        if abs(mouth_now - mouth_prev) > self.mouth_thresh:
            motions.append(MotionData(category="mouth_moved"))

        # Piscar (queda temporária no EAR)
        left_ear_now = eye_aspect_ratio(face.landmarks, left=True)
        right_ear_now = eye_aspect_ratio(face.landmarks, left=False)
        left_ear_prev = eye_aspect_ratio(self.prev_landmarks, left=True)
        right_ear_prev = eye_aspect_ratio(self.prev_landmarks, left=False)

        if (left_ear_prev - left_ear_now) > self.blink_thresh or (right_ear_prev - right_ear_now) > self.blink_thresh:
            motions.append(MotionData(category="eye_blink"))

        # Atualiza histórico e landmarks
        self.prev_landmarks = face.landmarks

        # Aplica filtros de estabilidade
        stable_motions = self._filter_motions(motions)

        if self.debug:
            print(f"[DEBUG] raw={motions} | stable={stable_motions}")

        return stable_motions

    def _filter_motions(self, motions: List[MotionData]) -> List[MotionData]:
        """Filtra movimentos que aparecem de forma instável."""
        stable = []
        for motion in self.motion_history.keys():
            self.motion_history[motion].append(any(m.category == motion for m in motions))
            print
            if sum(self.motion_history[motion]) >= self.min_confidence_frames:
                stable.append(MotionData(category=motion))
        return stable