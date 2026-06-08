import sys
import os

# Add the project directory to the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the flask application instance as 'application' for mod_wsgi
from app import app as application
