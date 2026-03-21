# 🚗 DrowzyAI — Real-Time Driver Drowsiness Monitoring System

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.3-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.13-red)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 Goal

Driver drowsiness is one of the leading causes of road accidents worldwide.
**DrowzyAI** detects drowsiness and yawning in real-time using only a webcam —
no dataset, no GPU, no expensive hardware required.

The system monitors:
- 😴 **Eye closure** → triggers DROWSY alert + alarm sound
- 🥱 **Yawning** → triggers YAWN alert
- 👤 **Face identity** → recognizes registered users via LBPH

Works on **live webcam**, **uploaded images**, and **uploaded videos**.

---

## 🧠 How We Detect Drowsiness — No Dataset Required

Most drowsiness detection projects train deep learning models on thousands
of labeled images. We use a completely different approach —
**Facial Landmark Geometry (pure math)** — which requires zero training data.

### MediaPipe FaceMesh
MediaPipe extracts **468 facial landmark points** from every frame in real-time.
We pick specific landmark indices for eyes and mouth and calculate ratios.

---

### 👁️ EAR — Eye Aspect Ratio
```
        B
    *-------*
   /         \
A *           * C
   \         /
    *-------*
        D
```
```
EAR = (|B-D| + |top-bottom|) / (2 × |A-C|)
    = (A + B) / (2.0 × C)

Where:
  A = euclidean distance between points eye[1] and eye[5]
  B = euclidean distance between points eye[2] and eye[4]
  C = euclidean distance between points eye[0] and eye[3]
```
```
EAR Value       Meaning
─────────────────────────────
0.25 – 0.35  →  Eyes fully open   → AWAKE ✅
0.18 – 0.25  →  Eyes half open    → WARNING ⚠️
Below 0.18   →  Eyes closed       → DROWSY 🔴 + ALARM 🔊
```

Eye landmark indices used:
```python
LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

EAR = (calculate_EAR(left_eye) + calculate_EAR(right_eye)) / 2.0
```

If EAR stays below threshold for **20 consecutive frames** → DROWSY alert triggered.

---

###  MAR — Mouth Aspect Ratio
```
        TOP (13)
          *
         / \
LEFT    *   *   RIGHT
(78)     \ /    (308)
          *
       BOTTOM (14)
```
```
MAR = Vertical Distance / Horizontal Distance
    = |TOP - BOTTOM| / |LEFT - RIGHT|
```
```
MAR Value       Meaning
─────────────────────────────
Below 0.65   →  Mouth normal    → OK ✅
Above 0.65   →  Mouth wide open → YAWN 🥱
```

If MAR stays above threshold for **15 consecutive frames** → YAWN alert triggered.

---

### 🔄 Per-Frame Detection Loop
```
Every Frame (webcam ~30fps):
│
├── Step 1: Flip frame (webcam mirror effect)
├── Step 2: Convert BGR → RGB
├── Step 3: MediaPipe extracts 468 landmarks
├── Step 4: Pick 6 eye points (left + right)
├── Step 5: Calculate EAR average
├── Step 6: Pick 4 mouth points
├── Step 7: Calculate MAR
│
├── Step 8: EAR check
│     if EAR < 0.18:
│         counter += 1
│         if counter > 20:
│             → DROWSY alert
│             → Red overlay on frame
│             → Alarm sound plays
│             → Log saved to database
│     else:
│         counter = 0   ← reset when eyes open
│
├── Step 9: MAR check
│     if MAR > 0.65:
│         yawn_counter += 1
│         if yawn_counter > 15:
│             → YAWN alert
│             → Log saved to database
│     else:
│         yawn_counter = 0
│
├── Step 10: LBPH Face Recognition
│     → Haar Cascade detects face box
│     → LBPH compares with registered face
│     → confidence < 70: show name
│     → confidence >= 70: show "Unknown"
│
├── Step 11: Draw HUD overlay
│     → EAR bar, MAR bar, Drowsy counter bar
│     → Status text (AWAKE / DROWSY / YAWNING)
│     → Timestamp
│
└── Step 12: Encode as JPEG → stream to browser
```

---

### 🤔 Why No Dataset?

| Factor | Dataset + CNN | Our Approach (Landmark Math) |
|---|---|---|
| Training required | Yes — hours/days | ❌ No training at all |
| Dataset needed | Thousands of images | ❌ Zero images needed |
| Works on new faces | Sometimes fails | ✅ Works on any face |
| GPU required | Recommended | ❌ Normal CPU works |
| Real-time speed | Slow on CPU | ✅ 30fps on CPU |
| Setup complexity | Very complex | ✅ Simple pip install |
| Accuracy | High | High |

**Conclusion:** Facial geometry ratios (EAR/MAR) are universal —
they work the same for every human face without any training data.

---

## 🏗️ System Architecture
```
Browser (Student/Admin)
         │
         ▼
   Flask Web Server (app.py)
         │
   ┌─────┴──────────────────────┐
   │                            │
   ▼                            ▼
STUDENT ROLE               ADMIN ROLE
─────────────              ───────────
Dashboard                  Admin Dashboard
Live Monitor               Manage Users
Analyze File               All Alerts
My History                 Delete/Clear Logs
         │
         ▼
   AI Detection Engine
   ┌─────────────────────────┐
   │  ai/drowsiness.py       │
   │  → MediaPipe FaceMesh   │
   │  → EAR calculation      │
   │  → MAR calculation      │
   │  → HUD drawing          │
   └─────────────────────────┘
   ┌─────────────────────────┐
   │  ai/face_recognition.py │
   │  → Haar Cascade detect  │
   │  → LBPH recognizer      │
   │  → Name + confidence    │
   └─────────────────────────┘
         │
         ▼
   SQLite Database
   → Users table
   → AlertLog table
         │
         ▼
   alarm.mp3 plays on DROWSY
```

---

## 📁 Project Structure
```
driver_monitoring_system/
│
├── app.py                    # Flask app factory
├── extensions.py             # SQLAlchemy + LoginManager
├── requirements.txt          # All dependencies
├── fix_admin.py              # One-time admin role script
│
├── ai/
│   ├── drowsiness.py         # EAR + MAR detection
│   └── face_recognition.py   # LBPH train + recognize
│
├── models/
│   └── user.py               # User + AlertLog models
│
├── routes/
│   ├── auth_routes.py        # Login, Register, Logout
│   ├── main_routes.py        # Page routes + admin actions
│   └── ai_routes.py          # Video stream + analysis APIs
│
├── static/
│   ├── audio/alarm.mp3       # Alarm sound
│   ├── css/style.css         # Dark cyberpunk theme
│   └── js/validation.js      # Form validation
│
├── templates/
│   ├── base.html             # Sidebar layout
│   ├── login.html            # Login page
│   ├── register.html         # Register + face upload
│   ├── dashboard.html        # Admin OR student dashboard
│   ├── webcam.html           # Live monitor (student only)
│   ├── upload.html           # Image/Video analysis (student only)
│   ├── history.html          # Student alert history
│   ├── all_history.html      # All users history (admin only)
│   └── admin.html            # User management (admin only)
│
└── uploads/
    ├── faces/                # Registered face photos
    ├── snapshots/            # Analyzed image results
    └── videos/               # Analyzed video results
```

---

---

## ⚙️ Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10 | Core language |
| Flask | 3.0.3 | Web framework |
| Flask-SQLAlchemy | 3.1.1 | Database ORM |
| Flask-Login | 0.6.3 | User sessions |
| MediaPipe | 0.10.14 | Face landmark extraction |
| OpenCV (contrib) | 4.13 | Camera + image processing + LBPH |
| SciPy | 1.15.3 | Euclidean distance (EAR/MAR math) |
| NumPy | 2.2.6 | Array operations |
| Pygame | 2.6.0 | Alarm sound playback |
| SQLite | built-in | Database |
| Chart.js | 4.4.0 | Dashboard bar charts (CDN) |

---

## 🚀 Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/driver_monitoring_system.git
cd driver_monitoring_system
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> ⚠️ Use only `opencv-contrib-python` — NOT `opencv-python`.
> Having both installed causes conflicts.

### 4. Add alarm sound
Place your `alarm.mp3` file at:
```
static/audio/alarm.mp3
```

### 5. Run the application
```bash
python app.py
```

### 6. Open browser
```
http://127.0.0.1:5000
```

### 7. Set admin role (first time only)
```bash
python fix_admin.py
```

---

## 📋 First Time Usage

1. Go to `http://127.0.0.1:5000/auth/register`
2. Fill name, email, password
3. Select **Admin** or **Student** role
4. Upload a clear face photo
5. Login with your credentials
6. Students → click **Live Monitor** → click **Start Camera**
7. Admin → see all student data in **Admin Dashboard**

---

## 🔍 Detection Thresholds

| Parameter | Value | Meaning |
|---|---|---|
| EAR Threshold | 0.18 | Below = eyes closed |
| MAR Threshold | 0.65 | Above = yawning |
| Drowsy Frame Count | 20 frames | Consecutive frames before alert |
| Yawn Frame Count | 15 frames | Consecutive frames before alert |
| Face Recognition Confidence | < 70 | Known face |

---

## 📊 Database Schema

### Users Table
| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| name | String | Full name |
| email | String | Unique email |
| password_hash | String | Hashed password |
| role | String | admin / student |
| face_image | String | Path to face photo |
| created_at | DateTime | Registration time |

### AlertLog Table
| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| user_id | ForeignKey | Linked user |
| alert_type | String | DROWSY / YAWN / NORMAL |
| source | String | webcam / image / video |
| details | Text | Extra info |
| snapshot_path | String | Result image path |
| timestamp | DateTime | When alert occurred |

---

##  Acknowledgements

- [MediaPipe](https://mediapipe.dev/) — Face landmark detection
- [OpenCV](https://opencv.org/) — Computer vision library
- [Soukupmarek EAR Paper](https://vision.fe.uni-lj.si/cvww2016/proceedings/papers/05.pdf) — Original EAR formula by Soukupová and Čech

---

## 📄 License

MIT License — free to use, modify and distribute.

---

*Built with ❤️ for road safety — DrowzyAI 2026*
