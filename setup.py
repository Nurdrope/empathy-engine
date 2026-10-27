"""
EmpathyEngine - Multi-Modal Emotional Intelligence System
Setup configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="empathy-engine",
    version="1.0.1",
    author="Nurdrope",
    author_email="",
    description="Multi-modal emotional intelligence system combining text, voice, and pattern analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nurdrope/empathy-engine",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "simple"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    # Core: text sentiment (VADER) + voice prosody (librosa). Transformer-based
    # emotion detection lives in the [ml] extra because torch is ~2GB; without
    # it, analyze_emotions() logs an error and returns None fields while the
    # VADER quick path keeps working.
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "vaderSentiment>=3.3.2",
        "yake>=0.4.8",
        "empath>=0.89",
        "python-dateutil>=2.8.2",
        "librosa>=0.10.0",
        "soundfile>=0.12.1",
        "audioread>=3.0.0",
        "numba>=0.57.0",
    ],
    extras_require={
        "ml": [
            "transformers>=4.30.0",
            "torch>=2.0.0",
        ],
        "nlp": [
            "sentence-transformers>=2.2.2",
            "spacy>=3.6.0",
            "textstat>=0.7.3",
        ],
        "voice-advanced": [
            "opensmile>=2.4.1",
            "praat-parselmouth>=0.4.3",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.23.0",
            "python-multipart>=0.0.6",
            "pydantic>=2.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "all": [
            "transformers>=4.30.0",
            "torch>=2.0.0",
            "sentence-transformers>=2.2.2",
            "spacy>=3.6.0",
            "textstat>=0.7.3",
            "opensmile>=2.4.1",
            "praat-parselmouth>=0.4.3",
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.23.0",
            "python-multipart>=0.0.6",
            "pydantic>=2.0.0",
            "pydantic-settings>=2.0.0",
            "structlog>=23.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "empathy-engine-api=empathy_engine.api.server:main",
        ],
    },
)
