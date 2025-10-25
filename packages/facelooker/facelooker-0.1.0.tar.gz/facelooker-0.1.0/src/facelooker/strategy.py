from abc import abstractmethod, ABC
from .helpers import *
from .models import FaceData

class FaceDetectionStrategy(ABC):
    @abstractmethod
    def detect(self, frame) -> list[FaceData]:
        pass

class DlibStrategy(FaceDetectionStrategy):
    def __init__(self, predictor_path: str):
        import dlib
        self._detector = dlib.get_frontal_face_detector()
        self._predictor = dlib.shape_predictor(predictor_path)

    def detect(self, frame) -> list[FaceData]:
        gray = to_gray(frame)
        rects = self._detector(gray, 0)
        faces = []

        for rect in rects:
            bbox = rect_to_bbox(rect)
            shape = self._predictor(gray, rect)
            landmarks = shape_to_landmarks(shape)
            faces.append(FaceData(bbox=bbox, landmarks=landmarks))

        return faces