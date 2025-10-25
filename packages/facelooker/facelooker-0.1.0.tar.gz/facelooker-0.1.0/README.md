# Facelooker

## Description
The Facelooker is a tiny Python library to provide some utilities for facial recognition and movement detection.
The main idea is to have a single instance of `Facelooker` class that runs the device camera and process all the
events automatically during the face recognition with OpenCV. All the movements and current pose are returned
in a single payload as a simple dictionary. This info can be consumed by any external consumer.

## How to Use

```python
from facelooker import Facelooker
from facelooker.strategy import DlibStrategy

PREDICTOR_PATH = "data/shape_predictor_68_face_landmarks.dat"

strategy = DlibStrategy(PREDICTOR_PATH)
facelooker = Facelooker(strategy, show_interface=True, show_debug_text=True)

facelooker.start() # Starts in a separated thread.

```

To load a predictor in `DlibStrategy`, you can [download the file here](https://huggingface.co/spaces/asdasdasdasd/Face-forgery-detection/blob/ccfc24642e0210d4d885bc7b3dbc9a68ed948ad6/shape_predictor_68_face_landmarks.dat). The facial recognition strategies are "under construction".