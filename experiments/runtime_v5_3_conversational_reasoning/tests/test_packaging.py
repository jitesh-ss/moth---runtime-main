import json,os,subprocess,sys,hashlib
from pathlib import Path
import pytest
from moth_runtime_v5_3.build_artifact import build_artifact
from moth_runtime_v5_3.artifact import ModelArtifact53
from moth_runtime_v5_3.runtime import Runtime53
from moth_runtime_v5_3.legacy.model import IntegrityError
from moth_runtime_v5_3.energy.schema import Runtime53Failure,Level
from moth_runtime_v5_3.tensor_data import put_data,read_data
from moth_runtime_v5_3.persistence.objects import ObjectStore
from moth_runtime_v5_3.legacy.canonical import canonical_bytes

DELIVERY='Direct courier lacks cold storage. Direct courier has road permit. Direct courier can meet the deadline. Backup courier has refrigeration. Backup courier has road permit. Backup courier can meet the deadline. Can the proposed plan be used and which plan should replace it?'

def test_three_clean_builds(tmp_path):
    hashes=[build_artifact(tmp_path/str(i))['artifact_hash'] for i in range(3)]
    assert len(set(hashes))==1

def test_isolated_artifact(tmp_path,artifact):
    script='''import sys
from moth_runtime_v5_3.runtime import Runtime53
r=Runtime53.initialize(sys.argv[1],sys.argv[2]);c=r.create_conversation('')
x=r.turn(c,'Take package A to room 3.')
assert x['status']=='ANSWER'
assert r.reexecute(c,x['turn_id'])['verified']
assert not any(k.startswith('moth_runtime') and not (k=='moth_runtime_v5_3' or k.startswith('moth_runtime_v5_3.')) for k in sys.modules)
'''
    env={**os.environ,'PYTHONPATH':str(artifact/'runtime'),'PYTHONDONTWRITEBYTECODE':'1'}
    result=subprocess.run([sys.executable,'-B','-c',script,str(tmp_path/'isolated'),str(artifact)],cwd=tmp_path,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr

def test_artifact_tamper(tmp_path,artifact):
    import shutil
    dst=tmp_path/'tamper';shutil.copytree(artifact,dst)
    with (dst/'conversation-foundation.json').open('ab') as f:f.write(b' ')
    with pytest.raises(IntegrityError):ModelArtifact53.open(dst)

def test_compatibility_reexecution(runtime):
    cid=runtime.create_conversation('')
    for presentation in [None,'Return compact JSON.','explain the result in detail']:
        result=runtime.turn(cid,DELIVERY,presentation)
        assert result['status']=='ANSWER'
        assert runtime.reexecute(cid,result['turn_id'])['verified']
    runtime.turn(cid,'Package A is in room 4.')
    assert runtime.verify_conversation(cid)['verified']

def test_tensor_canonical_tamper(tmp_path):
    store=ObjectStore(tmp_path)
    envelope=put_data(store,{'fact':'x','active':True},'knowledge')
    assert read_data(envelope,'knowledge')['active']
    with envelope.path.open('r+b') as f:f.seek(-1,2);f.write(b'!')
    with pytest.raises(Runtime53Failure):store.open(envelope.file_hash)

def test_older_artifact_rejected(tmp_path):
    root=Path(__file__).resolve().parents[3]
    old=root/'config/v5.2/model/model-5.2'
    with pytest.raises(IntegrityError):Runtime53.initialize(tmp_path/'store',old)

def test_layer_conflict_rolls_back(runtime):
    from moth_runtime_v5_3.persistence.store import ConcurrentTurnError
    cid=runtime.create_conversation('')
    prepared=runtime.prepare(cid,'Package A is in room 4.')
    hashes,policy=runtime._policy53(prepared);solved=runtime.solve(prepared)
    field=runtime.compile_hcf_field({'schema':'moth-hcf-source/5.3','entries':[{'meaning_id':'test','effect':'OBSERVE','scope':'conversation.message','value':'x'}],'activations':[]},Level.CONTEXT)
    runtime.upsert_layer_field(cid,Level.CONTEXT,'test',field['object_hash'],0)
    with pytest.raises(Runtime53Failure,match='CONCURRENT_LAYER_REVISION'):runtime.commit(prepared,solved,hashes,policy)
    assert runtime.store.conversation(cid)['head_sequence']==0
    assert runtime._knowledge(cid)[0] is None

def test_interrupted_commit_rolls_back(runtime):
    cid=runtime.create_conversation('')
    with runtime.store._connect() as db:
        db.execute("CREATE TRIGGER abort_knowledge BEFORE INSERT ON knowledge_revisions BEGIN SELECT RAISE(ABORT,'fault'); END")
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError,match='fault'):runtime.turn(cid,'Package A is in room 4.')
    assert runtime.store.conversation(cid)['head_sequence']==0
    assert runtime._knowledge(cid)[0] is None
    assert not [m for m in runtime.store.messages(cid) if m['role']=='USER']
