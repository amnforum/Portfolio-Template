import os
import sys
from pathlib import Path

path = str(Path(__file__).resolve().parent)
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_project.settings')

from portfolio_project.wsgi import application
app = application
