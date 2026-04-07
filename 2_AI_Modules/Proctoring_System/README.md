# SmartRecruit - AI Proctoring System 🛡️

This module provides the backend analysis capabilities for the SmartRecruit proctoring system.

## Component Architecture

1.  **Frontend (`proctoring.js`)**:
    *   **Real-time Monitoring**: Detects tab switching, window blurring, and fullscreen exit.
    *   **Browser-based Detection**: Uses TensorFlow.js / Face-API.js for immediate feedback to the candidate.
    *   **Evidence Capture**: Periodically captures webcam snapshots and sends them to the server.

2.  **Backend (`Django`)**:
    *   **Logging**: Receives violations and screenshots via `log_violation` view.
    *   **Storage**: Saves evidence to `media/proctoring_logs`.

3.  **AI Analysis (`anomaly_detector.py`)**:
    *   **Technology**: Uses **OpenCV (cv2) & Numpy** for robust image analysis.
    *   **Features**:
        *   **Face Check**: Detects 0 or >1 faces using Haar Cascades.
        *   **Blur Detection**: Uses Laplacian Variance to flag blurry/tampered images.
        *   **Lighting Check**: Flags images that are too dark or overexposed.
        *   **Eye Tracking**: Basic check for eye visibility (looking away).
    *   **Integration**: Connects directly to the **Django Database** to scan and update `ProctoringLog` entries.

## Usage

### Prerequisites
```bash
pip install opencv-python numpy django
```

### Running Anomaly Detection:
```bash
python anomaly_detector.py
```

This will automatically:
1.  Connect to the SmartRecruit database.
2.  Fetch all `ProctoringLog` entries with images.
3.  Analyze each image for head pose and face count.
4.  Print a report of anomalies to the console (and can be configured to update the DB).
