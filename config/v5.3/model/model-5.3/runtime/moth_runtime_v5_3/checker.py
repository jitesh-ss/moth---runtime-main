"""Independent certificate checking: does not call planner/search helpers."""
from .reasoning import ReasoningRequest, ReasoningResult, validate_request

def verify(request: ReasoningRequest, result: ReasoningResult):
    validate_request(request)
    if result.request_hash != request.request_hash:
        raise ValueError('request binding changed')
    actions = {a['id']:a for a in request.domain['actions']}
    forbidden = set(request.constraints.get('forbidden_actions',[]))
    def progress(s,p):
        while p<len(request.goals) and all(s.get(k)==v for k,v in request.goals[p].items()):
            p+=1
        return p
    def apply(s,a):
        if a['id'] in forbidden or any((s.get(k)!=v) if op=='eq' else (k not in s or s[k]==v) for k,op,v in a['pre']):
            raise ValueError('illegal action')
        return {**s,**a['effects']}
    if result.status == 'ANSWER':
        state = dict(request.initial); phase = progress(state,0); cost=0
        if len(result.plan)>request.limits['depth']:
            raise ValueError('plan exceeds depth')
        for identifier in result.plan:
            if identifier not in actions:
                raise ValueError('unknown action')
            a=actions[identifier]; state=apply(state,a); phase=progress(state,phase);cost+=a['cost']
        if phase!=len(request.goals) or cost!=result.certificate.get('cost'):
            raise ValueError('goal or cost differs')
        final=result.certificate.get('final',{})
        if not final or any(state.get(k)!=v for k,v in final.items()) or not set().union(*request.goals)<=set(final):
            raise ValueError('final state differs')
    elif result.status == 'IMPOSSIBLE':
        keys=result.certificate['keys']; rows=result.certificate['states']
        if len(keys)!=len(set(keys)) or not set().union(*request.goals)<=set(keys):
            raise ValueError('certificate variables incomplete')
        # The recorded variables must be closed under every potentially relevant action.
        relevant=[]
        for a in actions.values():
            if set(a['effects']) & set(keys) and a['id'] not in forbidden:
                if not ({k for k,_,_ in a['pre']}|set(a['effects']))<=set(keys):
                    raise ValueError('certificate omits causal variables')
                relevant.append(a)
        states=set()
        for v,p in rows:
            if len(v)!=len(keys) or type(p) is not int or not 0<=p<len(request.goals):
                raise ValueError('invalid certificate state')
            if any(k not in request.domain['variables'] or x not in request.domain['variables'][k] for k,x in zip(keys,v)):
                raise ValueError('invalid state value')
            states.add((tuple(v),p))
        start=tuple(request.initial[k] for k in keys)
        if (start,progress(request.initial,0)) not in states or len(states)!=len(rows):
            raise ValueError('missing initial or duplicate state')
        for values,phase in states:
            s=dict(zip(keys,values))
            if progress(s,phase)!=phase:
                raise ValueError('unprocessed goal in certificate')
            for a in relevant:
                try:nxt=apply(s,a)
                except ValueError:continue
                np=progress(nxt,phase)
                if (tuple(nxt[k] for k in keys),np) not in states:
                    raise ValueError('reachable set is not closed')
    elif result.status == 'INSUFFICIENT_INFORMATION':
        missing=result.detail.get('missing',[])
        if not missing or any(k in request.initial or k not in request.domain['variables'] for k in missing):
            raise ValueError('invalid missing facts')
    elif result.status != 'BUDGET_EXHAUSTED':
        raise ValueError('unknown reasoning outcome')
    return True
