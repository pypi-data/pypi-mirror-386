# __init__.py

# Import classes and functions from submodules
from .centree import *
from .workbench import *
from .termite import *
from .termite7 import *
from .scibite_search import *
from .utilities import *

# Read package metadata from __version__.py
from .__version__ import __version__, __author__, __copyright__, __license__, __email__

# Function to print or return the version info
def toolkit_version():
    return f"SciBite-Toolkit {__version__}\n Author: {__author__}\n Copyright: {__copyright__}\n License: {__license__}"