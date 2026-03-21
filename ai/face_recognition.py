import cv2
import numpy as np
import os

recognizer   = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

MODEL_PATH = 'uploads/face_model.yml'
LABEL_MAP  = {}
_trained   = False

def train_faces():
    global recognizer, LABEL_MAP, _trained
    from models.user import User
    faces, labels = [], []
    label_id = 0
    LABEL_MAP = {}

    users = User.query.filter(User.face_image != None).all()
    for user in users:
        img_path = user.face_image
        if not os.path.exists(img_path):
            continue
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        detected = face_cascade.detectMultiScale(img, 1.1, 5)
        if len(detected) == 0:
            img = cv2.resize(img, (200, 200))
            faces.append(img)
        else:
            x, y, bw, bh = detected[0]
            face_roi = cv2.resize(img[y:y+bh, x:x+bw], (200, 200))
            faces.append(face_roi)
        labels.append(label_id)
        LABEL_MAP[label_id] = user.name
        label_id += 1

    if faces:
        recognizer.train(faces, np.array(labels))
        os.makedirs('uploads', exist_ok=True)
        recognizer.save(MODEL_PATH)
        _trained = True
        print(f"[FaceRec] Trained: {LABEL_MAP}")
    else:
        _trained = False

def load_model():
    global recognizer, _trained
    if os.path.exists(MODEL_PATH):
        recognizer.read(MODEL_PATH)
        _trained = True

def recognize_face(frame):
    global _trained
    if not _trained:
        try:
            load_model()
        except:
            return frame, "Unknown"

    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
    name  = "Unknown"

    for (x, y, w, h) in faces:
        face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
        try:
            label, confidence = recognizer.predict(face_roi)
            if confidence < 70:
                name  = LABEL_MAP.get(label, "Unknown")
                color = (0, 255, 100)
                text  = f"{name} ({confidence:.0f})"
            else:
                name  = "Unknown"
                color = (0, 60, 255)
                text  = f"Unknown ({confidence:.0f})"
        except:
            color = (128, 128, 128)
            text  = "?"

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)
        cv2.rectangle(frame, (x, y-th-10), (x+tw+8, y), color, -1)
        cv2.putText(frame, text, (x+4, y-4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0,0,0), 1)

    return frame, name