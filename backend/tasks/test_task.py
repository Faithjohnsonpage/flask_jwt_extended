#!/usr/bin/python3
from api.v1.app import app

celery = app.celery

@celery.task(name="test.add")
def add(x, y):
    return x + y
