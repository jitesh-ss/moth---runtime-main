from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[3]
CANDIDATE=Path(__file__).resolve().parents[1]/'candidate'
sys.path.insert(0,str(CANDIDATE))
from moth_runtime_v5_3.build_artifact import build_artifact
from moth_runtime_v5_3.runtime import Runtime53

@pytest.fixture(scope='session')
def artifact(tmp_path_factory):
    path=tmp_path_factory.mktemp('artifact53')
    build_artifact(path)
    return path

@pytest.fixture
def runtime(tmp_path,artifact):
    return Runtime53.initialize(tmp_path/'store',artifact)
