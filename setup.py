"""
Setup script for building Claude Usage Tracker as a macOS app.
Usage: python setup.py py2app
"""

from setuptools import setup

APP = ['claude_usage.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'icon.icns',  # Optional: add your own icon
    'plist': {
        'CFBundleName': 'Claude Usage',
        'CFBundleDisplayName': 'Claude Usage',
        'CFBundleIdentifier': 'com.claudeusage.tracker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Hide from Dock (menu bar app)
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.14.0',
    },
    'packages': ['rumps', 'requests', 'keyring'],
}

setup(
    name='Claude Usage',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
