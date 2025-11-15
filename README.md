# Onco-Navigator AI - Bridging India's Cancer Care Gap

An AI-powered cancer care platform that streamlines early detection and specialist referral through three core pillars:
1. AI-Assisted Triage for Primary Care
2. Tele-Oncology Hub for Specialists
3. Patient Monitoring & Symptom Tracking

## Features

- **AI-Powered Mammography Analysis**: CNN model for breast cancer detection
- **Geolocation-Based Emergency Services**: Find nearest hospitals with real-time location
- **Patient Symptom Monitoring**: Daily check-in system for ongoing care
- **Tele-Oncology Workflow**: Streamlined communication between PCPs and oncologists
- **Responsive Web Interface**: Professional medical UI with mobile support

## Technology Stack

- **Backend**: Python, FastAPI
- **AI/ML**: TensorFlow, Keras
- **Database**: MongoDB (optional)
- **Frontend**: HTML, CSS, JavaScript with Jinja2 templating
- **APIs**: Geoapify for geolocation services
- **Deployment**: Uvicorn server

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- MongoDB account (optional, for data persistence)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cancer-mega-project
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your configuration:
     ```
     GEOAPIFY_API_KEY=your_geoapify_api_key_here
     MONGODB_URI=your_mongodb_connection_string_here
     ```

## Usage

1. Start the application:
   ```bash
   python app_main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Project Structure

```
├── app_main.py          # Main application file
├── ml/
│   └── breast_cancer_cnn.h5  # Pre-trained AI model
├── static/
│   └── medical-theme.css     # Styling
├── templates/
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── pcp.html         # Primary Care Provider interface
│   ├── pcp_result.html  # PCP result display
│   ├── oncologist.html  # Oncologist dashboard
│   └── patient.html     # Patient portal
├── .env                 # Environment variables (gitignored)
├── .env.example         # Example environment variables
└── requirements.txt     # Python dependencies
```

## Environment Variables

- `GEOAPIFY_API_KEY`: API key for Geoapify geolocation services
- `MONGODB_URI`: MongoDB connection string (optional)
- `APP_HOST`: Host address (default: 0.0.0.0)
- `APP_PORT`: Port number (default: 8000)
- `MODEL_PATH`: Path to AI model (default: ml/breast_cancer_cnn.h5)

## Key Features Explained

### Emergency Services
Click the "🚨 Emergency" button to:
- Access your real-time location
- Find the 5 nearest hospitals
- View distances and estimated travel times
- See hospital contact information

### AI Triage System
- Upload mammography images for AI analysis
- Get risk assessment scores (0.000 to 1.000)
- Automatic forwarding of high-risk cases to oncologists
- Visual preview of uploaded scans (properly sized)

### Tele-Oncology Hub
- View AI-flagged cases in a prioritized worklist
- Access case details and patient information
- Monitor case status and history

### Patient Portal
- Daily symptom check-in system
- View personal health information
- Track case status

## Security

- All sensitive configuration stored in `.env` file
- `.env` file is gitignored for security
- Use `.env.example` as a template for new deployments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is for educational and demonstration purposes.

## Acknowledgments

- Developed for the Indian HealthTech Hackathon 2025
- Uses TensorFlow for AI model implementation
- Geolocation services powered by Geoapify