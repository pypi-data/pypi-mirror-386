"""
#exonware/xwnode/src/exonware/xwnode/common/management/__init__.py

Management module for xwnode.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.26
"""

# Import and export main components
from pathlib import Path
import importlib

# Auto-discover and import all modules
_current_dir = Path(__file__).parent
for _file in _current_dir.glob('*.py'):
    if _file.name != '__init__.py' and not _file.name.startswith('_'):
        _module_name = _file.stem
        # Direct import - no fallback allowed
        globals()[_module_name] = importlib.import_module(f'.{_module_name}', package=__name__)

__all__ = []
