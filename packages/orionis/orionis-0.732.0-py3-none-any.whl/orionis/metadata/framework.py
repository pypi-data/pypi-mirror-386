#---------------------------------------------------------------------------
# Framework Metadata
#---------------------------------------------------------------------------

# Name of the framework
NAME = "orionis"

# Current version of the framework
VERSION = "0.732.0"

# Full name of the author or maintainer of the project
AUTHOR = "Raul Mauricio Uñate Castro"

# Email address of the author or maintainer for contact purposes
AUTHOR_EMAIL = "raulmauriciounate@gmail.com"

# Short description of the project or framework
DESCRIPTION = "Orionis Framework – Elegant, Fast, and Powerful."

#---------------------------------------------------------------------------
# Project URLs
#---------------------------------------------------------------------------

# URL to the project's skeleton or template repository (for initial setup)
SKELETON = "https://github.com/orionis-framework/skeleton"

# URL to the project's main framework repository
FRAMEWORK = "https://github.com/orionis-framework/framework"

# URL to the project's documentation
DOCS = "https://orionis-framework.com/"

# API URL to the project's JSON data
API = "https://pypi.org/pypi/orionis/json"

#---------------------------------------------------------------------------
# Python Requirements
#---------------------------------------------------------------------------

# Minimum Python version required to run the project
PYTHON_REQUIRES = ">=3.12"

#---------------------------------------------------------------------------
# Project Classifiers
#---------------------------------------------------------------------------

# List of classifiers that provide metadata about the project for PyPI and other tools.
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Typing :: Typed',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Internet :: WWW/HTTP :: WSGI',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

#---------------------------------------------------------------------------
# Project Keywords
#---------------------------------------------------------------------------

# List of keywords that describe the project and help with discoverability on package indexes.
KEYWORDS = [
    "orionis",
    "framework",
    "python",
    "orionis-framework",
    "granian",
    "asgi",
    "rsgi"
]

#---------------------------------------------------------------------------
# Project Dependencies
#---------------------------------------------------------------------------

# List of required packages and their minimum versions.
REQUIRES = [
    'apscheduler>=3.11.0',
    'python-dotenv>=1.0.1',
    'requests>=2.32.3',
    'rich>=13.9.4',
    'psutil>=7.0.0',
    'cryptography>=44.0.3',
    'setuptools>=68.0.0',
    'wheel>=0.42.0',
    'twine>=5.0.0',
    'pyclean>=3.1.0',
    'dotty-dict>=1.3.1',
    'granian>=2.5.5',
]

#---------------------------------------------------------------------------
# Function to retrieve the icon SVG code
#---------------------------------------------------------------------------

# This function reads the 'icon.svg' file from the current directory and returns its content.
def icon():
    """
    Retrieve the SVG code for the project's icon image.

    This function reads the 'icon.svg' file located in the same directory as this module and returns its content as a string. If the file is not found or cannot be read, it returns None.

    Returns
    -------
    str or None
        The SVG code as a string if the file is successfully read, otherwise None.
    """
    import os

    # Construct the absolute path to the 'icon.svg' file in the current directory
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'icon.svg')

    try:

        # Attempt to open and read the SVG file
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    except OSError:

        # Return None if the file is not found or unreadable
        return None

    except Exception:

        # Return None for any other exceptions that may occur
        return None