from .strategy import FaceDetectionStrategy
from .helpers import draw_face_data
from .motion import FaceMotionClassifier
from .pose import FacePosePredictor
from .models import FaceDetectionData

from typing import Generator

import queue
import cv2
import threading

class Facelooker:
    def __init__(self, strategy: FaceDetectionStrategy, show_interface = False, show_debug_text = False):
        self._strategy = strategy
        self._show_interface = show_interface
        self._show_debug_text = show_debug_text
        self._motion_classifier = FaceMotionClassifier(debug=False)
        self._pose_predictor = FacePosePredictor(debug=False)
        self._face_detections = queue.SimpleQueue()
        self._running = False
        self._thread = None

    def iterate_over_face_detections(self) -> Generator[FaceDetectionData, None, None]:
        yield self._face_detections.get()

        if not self._face_detections.empty():
            self.iterate_over_face_detections()

    def process_frame(self, frame):
        faces = self._strategy.detect(frame)
        
        for face in faces:
            motions = self._motion_classifier.classify(face)
            pose = self._pose_predictor.predict(face, frame.shape)

            yield {"face": face, "motions": motions or [], "pose": pose}
    
    def _stream_from_camera(self, camera_index: int):
        cap = cv2.VideoCapture(camera_index)

        if not cap.isOpened():
            raise RuntimeError("Failed to open camera in OpenCV.")
        
        while self._running:
            ret, frame = cap.read()

            if not ret:
                break

            current_result: dict = {"face": None, "motions": [], "pose": None}
            faces = []

            for result in self.process_frame(frame):
                current_result = result
                faces.append(current_result["face"])

                self._face_detections.put(FaceDetectionData(motions=current_result["motions"], pose=current_result["pose"]))

            frame = draw_face_data(frame, faces)

            if self._show_debug_text:
                if current_result.get("motions") is not None:
                    cv2.putText(frame, "motions: " + ", ".join([motion.category for motion in current_result["motions"]]), (20, 40), cv2.FONT_HERSHEY_COMPLEX, 0.8, (80, 255, 255), 1)

                if current_result.get("pose") is not None:
                    cv2.putText(frame, "pose: " + current_result["pose"].category, (20, 80), cv2.FONT_HERSHEY_COMPLEX, 0.8, (80, 255, 255), 1)
                    cv2.putText(frame, "pose offset: " + ", ".join([
                        f"{current_result["pose"].metadata["offset_x"]:.2f}",
                        f"{current_result["pose"].metadata["offset_y"]:.2f}"
                    ]), (20, 120), cv2.FONT_HERSHEY_COMPLEX, 0.8, (80, 80, 250), 1)

            if self._show_interface:
                cv2.imshow("facelooker", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self._running = False
        
        cap.release()
        cv2.destroyAllWindows()
    
    def start(self, camera_index: int = 0, as_daemon: bool = False):
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._stream_from_camera, args=(camera_index,), daemon=as_daemon)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    @property
    def running(self):
        return self._running