# Flood Risk Prediction System

A Django application for assessing flood risk from rainfall, river level, and area type inputs. Prediction history is stored in the local database for later review.

## Requirements

- Python 3.10 or newer
- Django

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install django
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser.

## Prediction model

The application uses a `RandomForestClassifier` when the database contains at least six labeled reports covering `LOW`, `MEDIUM`, and `HIGH` outcomes. With less training data, it uses the transparent rule-based fallback so predictions are not made from an incomplete model. Replace the starter history with real labeled flood observations before relying on the model for operational decisions.

## Project layout

- `flood_ai_system/` - Django project configuration
- `predictor/` - risk prediction application, templates, and static files
- `manage.py` - Django command-line entry point

The local SQLite database and virtual environment are intentionally excluded from Git.

## Accounts and password reset

Users can create an account with their name, username, email, and password. Existing users can sign in with either their username or email address. The **Forgot your password?** flow sends a one-time reset link to the account email.

Saved flood reports are private per user. Each new report is linked to the account that created it, and the history page only shows that user’s reports. Reports created before account ownership was added remain unassigned and are hidden from user histories.

The prediction form is public, so visitors can check flood risk without an account. Anonymous predictions are not saved; users can sign in or create an account when they want report history.

For local development, reset emails are printed in the Django server console. For real email delivery, replace `EMAIL_BACKEND` in `flood_ai_system/settings.py` with an SMTP backend and configure the SMTP host, port, username, password, and TLS settings through environment variables.