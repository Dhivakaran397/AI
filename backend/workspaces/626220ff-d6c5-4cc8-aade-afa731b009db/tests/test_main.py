import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from main import execute_task

def test_execute_task():
    res = execute_task()
    assert res['status'] == 'success'
    assert 'goal' in res
