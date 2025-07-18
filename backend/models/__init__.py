#!/usr/bin/env python3
"""
Initialize the models package
"""
from models.engine.db import DB

# Import all model classes here so Alembic can see them
from models.user import User

storage = DB()
storage.reload()
