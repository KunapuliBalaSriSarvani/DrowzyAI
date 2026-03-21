from flask import Blueprint, Response, request, jsonify, current_app
from flask_login import login_required, current_user
from models.user import AlertLog
from extensions import db
import cv2, os, time, base64

ai_bp = Blueprint('ai', __name__)
camera = None
alert_buffer = []

def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
    return camera

def release_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()
        camera = None

def generate_frames(user_id, app):
    from ai.drowsiness import process_frame
    from ai.face_recognition import recognize_face
    global alert_buffer
    cap = get_camera()
    last_log_time = {}

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame, alerts = process_frame(frame)
        frame, face_name = recognize_face(frame)

        if alerts:
            for alert in alerts:
                now = time.time()
                if alert not in last_log_time or (now - last_log_time[alert]) > 5:
                    last_log_time[alert] = now
                    alert_buffer.append(alert)
                    if len(alert_buffer) > 50:
                        alert_buffer.pop(0)
                    with app.app_context():
                        try:
                            log = AlertLog(user_id=user_id, alert_type=alert, source='webcam')
                            db.session.add(log)
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            print(f"Log error: {e}")

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


@ai_bp.route('/video_feed')
@login_required
def video_feed():
    uid = current_user.id
    app = current_app._get_current_object()
    return Response(generate_frames(uid, app),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@ai_bp.route('/stop_camera', methods=['POST'])
@login_required
def stop_camera():
    release_camera()
    return jsonify({'status': 'stopped'})


@ai_bp.route('/get_alerts', methods=['GET'])
@login_required
def get_alerts():
    global alert_buffer
    alerts = list(alert_buffer)
    alert_buffer = []
    return jsonify({'alerts': alerts})


@ai_bp.route('/analyze_image', methods=['POST'])
@login_required
def analyze_image():
    from ai.drowsiness import process_frame
    from ai.face_recognition import recognize_face
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    file = request.files['image']
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'snapshots')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"img_{int(time.time())}.jpg"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    frame = cv2.imread(filepath)
    if frame is None:
        return jsonify({'error': 'Cannot read image'}), 400
    frame, alerts = process_frame(frame)
    frame, face_name = recognize_face(frame)
    out_filename = f"result_{filename}"
    out_path = os.path.join(upload_dir, out_filename)
    cv2.imwrite(out_path, frame)
    alert_list = alerts if alerts else ['NORMAL']
    for alert in alert_list:
        try:
            log = AlertLog(user_id=current_user.id, alert_type=alert,
                           source='image', snapshot_path=f"uploads/snapshots/{out_filename}")
            db.session.add(log)
        except Exception as e:
            print(f"Log error: {e}")
    db.session.commit()
    with open(out_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    return jsonify({
        'result_image': f"data:image/jpeg;base64,{img_b64}",
        'alerts': alerts or [],
        'face': face_name,
        'status': 'done'
    })


@ai_bp.route('/analyze_video', methods=['POST'])
@login_required
def analyze_video():
    from ai.drowsiness import process_frame
    from ai.face_recognition import recognize_face
    if 'video' not in request.files:
        return jsonify({'error': 'No video uploaded'}), 400
    file = request.files['video']
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'videos')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"vid_{int(time.time())}.mp4"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    cap = cv2.VideoCapture(filepath)
    fps    = cap.get(cv2.CAP_PROP_FPS) or 25
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_filename = f"result_{filename}"
    out_path = os.path.join(upload_dir, out_filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
    all_alerts = []
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        if frame_count % 2 == 0:
            frame, alerts = process_frame(frame)
            frame, _ = recognize_face(frame)
            all_alerts.extend(alerts or [])
        writer.write(frame)
    cap.release()
    writer.release()
    alert_counts = {}
    for a in all_alerts:
        alert_counts[a] = alert_counts.get(a, 0) + 1
    if not alert_counts:
        alert_counts['NORMAL'] = 1
    for alert_type, count in alert_counts.items():
        log = AlertLog(user_id=current_user.id, alert_type=alert_type, source='video',
                       details=f"Detected {count} times in {frame_count} frames",
                       snapshot_path=f"uploads/videos/{out_filename}")
        db.session.add(log)
    db.session.commit()
    return jsonify({
        'alerts': list(alert_counts.keys()),
        'alert_counts': alert_counts,
        'total_frames': frame_count,
        'status': 'done'
    })