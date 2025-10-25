import cv2
import numpy as np
import dlib
from .models import FaceData

def to_gray(frame: np.ndarray) -> np.ndarray:
    """Converts a BGR frame to gray scale."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

def rect_to_bbox(rect: dlib.rectangle) -> tuple[int, int, int, int]:
    """Converts a dlib rect into a tuple (x,y,w,h)."""
    x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()
    return tuple([x,y,w,h])

def shape_to_landmarks(shape: dlib.full_object_detection) -> list[tuple[int, int]]:
    """Converts the dlib shape into a list of coordinates (x, y)."""
    return [(shape.part(i).x, shape.part(i).y) for i in range(shape.num_parts)]

def draw_face_data(frame: np.ndarray, face_data_list: list[FaceData]) -> np.ndarray:
    """Draw rects and landmarks in the frame."""
    for face in face_data_list:
        x, y, w, h = face.bbox
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        for (px, py) in face.landmarks:
            cv2.circle(frame, (px, py), 1, (0, 0, 255), -1)
    return frame

def avg_distance(points_a, points_b):
    """Distância média entre dois conjuntos de landmarks."""
    if len(points_a) != len(points_b):
        return 0
    
    a, b = np.array(points_a), np.array(points_b)
    return float(np.mean(np.linalg.norm(a - b, axis=1)))

def mouth_open_ratio(landmarks):
    """Mede o quanto a boca está aberta."""
    top = np.mean([landmarks[62], landmarks[63], landmarks[64]], axis=0)
    bottom = np.mean([landmarks[66], landmarks[67], landmarks[65]], axis=0)

    return np.linalg.norm(top - bottom)

def eye_aspect_ratio(landmarks, left: bool = True):
    """Calcula o Eye Aspect Ratio (EAR)."""
    if left:
        pts = [36, 37, 38, 39, 40, 41]
    else:
        pts = [42, 43, 44, 45, 46, 47]

    eye = np.array([landmarks[p] for p in pts])
    v1 = np.linalg.norm(eye[1] - eye[5])
    v2 = np.linalg.norm(eye[2] - eye[4])
    h = np.linalg.norm(eye[0] - eye[3])
    
    return (v1 + v2) / (2.0 * h)