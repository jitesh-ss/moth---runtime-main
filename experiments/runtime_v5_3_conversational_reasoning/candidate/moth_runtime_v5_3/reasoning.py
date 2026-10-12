"""Pure bounded finite-state composition. No persistence or external actions."""
from dataclasses import dataclass, field, asdict
from heapq import heappop, heappush
from .legacy.canonical import digest

LIMITS = dict(message_tokens=512, clauses=256, facts=4096, actions=8192, depth=32, expansions=100000)

@dataclass(frozen=True)
class ReasoningRequest:
    domain: dict
    initial: dict
    goals: list
    facts: list = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    prior_results: list = field(default_factory=list)
    bindings: dict = field(default_factory=dict)
    limits: dict = field(default_factory=lambda: dict(LIMITS))

    @property
    def request_hash(self):
        return digest('moth-reasoning-request/5.3', asdict(self))

@dataclass(frozen=True)
class ReasoningResult:
    status: str
    request_hash: str
    plan: tuple = ()
    certificate: dict = field(default_factory=dict)
    detail: dict = field(default_factory=dict)

    def canonical(self):
        value = asdict(self)
        value['plan'] = list(value['plan'])
        return value

def validate_request(request):
    d = request.domain
    if set(d) != {'variables', 'actions'} or not d['variables']:
        raise ValueError('invalid finite domain')
    for k, values in d['variables'].items():
        if not isinstance(k,str) or not values or len(set(values)) != len(values) or not all(isinstance(v,str) for v in values):
            raise ValueError('invalid variable domain')
    ids = set()
    for a in d['actions']:
        if set(a) != {'id','pre','effects','cost'} or a['id'] in ids or type(a['cost']) is not int or a['cost'] <= 0:
            raise ValueError('invalid action')
        ids.add(a['id'])
        for k, op, v in a['pre']:
            if k not in d['variables'] or v not in d['variables'][k] or op not in ('eq','ne'):
                raise ValueError('invalid precondition')
        if not a['effects'] or any(k not in d['variables'] or v not in d['variables'][k] for k,v in a['effects'].items()):
            raise ValueError('invalid effect')
    for k,v in request.initial.items():
        if k not in d['variables'] or v not in d['variables'][k]:
            raise ValueError('invalid initial value')
    for goal in request.goals:
        if not goal or any(k not in d['variables'] or v not in d['variables'][k] for k,v in goal.items()):
            raise ValueError('invalid goal')
    if not request.goals:
        raise ValueError('missing goal')
    if set(request.constraints) - {'forbidden_actions'}:
        raise ValueError('unsupported hard constraint')
    if not set(request.constraints.get('forbidden_actions',[])) <= ids:
        raise ValueError('unknown forbidden action')
    if set(request.limits) != set(LIMITS) or any(type(v) is not int or not 0 <= v <= LIMITS[k] for k,v in request.limits.items()):
        raise ValueError('invalid computation limits')

def relevant_domain(request):
    """Backward causal closure, including all alternative achievers and side effects."""
    required = {k for goal in request.goals for k in goal}
    chosen = set()
    changed = True
    while changed:
        before = (len(required), len(chosen))
        for i,a in enumerate(request.domain['actions']):
            if set(a['effects']) & required:
                chosen.add(i)
                required.update(k for k,_,_ in a['pre'])
                required.update(a['effects'])
        changed = before != (len(required), len(chosen))
    return sorted(required), sorted((request.domain['actions'][i] for i in chosen
        if request.domain['actions'][i]['id'] not in request.constraints.get('forbidden_actions',[])), key=lambda a:a['id'])

def _advance(state, phase, goals):
    while phase < len(goals) and all(state[k] == v for k,v in goals[phase].items()):
        phase += 1
    return phase

class Kernel53:
    def solve(self, request: ReasoningRequest) -> ReasoningResult:
        validate_request(request)
        identity = request.request_hash
        keys, actions = relevant_domain(request)
        if len(request.facts)>request.limits['facts'] or len(request.domain['actions'])>request.limits['actions']:
            return ReasoningResult('BUDGET_EXHAUSTED',identity,detail={'reason':'input_limit'})
        missing = sorted(set(keys)-set(request.initial))
        if missing:
            return ReasoningResult('INSUFFICIENT_INFORMATION',identity,detail={'missing':missing})
        initial = tuple(request.initial[k] for k in keys)
        phase = _advance(request.initial,0,request.goals)
        queue = [(0,(),initial,phase)]
        best = {(initial,phase):[(0,0)]}
        reached = set()
        expanded = 0
        cutoff = False
        while queue:
            cost,path,values,phase = heappop(queue)
            state = dict(zip(keys,values))
            if phase == len(request.goals):
                return ReasoningResult('ANSWER',identity,path,{'final':state,'cost':cost}, {'expanded':expanded})
            if expanded >= request.limits['expansions']:
                return ReasoningResult('BUDGET_EXHAUSTED',identity,detail={'reason':'expansions','expanded':expanded})
            expanded += 1
            reached.add((values,phase))
            for a in actions:
                if not all((state[k]==v) if op=='eq' else (state[k]!=v) for k,op,v in a['pre']):
                    continue
                nxt = {**state,**a['effects']}
                nv = tuple(nxt[k] for k in keys)
                np = _advance(nxt,phase,request.goals)
                nc,nd = cost+a['cost'],len(path)+1
                labels = best.get((nv,np),[])
                if any(c<=nc and depth<=nd for c,depth in labels):
                    continue
                if nd > request.limits['depth']:
                    cutoff = True
                    continue
                best[nv,np] = [(c,depth) for c,depth in labels if not (nc<=c and nd<=depth)] + [(nc,nd)]
                heappush(queue,(nc,path+(a['id'],),nv,np))
        if cutoff:
            return ReasoningResult('BUDGET_EXHAUSTED',identity,detail={'reason':'depth','expanded':expanded})
        certificate = {'keys':keys,'states':[[list(v),phase] for v,phase in sorted(reached)]}
        return ReasoningResult('IMPOSSIBLE',identity,certificate=certificate,detail={'expanded':expanded})
