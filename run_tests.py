
import sys
import os
import pytest

# Add the current directory to sys.path so that 'app_main' can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    # Run pytest on the tests directory
    sys.exit(pytest.main(["tests/test_pcp_workflow.py", "-v"]))
