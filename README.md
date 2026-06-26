# File Integrity Checker

A complete offline File Integrity Checker web application built with Python Flask. It lets users upload a file, generate cryptographic hashes, and verify file integrity by comparing a known hash with a freshly generated one.

## Features

- Upload any file up to 100 MB
- Generate MD5, SHA-1, SHA-256, and SHA-512 hashes
- Verify a file against a pasted known hash
- Secure filename handling with `werkzeug.utils.secure_filename`
- Temporary uploads are deleted automatically after processing
- Hash reports can be downloaded as TXT files
- Copy hash values to the clipboard
- Drag-and-drop uploads
- Client-side validation, progress animation, and loading spinner
- Dark cybersecurity-inspired responsive interface
- No database, external APIs, paid services, Docker, or API keys

## Project Structure

```text
file-integrity-checker/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── index.html
│   └── result.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
├── uploads/
└── utils/
    └── hashing.py
```

## Requirements

- Python 3.10 or newer
- pip

## Run Locally

1. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the Flask app:

```bash
python app.py
```

4. Open the app in your browser:

```text
http://127.0.0.1:5000
```

## Deployment on Render

1. Push this project to a GitHub repository.
2. In Render, create a new Web Service.
3. Connect the GitHub repository.
4. Use these settings:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

5. Add an environment variable for production:

```text
SECRET_KEY=<your-random-secret-value>
```

6. Deploy the service.

## Security Notes

- Uploaded filenames are sanitized before saving.
- Files are stored only temporarily and removed after hashing.
- The app prevents oversized uploads with Flask's `MAX_CONTENT_LENGTH`.
- Hashing uses Python's standard `hashlib` library only.
- No uploaded file contents are sent to external services.

## Supported Hash Algorithms

- MD5
- SHA-1
- SHA-256
- SHA-512

MD5 and SHA-1 are included because they are still commonly encountered in legacy integrity workflows. For stronger modern integrity checks, prefer SHA-256 or SHA-512.
