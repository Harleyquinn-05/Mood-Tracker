# 🔐 Mood Tracker Web App with Suspicious Login Detection

A full-stack web application that helps users track their mood, improve mental well-being, and ensures enhanced security with **intruder detection during failed login attempts**.

---

## 📌 Features

### 🧠 Mood Tracking System

* Analyze user mood input
* Detect emotions (happy, sad, anxious, etc.)
* Provide quotes, suggestions, and activities
* Store mood history for logged-in users

### 🎮 Interactive Activities

* Breathing exercise
* Diary writing
* To-do planner
* Mini games (Ludo, Mario)

### 👤 User Authentication

* User registration and login system
* Password hashing for security
* Session-based login management

---

## 🔐 Suspicious Login Detection (Security Feature)

This project includes an advanced **intruder detection system**:

* 📷 Captures user image using webcam during login
* 🚨 Detects failed login attempts
* 🗂 Stores:

  * Username
  * IP address
  * Timestamp
  * Captured image
* 🖥️ Admin dashboard to view suspicious activity

---

## ⚙️ Technologies Used

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python (Flask)
* **Database:** SQLite
* **Browser API:** `getUserMedia()` (for camera access)

---

## 📁 Project Structure

```
project/
│
├── main.py
├── app.db
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   └── security.html
│
└── static/
    ├── uploads/
    └── suspicious/   # stores captured intruder images
```

---

## 🚀 How to Run the Project

### 1️⃣ Clone the repository

```
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2️⃣ Install dependencies

```
pip install flask
```

### 3️⃣ Run the application

```
python main.py
```

### 4️⃣ Open in browser

```
http://localhost:5001
```

---

## 🔄 How Suspicious Detection Works

1. User clicks **Login**
2. Camera captures image using JavaScript
3. Image is sent to Flask backend
4. If login fails:

   * Image is saved in `static/suspicious`
   * Log is stored in database
5. Admin can view logs and images

---

## 📊 Database Tables

### users

* id, username, email, password_hash

### moods

* user_id, input, emotion, quote, action, created_at

### security_logs

* username, action, ip_address, created_at, image

---

## 🛡️ Security Benefits

* Detect unauthorized login attempts
* Capture intruder identity
* Maintain login history
* Improve system transparency

---

## 🔮 Future Improvements

* Face recognition for intruder detection
* Email alerts on suspicious activity
* Multi-factor authentication (MFA)
* AI-based emotion detection

---

## 👩‍💻 Author

Developed by **ayu7714 n Harleyquinn-05** 💻
BCA Student | Cybersecurity Enthusiast

---
## ⭐ Acknowledgement

This project was built as part of learning **web development + cybersecurity concepts** by combining user experience with real-world security features.

---
📌 Note

Make sure to allow camera permissions in the browser for the security feature to work properly.
