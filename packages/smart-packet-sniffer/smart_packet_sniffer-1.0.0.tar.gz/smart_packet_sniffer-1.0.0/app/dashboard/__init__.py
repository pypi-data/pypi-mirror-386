"""Web dashboard package for Smart Packet Sniffer"""
from .routes import app, socketio

__all__ = ['app', 'socketio']