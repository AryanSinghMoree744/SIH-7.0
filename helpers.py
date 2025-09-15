import base64, io, pickle
from PIL import Image
import numpy as np

try:
    import face_recognition
    HAVE_FR = True
except:
    HAVE_FR = False

def decode_base64_image(data_url):
    header, encoded = data_url.split(",", 1)
    img_data = base64.b64decode(encoded)
    return Image.open(io.BytesIO(img_data))

def image_to_numpy(pil_image):
    return np.array(pil_image.convert('RGB'))

def get_face_encoding_from_pil(pil_image):
    img = image_to_numpy(pil_image)
    if HAVE_FR:
        encs = face_recognition.face_encodings(img)
        return encs[0] if encs else None
    return None

def compare_encodings(enc1, enc2, threshold=0.6):
    if enc1 is None or enc2 is None:
        return False
    dist = np.linalg.norm(enc1 - enc2)
    return dist <= threshold

def serialize_encoding(enc):
    return pickle.dumps(enc)

def deserialize_encoding(b):
    return pickle.loads(b) if b else None
