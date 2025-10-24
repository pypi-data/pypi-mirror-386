#!/usr/bin/env python3
"""
xwnode Integration Tests Runner
=============================

Simple script to run xwnode integration tests independently.
Can be used for development and debugging.
Following Python/pytest best practices.
"""

import sys
import subprocess
import os
from pathlib import Path

def setup_environment():
    """Setup the Python environment for running tests."""
    # Use xwsystem utility for path setup
    try:
        from src.xlib.xwsystem.utils.paths import setup_python_path
        project_root, src_path = setup_python_path(__file__, levels_up=6)
        return project_root, src_path
    except ImportError:
        # Fallback to manual calculation if xwsystem not available
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent.parent.parent
        src_path = project_root / "src"
        
        # Add src to Python path
        src_path_str = str(src_path)
        if src_path_str not in sys.path:
            sys.path.insert(0, src_path_str)
        
        return project_root, src_path

def main():
    """Run the xwnode integration tests."""
    try:
        # Setup environment first
        project_root, src_path = setup_environment()
        
        current_dir = Path(__file__).parent
        test_file = current_dir / "test_integration.py"
        
        print("🧪 Running xwnode Integration Tests")
        print("=" * 40)
        print(f"Project root: {project_root}")
        print(f"Source path: {src_path}")
        print(f"Test file: {test_file}")
        print(f"Current working directory: {Path.cwd()}")
        print()
        
        # Verify the test file exists
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return 1
        
        # Verify project root exists
        if not project_root.exists():
            print(f"❌ Project root not found: {project_root}")
            return 1
        
        # Verify src path exists
        if not Path(src_path).exists():
            print(f"❌ Source path not found: {src_path}")
            return 1
        
        # Build PYTHONPATH more robustly
        python_path_parts = [str(src_path), str(project_root)]
        existing_pythonpath = os.environ.get('PYTHONPATH', '')
        if existing_pythonpath:
            python_path_parts.append(existing_pythonpath)
        
        python_path = os.pathsep.join(python_path_parts)
        
        # Run pytest on the test file with proper environment
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], 
        check=False,
        cwd=str(project_root),  # Run from project root
        env={
            **dict(os.environ),
            'PYTHONPATH': python_path
        })
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main()) 