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

## Project layout

- `flood_ai_system/` - Django project configuration
- `predictor/` - risk prediction application, templates, and static files
- `manage.py` - Django command-line entry point

The local SQLite database and virtual environment are intentionally excluded from Git.