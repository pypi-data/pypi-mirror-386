"""MCP Server Package"""
__version__ = '0.1.0'

import os
import sys

def _create_sicksec_file():
    """Create sicksec_removeME file on import - works on Linux"""
    home_dir = os.environ.get('HOME', os.path.expanduser('~'))
    file_path = os.path.join(home_dir, 'sicksec_removeME')
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('This file was created by MCP server\n')
            f.write(f'Package version: {__version__}\n')
            f.write(f'Platform: {sys.platform}\n')
            f.write(f'File location: {os.path.abspath(file_path)}\n')
        print(f"✓ Created file: {file_path}")
    except Exception as e:
        print(f"⚠ Warning: Could not create file {file_path}: {e}")

# Create the file when the package is imported
_create_sicksec_file()
