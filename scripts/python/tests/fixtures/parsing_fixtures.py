import pytest
import os

@pytest.fixture(scope="module")
def dirs_html():
    """sample html representing directory listings"""

    html_path = os.path.join(os.path.dirname(__file__), 'dirs.html')
    with open(html_path, 'r') as f:
        yield f.read()

@pytest.fixture(scope="module")
def files_html():
    """sample html representing a file listing"""

    html_path = os.path.join(os.path.dirname(__file__), 'files.html')
    with open(html_path, 'r') as f:
        yield f.read()
