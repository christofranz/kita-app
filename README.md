# Project Name: **Kita App Backend API**

**Version:** 1.0.0  
**Release Date:** 2024-11-05  

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [API Documentation](#api-documentation)
4. [Installation and Setup](#installation-and-setup)
5. [Configuration](#configuration)
6. [Versioning](#versioning)
7. [Changelog](#changelog)
8. [Contributing](#contributing)
9. [License](#license)

---

### Project Overview

This is the backend API for the **Kita App**, a child event management app designed for use by parents, teachers, and administrators. The backend API is built with **Flask** and **MongoDB**, deployed on **Heroku**, and uses **Firebase Authentication** for secure user management.

### Features

- User authentication with Firebase (login, register, email verification)
- Event and feedback management for children’s activities
- Role-based access control for parents, teachers, and admins
- Secure data handling and API rate limiting

---

### API Documentation

Full API documentation is available via the Swagger UI.  
**Access the Swagger UI at:** `https://<your-heroku-app>.herokuapp.com/docs`

---

### Installation and Setup

#### Prerequisites

- **Python 3.8+**
- **MongoDB** (local or cloud)
- **Firebase project** setup

#### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/kita-app-backend.git
   cd kita-app-backend
   ```
2. Install dependencies, preferrably in a virtual environment:
    ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Use .env.example as a template and create a .env file with your configuration.
   - Key environment variables:
      - FLASK_SECRET_KEY: Flask app secret
      - JWT_SECRET_KEY: JWT signing key
      - MONGO_URI: MongoDB connection URI
      - FIREBASE_CREDENTIALS: Path to your Firebase credentials JSON

4. Run the app
   ```bash
   python run.py
   ```

---

### Configuration

- **Environment Variables**: Required variables for production are in ```.env.example```.
- **Firebase Credentials**: Store ```firebase_credentials.json``` securely; do not commit it to version control.
- **Deployment**: E.g. on Heroku, set environment variables in the Heroku dashboard.

---

### Versioning

This project follows **semantic versioning**:

- Major version updates introduce significant changes and may include breaking changes.
- Minor updates add new features but are backward-compatible.
- Patch updates include bug fixes or improvements that are backward-compatible.
  

Current Version: 1.0.0

#### Version Endpoint (TODO)
Clients can retrieve the current API version by calling:
    ```http
    python run.py
    ```

Example response:
    ```json
    {
        "api_version": "2.0.0",
        "release_date": "2024-10-01",
        "status": "stable",
        "min_supported_version": "1.5.0"
    }
    ```

---

### Changelog
Version 1.0.0 (2024-11-05)
Initial release with core event and user management features.

---

### License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.