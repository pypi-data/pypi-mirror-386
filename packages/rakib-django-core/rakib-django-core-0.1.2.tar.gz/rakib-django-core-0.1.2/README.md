# Rakib App - Core Django Package

A reusable Django app for core functionalities including utilities, services, and management commands.

## Installation

### From Test PyPI (Development):
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rakib-django-core==0.1.1
```
### From PyPI (Stable Release):
```bash
pip install rakib-django-core
```

## Usage

### 1. Add to your Django project's INSTALLED_APPS:
```python
INSTALLED_APPS = [
    # ...
    'core',
]
```     

### 2. Run migrations if you're using the models:
```python
python manage.py migrate
``` 

## Features
- Custom management commands
- Utility functions
- Email and SMS services
- Template tags
- Context processors

## Available Management Commands
```python
python manage.py superuser
python manage.py staffuser
python manage.py newapp
python manage.py newapi
python manage.py appmigrations
python manage.py setup
```