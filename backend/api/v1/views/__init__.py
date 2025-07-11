#!/usr/bin/env python3
"""Blueprint for API """
from flask import Blueprint

app_views = Blueprint('app_views', __name__)


from api.v1.views.users import *
