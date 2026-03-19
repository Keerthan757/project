import cv2
import mediapipe as mp
from flask import Flask, Response, render_template, jsonify, request, redirect, url_for, send_file
import numpy as np
import csv
from datetime import datetime

app = Flask(__name__)

# -------------------------
# Student Details
# -------------------------
student = {
    "name":"",
    "regno":"",
    "email":"",
    "subject":""
}

# -------------------------
# Camera
# -------------------------
camera = cv2.VideoCapture(0)

# -------------------------
# Mediapipe FaceMesh
# -------------------------
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=True,
    max_num_faces=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# -------------------------
# Eye Landmarks
# -------------------------
LEFT_EYE = [33,160,158,133,153,144]
RIGHT_EYE = [362,385,387,263,373,380]

LEFT_CORNER = 33
RIGHT_CORNER = 263
NOSE_TIP = 1

EAR_THRESHOLD = 0.20
FPS = 30

# -------------------------
# Tracking Variables
# -------------------------
blink_counter = 0
closed_frames = 0
focus_frames = 0
total_frames = 0

state = {
    "faces":0,
    "blinks":0,
    "focus":100,
    "gaze":"Center",
    "status":"Waiting"
}

# -------------------------
# EAR Calculation
# -------------------------
def eye_aspect_ratio(eye):

    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])

    return (A + B) / (2.0 * C)

# -------------------------
# Video Stream Generator
# -------------------------
def generate_frames():

    global blink_counter, closed_frames, focus_frames, total_frames

    while True:

        success, frame = camera.read()

        if not success:
            continue

        frame = cv2.flip(frame,1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = face_mesh.process(rgb)

        status = "No Face"
        gaze = "Center"

        if results.multi_face_landmarks:

            faces = len(results.multi_face_landmarks)
            state["faces"] = faces

            face = results.multi_face_landmarks[0]

            h,w,_ = frame.shape

            nose = face.landmark[NOSE_TIP]
            left = face.landmark[LEFT_CORNER]
            right = face.landmark[RIGHT_CORNER]

            center = (left.x + right.x) / 2

            if nose.x < center - 0.02:
                gaze = "Left"

            elif nose.x > center + 0.02:
                gaze = "Right"

            else:
                gaze = "Center"

            state["gaze"] = gaze

            left_eye = []
            right_eye = []

            for i in LEFT_EYE:
                lm = face.landmark[i]
                left_eye.append([int(lm.x*w), int(lm.y*h)])

            for i in RIGHT_EYE:
                lm = face.landmark[i]
                right_eye.append([int(lm.x*w), int(lm.y*h)])

            leftEAR = eye_aspect_ratio(np.array(left_eye))
            rightEAR = eye_aspect_ratio(np.array(right_eye))

            ear = (leftEAR + rightEAR) / 2

            if ear < EAR_THRESHOLD:

                closed_frames += 1

                if closed_frames > FPS * 2:
                    status = "Drowsy"

            else:

                if 2 <= closed_frames < FPS * 2:
                    blink_counter += 1

                closed_frames = 0
                status = "Focused"

        state["status"] = status
        state["blinks"] = blink_counter

        total_frames += 1

        if status == "Focused":
            focus_frames += 1

        if total_frames > 0:
            state["focus"] = int((focus_frames/total_frames)*100)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n')

# -------------------------
# Routes
# -------------------------

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/start', methods=['POST'])
def start():

    student["name"] = request.form["name"]
    student["regno"] = request.form["regno"]
    student["email"] = request.form["email"]
    student["subject"] = request.form["subject"]

    return redirect(url_for("dashboard"))

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html", student=student)

@app.route('/video')
def video():

    return Response(generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    return jsonify(state)

@app.route('/export')
def export():


    with open("report.csv","w",newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["Time","Student","RegNo","Faces","Blinks","Focus","Gaze"])

        writer.writerow([
            datetime.now(),
            student["name"],
            student["regno"],
            state["faces"],
            state["blinks"],
            state["focus"],
            state["gaze"]
        ])

    return send_file("report.csv", as_attachment=True)


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
       