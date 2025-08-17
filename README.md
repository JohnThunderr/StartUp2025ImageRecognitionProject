
# Flask Application

A Flask web application with user authentication, role-based dashboards (customer vs developer), and an integrated webcam streaming feature using OpenCV.

✅ Add webcam streaming inside the dashboard

✅ Support multiple user roles (customer, developer)

✅ Auto-create database on first run

  

## ✨ Features

🔐 Authentication: Sign up, login, logout (secure password hashing with pbkdf2:sha256)

👥 Role-based dashboards:

Customer → sees webcam option

Developer → sees webcam option + extra tools (future features)

📸 Webcam streaming: View your webcam feed inside the browser

🗄 SQLite database: Auto-generated on first run, no setup required



## 📦 Requirements

Python 3.8+

IDE (to make changes in webcam features)



## 🚀 Getting Started
1. Clone repo
```
git clone https://github.com/JohnThunderr/StartUp2025ImageRecognitionProject.git
```
2. Install dependencies 
```
pip install -r requirements.txt
```
3. Run the app 
```
python main.py
```



## 👥 User Roles

New signups are customers by default

To promote a user to developer:

You can use database.db in DB Browser for SQLite and update it manually to developer role (at this moment, future updates may have different option)  



