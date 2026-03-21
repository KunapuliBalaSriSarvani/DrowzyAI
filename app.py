from flask import Flask, render_template, Response
import cv2
from ai.drowsiness import process_frame

app = Flask(__name__)

cap = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = process_frame(frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('webcam.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)