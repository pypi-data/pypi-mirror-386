from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name             = "rakib-django-core",
    version          = "0.1.2",  
    author           = "Md. Rakib Hassan",
    author_email     = "rakib1515hassan@gmail.com",
    description      = "This is a Django-based web application for managing core functionalities.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url              = "https://github.com/rakib1515hassan/django-core-app",
    packages         = find_packages(exclude=['*.pyc', '__pycache__']),  # exclude add করুন
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Django>=3.2",
    ],
    include_package_data=True,
    exclude_package_data={
        '': ['*.pyc', '__pycache__/*'],  # pycache files exclude করুন
    },
)