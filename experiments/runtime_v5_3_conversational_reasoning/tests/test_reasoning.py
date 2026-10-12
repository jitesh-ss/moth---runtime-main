from collections import deque
from copy import deepcopy
from dataclasses import replace
import pytest
from moth_runtime_v5_3.reasoning import Kernel53,ReasoningRequest,LIMITS
from moth_runtime_v5_3.checker import verify

# An independent test-only oracle uses its own queue, transitions and goal check.
def oracle(domain,initial,goal):
    names=sorted(initial);start=tuple(initial[k] for k in names)
    queue=deque([(start,0)]);seen={start}
    while queue:
        values,depth=queue.popleft();state=dict(zip(names,values))
        if all(state[k]==v for k,v in goal.items()):return depth
        for a in domain['actions']:
            if any((state[k]!=v) if op=='eq' else state[k]==v for k,op,v in a['pre']):continue
            after=dict(state);after.update(a['effects']);key=tuple(after[k] for k in names)
            if key not in seen:seen.add(key);queue.append((key,depth+1))
    return None

def chain(depth):
    domain={'variables':{'position':[str(i) for i in range(depth+1)]},'actions':[
        {'id':f'step{i:02}','pre':[['position','eq',str(i)]],'effects':{'position':str(i+1)},'cost':1} for i in range(depth)]}
    return ReasoningRequest(domain,{'position':'0'},[{'position':str(depth)}])

@pytest.mark.parametrize('depth',[2,4,8,12])
def test_depth_oracle(depth):
    req=chain(depth);result=Kernel53().solve(req)
    assert result.status=='ANSWER';assert len(result.plan)==oracle(req.domain,req.initial,req.goals[0])==depth
    assert verify(req,result)
    with pytest.raises(ValueError):verify(req,replace(result,plan=result.plan[::-1]))

def test_impossible_closed_certificate():
    req=chain(4);req.domain['actions'].pop()
    r=Kernel53().solve(req)
    assert r.status=='IMPOSSIBLE';assert oracle(req.domain,req.initial,req.goals[0]) is None;assert verify(req,r)
    bad=deepcopy(r.certificate);bad['states'].pop()
    with pytest.raises(ValueError):verify(req,replace(r,certificate=bad))

@pytest.mark.parametrize('limits',[{'depth':1},{'expansions':1}])
def test_cutoff_not_impossible(limits):
    req=replace(chain(4),limits={**LIMITS,**limits});r=Kernel53().solve(req)
    assert r.status=='BUDGET_EXHAUSTED';assert verify(req,r)

def test_unknown_and_binding_tamper():
    req=replace(chain(4),initial={});r=Kernel53().solve(req)
    assert r.status=='INSUFFICIENT_INFORMATION'
    with pytest.raises(ValueError):verify(replace(req,bindings={'forged':'value'}),r)

def test_hard_forbidden_actions():
    req=replace(chain(4),constraints={'forbidden_actions':['step00']})
    r=Kernel53().solve(req);assert r.status=='IMPOSSIBLE';assert verify(req,r)

def ordered_oracle(domain,initial,goals):
    keys=sorted(initial)
    def phase(s,p):
        while p<len(goals) and all(s[k]==v for k,v in goals[p].items()):p+=1
        return p
    first=(tuple(initial[k] for k in keys),phase(initial,0))
    queue=deque([(first,0)]);seen={first}
    while queue:
        (values,p),depth=queue.popleft();state=dict(zip(keys,values))
        if p==len(goals):return depth
        for action in domain['actions']:
            legal=True
            for variable,op,value in action['pre']:
                if (op=='eq' and state[variable]!=value) or (op=='ne' and state[variable]==value):legal=False;break
            if legal:
                nxt=dict(state);nxt.update(action['effects']);key=(tuple(nxt[k] for k in keys),phase(nxt,p))
                if key not in seen:seen.add(key);queue.append((key,depth+1))
    return None

@pytest.mark.parametrize('depth',[2,4,8,12])
def test_logistics_oracle(depth,runtime):
    source=runtime.chat_source
    initial={**source['defaults'],'packagea.location':'room1'}
    if depth==2:goals=[{'robot1.location':'room3'}]
    else:goals=[{'packagea.location':room} for room in ['room3','room1','room3'][:depth//4]]
    req=ReasoningRequest(source['domain'],initial,goals)
    r=Kernel53().solve(req)
    assert r.status=='ANSWER'
    assert len(r.plan)==depth==ordered_oracle(req.domain,initial,goals)
    assert verify(req,r)
