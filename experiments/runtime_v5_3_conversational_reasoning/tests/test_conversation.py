from pathlib import Path
import json
from copy import deepcopy
import pytest
from moth_runtime_v5_3.runtime import Runtime53
from moth_runtime_v5_3.knowledge import active_facts
from moth_runtime_v5_3.chat import verify_surface
from moth_runtime_v5_3.persistence.store import ConcurrentTurnError
FIXTURES=Path(__file__).resolve().parents[1]/'fixtures'

@pytest.mark.parametrize('case',json.loads((FIXTURES/'conversations-001.json').read_text()),ids=lambda c:c['id'])
def test_conversations(runtime,case):
    cid=runtime.create_conversation('')
    original=[]
    for step in case['turns']:
        result=runtime.turn(cid,step['message'])
        assert result['status']==step['status'],result
        original.append(result['turn_id'])
        runtime=Runtime53.open(runtime.store.root)
    assert case['last_contains'] in result['response']
    for turn in original:assert runtime.reexecute(cid,turn)['verified']

@pytest.mark.parametrize('case',json.loads((FIXTURES/'paraphrases-heldout-001.json').read_text()))
def test_heldout(runtime,case):
    cid=runtime.create_conversation('')
    result=runtime.turn(cid,case['message'])
    assert result['status']==case['status']

def test_historical_correction_and_surface_tamper(runtime):
    cid=runtime.create_conversation('')
    result=runtime.turn(cid,'Package A is in room 2.')
    runtime.turn(cid,'Actually, package A is in room 4.')
    assert runtime.reexecute(cid,result['turn_id'])['verified']
    artifact=deepcopy(result['conversation53']['surface']);artifact['text']='invented'
    with pytest.raises(ValueError):verify_surface(artifact,result['conversation53']['solved'])

def test_atomic_conflict(runtime):
    cid=runtime.create_conversation('')
    prepared=runtime.prepare(cid,'Package A is in room 3.')
    hashes,policy=runtime._policy53(prepared);solved=runtime.solve(prepared)
    runtime.turn(cid,'Package B is in room 4.')
    with pytest.raises(ConcurrentTurnError):runtime.commit(prepared,solved,hashes,policy)
    assert runtime.store.conversation(cid)['head_sequence']==1
    assert runtime.inspect_knowledge(cid)['active_facts']

def test_partial_message_applies_nothing(runtime):
    cid=runtime.create_conversation('')
    before=runtime.inspect_knowledge(cid)['facts']
    result=runtime.turn(cid,'Package A is in room 5 and bend spacetime.')
    assert result['status']=='CLARIFICATION_REQUIRED'
    assert runtime.inspect_knowledge(cid)['facts']==before

def test_dependency_invalidation():
    k={'facts':[{'id':'a','active':False,'dependencies':[]},{'id':'b','active':True,'dependencies':['a']},{'id':'c','active':True,'dependencies':['b']}]}
    assert not active_facts(k)

def test_negative_unknown_planning(runtime):
    cid=runtime.create_conversation('')
    runtime.turn(cid,'Package A is not in room 2.')
    result=runtime.turn(cid,'Take package A to room 3.')
    assert result['status']=='INSUFFICIENT_INFORMATION'

def test_policy_refusal_is_replayable(runtime):
    cid=runtime.create_conversation('')
    r=runtime.turn(cid,'Where is package A?',presentation='invalid')
    assert r['status']=='REFUSAL'
    assert runtime.reexecute(cid,r['turn_id'])['verified']

def test_ordered_goals_and_why(runtime):
    cid=runtime.create_conversation('')
    r=runtime.turn(cid,'Take package A to room 3 then take package A to room 4.')
    assert r['status']=='ANSWER'
    assert len(r['conversation53']['solved']['request']['goals'])==2
    why=runtime.turn(cid,"Why can't it get there?")
    assert why['status']=='ANSWER'
    assert r['response'] in why['response']

def test_budget_commits_facts_and_reexecution(runtime):
    cid=runtime.create_conversation('')
    # Budget is a compiled artifact setting; use a dedicated fixture copy below.
    from moth_runtime_v5_3.chat import prepare,solve
    from moth_runtime_v5_3.knowledge import initial_knowledge,state_from
    source=deepcopy(runtime.chat_source);source['limits']['expansions']=0
    next,prepared=prepare(source,initial_knowledge(source),'Package A is in room 4. Take it to room 3.','m',{})
    assert solve(prepared)['status']=='BUDGET_EXHAUSTED'
    assert state_from(next)['packagea.location']=='room4'

def test_persistent_facts_beyond_recent_text(runtime):
    cid=runtime.create_conversation('')
    first=runtime.turn(cid,'Package A is in room 5.')
    # An over-budget intervening message is recorded but never deletes knowledge.
    runtime.turn(cid,'noise '*600)
    final=runtime.turn(cid,'Where is package A?')
    assert final['status']=='ANSWER' and 'room5' in final['response']
    assert runtime.reexecute(cid,first['turn_id'])['verified']

def test_impossible_chat_and_replay(runtime):
    cid=runtime.create_conversation('')
    runtime.turn(cid,'Robot one is in room six. Robot one has 0 battery.')
    result=runtime.turn(cid,'Take package A to room three.')
    assert result['status']=='IMPOSSIBLE'
    assert runtime.reexecute(cid,result['turn_id'])['verified']

def test_chat_structured_python_is_inert(runtime):
    from moth_runtime_v5_3.surface import recover_surface_value
    cid=runtime.create_conversation('')
    r=runtime.turn(cid,'Take package A to room three.',presentation='Return compact Python.')
    assert r['status']=='ANSWER'
    assert recover_surface_value(r['response'],r['response_mode'])['status']=='ANSWER'
    assert r['deterministic']['dispatch_count']==0
    assert runtime.reexecute(cid,r['turn_id'])['verified']

def test_oversized_message_refuses_without_crashing(runtime):
    cid=runtime.create_conversation('')
    result=runtime.turn(cid,'x'*20000)
    assert result['status']=='REFUSAL'
    assert runtime.reexecute(cid,result['turn_id'])['verified']

def test_followups_do_not_recursively_embed_history(runtime):
    cid=runtime.create_conversation('')
    plan=runtime.turn(cid,'Take package A to room 3.')
    for _ in range(3):
        why=runtime.turn(cid,'Why?')
        assert why['response'].count(plan['response'])==1
        assert runtime.reexecute(cid,why['turn_id'])['verified']

def test_existing_inspection_commands_on_chat(runtime):
    cid=runtime.create_conversation('')
    result=runtime.turn(cid,'Take package A to room 3.')
    assert runtime.inspect_context(cid)['messages']
    assert runtime.inspect_hcf(cid,result['turn_id'])['transient_context_object_hashes']
