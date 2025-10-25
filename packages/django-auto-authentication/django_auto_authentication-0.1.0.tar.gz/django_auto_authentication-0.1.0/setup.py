from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="django_auto_authentication",  # Unique package name
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,  # include templates, static, etc.
    install_requires=[
        "django>=4.0",  # ensure compatible with Django 4.x+
    ],
    python_requires='>=3.10',
    description="A reusable Django authentication package with login, register, dashboard, and home page.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jagritiS/django_auto_authentication",  # link to your GitHub
    author="Jagriti Srivastava",
    author_email="jagritisrvstv@gmail.com",  # replace with your email
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
