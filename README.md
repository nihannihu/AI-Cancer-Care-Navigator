---
title: Onco Navigator AI
emoji: 🩺
colorFrom: blue
colorTo: green
sdk: docker
pinned: true
app_port: 7860
---

# 🩺 Onco-Navigator AI: Bridging the Cancer Care Gap

**An Advanced AI-Powered Platform for Early Detection, Specialist Referral, and Patient Support.**

> *Accurate Triage. Instant Specialist Access. Compassionate Care.*

![Banner](https://img.shields.io/badge/Status-Live-green) ![License](https://img.shields.io/badge/License-MIT-blue) ![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688) ![AI](https://img.shields.io/badge/AI-Gemini%20%26%20TensorFlow-orange)

## 📖 Overview

**Onco-Navigator AI** is a comprehensive digital health solution designed to address critical gaps in oncology care, particularly in resource-constrained settings. By leveraging state-of-the-art **Artificial Intelligence** and **Telemedicine**, it creates a seamless ecosystem connecting Primary Care Physicians (PCPs), Oncologists, and Patients.

The platform streamlines the journey from initial suspicion to treatment and ongoing management, ensuring no patient is lost to follow-up.

## 🚀 Key Features

### 1. 🤖 AI-Assisted Triage (For PCPs)
-   **Deep Learning Analysis:** Utilizes `MobileNetV2` / Custom CNNs to analyze mammography and histology images for immediate risk assessment.
-   **Risk Scoring:** Provides a confidence-based risk score (Low, Medium, High) to prioritize urgent cases.
-   **Automated Referrals:** Instantly flags high-risk cases for oncologist review.

### 2. 🏥 Tele-Oncology Hub (For Specialists)
-   **Unified Workflow:** A centralized dashboard for oncologists to review prioritized cases, images, and patient history.
-   **AI-Enhanced Medical Timeline:** Automatically aggregates patient history into a chronological timeline for rapid decision-making.
-   **Secure Communication:** Direct communication channels for treatment planning.

### 3. ❤️ Patient Compassion Portal
-   **AI Health Assistant:** A 24/7 empathetic chatbot powered by **Google Gemini Pro** to answer medical queries, explain reports, and provide emotional support.
-   **Lab Report Analysis:** Uses OCR and NLP to extract key metrics (WBC, Hemoglobin, etc.) from uploaded PDF lab reports and explain them in plain language.
-   **Medicine Adherence:** Tracks medication schedules (Chemo/Hormonal therapy) with reminders.
-   **Voice Symptom Log:** Allows patients to record symptoms via voice, which AI transcribes and adds to their clinical record.
-   **QR Code Profile:** Generates a secure QR code for instant sharing of medical history with emergency responders or new doctors.
-   **Emergency Locator:** Real-time geolocation to find the nearest cancer care centers and hospitals.

## 🛠️ Technology Stack

High-performance, scalable, and secure architecture.

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | **Python, FastAPI** | High-performance async API framework. |
| **AI (LLM)** | **Google Gemini 1.5 Flash/Pro** | Natural Language Processing for chatbot, report analysis, and insights. |
| **AI (Vision)** | **TensorFlow / Keras** | Convolutional Neural Networks for medical image classification. |
| **Database** | **MongoDB** | NoSQL database for flexible patient records and medical data. |
| **Frontend** | **HTML5, CSS3, JavaScript** | Responsive, accessible UI served via Jinja2 templates. |
| **ML Ops** | **Hugging Face Spaces** | Cloud deployment and model hosting. |
| **Services** | **Geoapify, SMTP** | Location services and Email notifications. |
| **Security** | **PBKDF2 Hashing, JWT** | Robust authentication and secure session management. |

## 🏗️ Installation & Local Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/nihannihu/AI-Cancer-Care-Navigator.git
    cd AI-Cancer-Care-Navigator
    ```

2.  **Set Up Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file (see `.env.example`) and add your keys:
    ```env
    GEMINI_API_KEY=your_key
    MONGODB_URI=your_mongo_db
    SMTP_PASS=your_app_password
    ```

5.  **Run the Application**
    ```bash
    python app_main.py
    ```
    Visit `http://localhost:8000` in your browser.

## 📸 Screenshots

*(Add screenshots of your Dashboard, AI Analysis, and Chatbot here)*

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📜 License

MIT License. Built for the **Indian HealthTech Hackathon 2025**.