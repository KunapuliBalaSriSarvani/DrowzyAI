import cv2
import mediapipe as mp
from scipy.spatial import distance as dist
import pygame

pygame.mixer.init()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

LEFT_EYE = [33,160,158,133,153,144]
RIGHT_EYE = [362,385,387,263,373,380]

EAR_THRESHOLD = 0.25
FRAME_THRESHOLD = 20

counter = 0

def calculate_EAR(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A+B)/(2.0*C)

def process_frame(frame):
    global counter
    alerts = []

    frame = cv2.flip(frame,1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face in results.multi_face_landmarks:
            h,w,_ = frame.shape

            left_eye = [(int(face.landmark[i].x*w), int(face.landmark[i].y*h)) for i in LEFT_EYE]
            right_eye = [(int(face.landmark[i].x*w), int(face.landmark[i].y*h)) for i in RIGHT_EYE]

            ear = (calculate_EAR(left_eye)+calculate_EAR(right_eye))/2

            # draw eye dots
            for (x,y) in left_eye+right_eye:
                cv2.circle(frame,(x,y),2,(0,255,0),-1)

            if ear < EAR_THRESHOLD:
                counter += 1
                if counter > FRAME_THRESHOLD:
                    alerts.append("DROWSY")

                    pygame.mixer.music.load("static/audio/alarm.mp3")
                    pygame.mixer.music.play()

                    cv2.putText(frame,"DROWSY ALERT!",(100,200),
                                cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)
            else:
                counter = 0

    return frame, alerts