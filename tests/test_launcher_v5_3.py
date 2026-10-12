import pytest
from moth_launcher_v5_3.cli import select_runtime,LauncherUsageError

@pytest.mark.parametrize('version',['4.7','4.8','4.9','5.0','5.1','5.2','5.3'])
def test_all_versions_remain_selectable(version):
    assert select_runtime(['--runtime',version,'status'])==(version,['status'])

@pytest.mark.parametrize('args',[[],['--runtime','9.9'],['--runtime','5.3','--runtime','5.2']])
def test_explicit_unique_runtime_required(args):
    with pytest.raises(LauncherUsageError):select_runtime(args)
