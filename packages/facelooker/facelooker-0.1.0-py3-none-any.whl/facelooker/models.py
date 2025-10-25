from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Literal, Dict, Any
from datetime import datetime

@dataclass
class FaceData:
    bbox: Tuple[int, int, int, int]
    landmarks: List[Tuple[int, int]]
    emotion: Optional[str] = None
    motion_vector: Optional[Tuple[float, float]] = None

@dataclass
class MotionData:
    category: Literal["mouth_moved", "eye_blink", "face_left", "face_right", "generic"]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        return self.category
    
    def __repr__(self):
        return self.category

@dataclass
class PoseData:
    category: Literal["face_up", "face_down", "face_left", "face_right", "face_idle"]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        return 1

    def __gt__(self, other):
        return 1
    
    def __str__(self):
        return self.category
    
    def __repr__(self):
        return self.category

@dataclass
class FaceDetectionData:
    motions: List[MotionData]
    pose: PoseData
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"At {str(self.timestamp.strftime("%Y-%m-%d %H:%M:%S"))}: \n[Pose]: {str(self.pose)}\n[Motions]: ({', '.join([str(motion) for motion in self.motions])})\n"
    
    def __repr__(self):
        return f"At {str(self.timestamp.strftime("%Y-%m-%d %H:%M:%S"))}: \n[Pose]: {str(self.pose)}\n[Motions]: ({', '.join([str(motion) for motion in self.motions])})\n"