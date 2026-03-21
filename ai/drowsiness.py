import cv2
import mediapipe as mp
from scipy.spatial import distance as dist
import pygame

# 🔊 init sound
pygame.mixer.init()

# MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

EAR_THRESHOLD = 0.25
FRAME_THRESHOLD = 20

counter = 0
alarm_on = False

def calculate_EAR(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def process_frame(frame):
    global counter, alarm_on

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape

            left_eye = []
            right_eye = []

            # LEFT EYE + DOTS
            for idx in LEFT_EYE:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                left_eye.append((x, y))
                cv2.circle(frame, (x, y), 2, (0,255,0), -1)

            # RIGHT EYE + DOTS
            for idx in RIGHT_EYE:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                right_eye.append((x, y))
                cv2.circle(frame, (x, y), 2, (0,255,0), -1)

            # EAR
            ear = (calculate_EAR(left_eye) + calculate_EAR(right_eye)) / 2.0

            # DROWSINESS
            if ear < EAR_THRESHOLD:
                counter += 1

                if counter > FRAME_THRESHOLD:
                    cv2.putText(frame, "DROWSY ALERT!", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

                    if not alarm_on:
                        pygame.mixer.music.load("static/audio/alarm.mp3")
                        pygame.mixer.music.play()
                        alarm_on = True
            else:
                counter = 0
                alarm_on = False
                cv2.putText(frame, "AWAKE", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    return frame