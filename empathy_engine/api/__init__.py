"""
EmpathyEngine API Layer
FastAPI-based REST API for remote/distributed use
"""

from .server import app, EmpathyAPI

__all__ = ['app', 'EmpathyAPI']
