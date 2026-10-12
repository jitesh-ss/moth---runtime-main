"""Promotion and installed-entrypoint gates; full behavior panel lives with its experiment."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from moth_runtime_v5_3.runtime import Runtime53
from moth_runtime_v5_3.artifact import ModelArtifact53
from moth_runtime_v5_3.build_artifact import build_artifact

ROOT=Path(__file__).resolve().parents[1]
ARTIFACT=ROOT/'config/v5.3/model/model-5.3'

def test_promoted_artifact_and_source_lock():
    lock=json.loads((ROOT/'config/v5.3/ARCHITECTURE-LOCK.json').read_text())
    assert ModelArtifact53.open(ARTIFACT).artifact_hash==lock['artifact_hash']
    for path,expected in lock['files'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path

def test_preserved_previous_files():
    baseline=json.loads((ROOT/'experiments/runtime_v5_3_conversational_reasoning/fixtures/baseline-hashes.json').read_text())
    for path,expected in baseline.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path

def test_promoted_rebuild_is_identical(tmp_path):
    assert build_artifact(tmp_path/'artifact')['artifact_hash']==ModelArtifact53.open(ARTIFACT).artifact_hash

def test_installed_cli_chat_and_reexecution(tmp_path):
    base=[str(ROOT/'.venv/bin/moth'),'--runtime','5.3','--store',str(tmp_path/'store'),'--json']
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    def run(*args):
        p=subprocess.run([*base,*args],cwd=ROOT,env=env,text=True,capture_output=True)
        assert p.returncode==0,p.stderr
        return json.loads(p.stdout)
    run('init','--artifact',str(ARTIFACT))
    cid=run('session','create')['conversation_id']
    result=run('turn',cid,'Take package A to room three.')
    assert result['status']=='ANSWER'
    assert run('reexecute',cid,result['turn_id'])['verified']
    assert run('inspect','knowledge',cid)['active_facts']
    assert run('verify','--session',cid)['verified']
