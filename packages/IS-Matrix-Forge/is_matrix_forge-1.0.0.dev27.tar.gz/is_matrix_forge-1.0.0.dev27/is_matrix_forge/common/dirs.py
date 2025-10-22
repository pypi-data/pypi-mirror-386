"""
Directory configuration for the LED Matrix Battery application.

This module provides platform-specific directory paths for storing application
data, configuration files, and other resources using the platformdirs library.
"""

from platformdirs import PlatformDirs


APP_DIRS    = PlatformDirs('LEDMatrixLib', appauthor='Inspyre Softworks')
APP_DIR     = APP_DIRS.user_data_path
PRESETS_DIR = APP_DIR.joinpath('presets')


__all__ = [
    'APP_DIRS',
    'APP_DIR',
    'PRESETS_DIR',
]
