import cv2
import mediapipe as mp
from scipy.spatial import distance as dist
import numpy as np
import datetime

mp_face_mesh = mp.solutions.face_mesh

face_mesh_video = mp_face_mesh.FaceMesh(
    refine_landmarks=True, max_num_faces=1,
    min_detection_confidence=0.4,
    min_tracking_confidence=0.4
)
face_mesh_image = mp_face_mesh.FaceMesh(
    static_image_mode=True, max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.4
)

LEFT_EYE     = [33, 160, 158, 133, 153, 144]
RIGHT_EYE    = [362, 385, 387, 263, 373, 380]
MOUTH_TOP    = 13
MOUTH_BOTTOM = 14
MOUTH_LEFT   = 78
MOUTH_RIGHT  = 308

# EAR: normal open eyes = 0.25 to 0.35
# EAR: closed eyes = below 0.18
# So only alert if CLEARLY closed
EAR_THRESHOLD   = 0.18
MAR_THRESHOLD   = 0.65   # very wide open mouth = yawn
FRAME_THRESHOLD = 20     # webcam: 20 consecutive frames
YAWN_THRESHOLD  = 15

counter      = 0
yawn_counter = 0


def calculate_EAR(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def calculate_MAR(landmarks, h, w):
    top    = landmarks[MOUTH_TOP]
    bottom = landmarks[MOUTH_BOTTOM]
    left   = landmarks[MOUTH_LEFT]
    right  = landmarks[MOUTH_RIGHT]
    top_pt    = (int(top.x * w),    int(top.y * h))
    bottom_pt = (int(bottom.x * w), int(bottom.y * h))
    left_pt   = (int(left.x * w),   int(left.y * h))
    right_pt  = (int(right.x * w),  int(right.y * h))
    vertical   = dist.euclidean(top_pt, bottom_pt)
    horizontal = dist.euclidean(left_pt, right_pt)
    return vertical / (horizontal + 1e-6)


def draw_bar(frame, x, y, w, val, max_val, color, label):
    ratio = min(val / (max_val + 1e-6), 1.0)
    cv2.rectangle(frame, (x, y), (x + w, y + 12), (40, 40, 40), -1)
    cv2.rectangle(frame, (x, y), (x + int(w * ratio), y + 12), color, -1)
    cv2.putText(frame, f"{label}: {val:.2f}", (x, y - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)


def process_frame(frame, is_image=False):
    global counter, yawn_counter
    alerts = []

    # Webcam needs flip, uploaded image does NOT
    if not is_image:
        frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Choose correct FaceMesh
    face_mesh_obj = face_mesh_image if is_image else face_mesh_video

    # HUD overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (260, h), (8, 12, 20), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
    cv2.putText(frame, "DrowzyAI Monitor", (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    cv2.line(frame, (0, 28), (260, 28), (0, 200, 255), 1)

    results = face_mesh_obj.process(rgb)

    status_text  = "NO FACE"
    status_color = (128, 128, 128)
    ear_val = 0.0
    mar_val = 0.0

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            left_eye, right_eye = [], []

            for idx in LEFT_EYE:
                x_ = int(face_landmarks.landmark[idx].x * w)
                y_ = int(face_landmarks.landmark[idx].y * h)
                left_eye.append((x_, y_))
                cv2.circle(frame, (x_, y_), 2, (0, 255, 100), -1)

            for idx in RIGHT_EYE:
                x_ = int(face_landmarks.landmark[idx].x * w)
                y_ = int(face_landmarks.landmark[idx].y * h)
                right_eye.append((x_, y_))
                cv2.circle(frame, (x_, y_), 2, (0, 255, 100), -1)

            ear_val = (calculate_EAR(left_eye) + calculate_EAR(right_eye)) / 2.0
            mar_val = calculate_MAR(face_landmarks.landmark, h, w)

            # Draw eye contours
            cv2.polylines(frame, [np.array(left_eye,  dtype=np.int32)], True, (0, 255, 0), 1)
            cv2.polylines(frame, [np.array(right_eye, dtype=np.int32)], True, (0, 255, 0), 1)

            # ── DROWSINESS LOGIC ──────────────────────────────
            if ear_val < EAR_THRESHOLD:
                # Eyes clearly closed
                if is_image:
                    # For images: detect immediately, no frame counter needed
                    alerts.append("DROWSY")
                    status_text  = "DROWSY!"
                    status_color = (0, 0, 255)
                    # Red flash overlay
                    al = frame.copy()
                    cv2.rectangle(al, (0, 0), (w, h), (0, 0, 160), -1)
                    cv2.addWeighted(al, 0.2, frame, 0.8, 0, frame)
                    cv2.putText(frame, "DROWSY ALERT!", (w // 2 - 130, h // 2),
                                cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 0, 255), 3)
                else:
                    # For webcam: count frames
                    counter += 1
                    if counter > FRAME_THRESHOLD:
                        alerts.append("DROWSY")
                        status_text  = "DROWSY!"
                        status_color = (0, 0, 255)
                        al = frame.copy()
                        cv2.rectangle(al, (0, 0), (w, h), (0, 0, 160), -1)
                        cv2.addWeighted(al, 0.2, frame, 0.8, 0, frame)
                        cv2.putText(frame, "DROWSY ALERT!", (w // 2 - 130, h // 2),
                                    cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 0, 255), 3)
                    else:
                        status_text  = "EYES CLOSING..."
                        status_color = (0, 165, 255)
            else:
                # Eyes open — AWAKE
                counter     = 0
                status_text  = "AWAKE"
                status_color = (0, 220, 80)

            # ── YAWN LOGIC ────────────────────────────────────
            if mar_val > MAR_THRESHOLD:
                if is_image:
                    alerts.append("YAWN")
                    cv2.putText(frame, "YAWNING!", (w - 210, 55),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
                else:
                    yawn_counter += 1
                    if yawn_counter > YAWN_THRESHOLD:
                        alerts.append("YAWN")
                        cv2.putText(frame, "YAWNING!", (w - 210, 55),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
            else:
                yawn_counter = 0

    # ── HUD BARS ──────────────────────────────────────────────
    draw_bar(frame, 10, 45,  220, ear_val, 0.4,            (0, 255, 100), "EAR")
    draw_bar(frame, 10, 72,  220, mar_val, 1.0,            (0, 165, 255), "MAR")
    draw_bar(frame, 10, 99,  220, counter, FRAME_THRESHOLD, (0, 0,   255), "Drowsy")

    # ── STATUS BOX ────────────────────────────────────────────
    cv2.rectangle(frame, (6, h - 44), (254, h - 8), (16, 20, 28), -1)
    cv2.putText(frame, f"STATUS: {status_text}", (12, h - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

    ts = datetime.datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, ts, (10, h - 52),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 100, 100), 1)

    return frame, alerts


