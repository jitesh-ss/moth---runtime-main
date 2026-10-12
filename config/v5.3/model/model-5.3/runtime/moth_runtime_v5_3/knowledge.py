"""Immutable factual revisions: assertions are not instruction authority."""
from copy import deepcopy
from .legacy.canonical import digest

def initial_knowledge(source):
    facts=[]
    for variable,value in sorted(source['defaults'].items()):
        fact={'variable':variable,'value':value,'polarity':True,'kind':'foundation_default',
              'source':'foundation','dependencies':[],'active':True,'supersedes':[]}
        fact['id']=digest('moth-fact/5.3',fact);facts.append(fact)
    return {'facts':facts,'focus':[],'pending':None,'last_result':None}

def active_facts(knowledge):
    active={f['id']:f for f in knowledge['facts'] if f['active']}
    while True:
        invalid=[k for k,f in active.items() if any(d not in active for d in f['dependencies'])]
        if not invalid:return list(active.values())
        for k in invalid:del active[k]

def apply_interpretation(knowledge, interpretation, message_id):
    next=deepcopy(knowledge)
    if interpretation.pending:
        next['pending']=interpretation.pending
        return next,'CLARIFICATION_REQUIRED',interpretation.pending
    clauses=interpretation.clauses
    if len(clauses)==1 and clauses[0]['kind']=='cancel':
        next['pending']=None
        return next,'ACKNOWLEDGED',{'changed':[]}
    if len(clauses)==1 and clauses[0]['kind']=='confirm':
        pending=knowledge['pending']
        if not pending or pending.get('kind')!='conflict':
            return next,'CLARIFICATION_REQUIRED',{'reason':'There is no factual correction awaiting confirmation.','choices':[]}
        clauses=deepcopy(pending['clauses'])
        for c in clauses:c['correction']=True
    changed=[]
    for c in clauses:
        if 'variable' not in c:continue
        variable=c['variable'];value=c['value'];polarity=c['polarity']
        relevant=[f for f in active_facts(next) if f['variable']==variable]
        conflicts=[f for f in relevant if (f['polarity'] and polarity and f['value']!=value) or (f['value']==value and f['polarity']!=polarity)]
        if conflicts and not c['correction'] and not c['retract'] and any(f['kind']!='foundation_default' for f in conflicts):
            pending={'kind':'conflict','clauses':clauses,'reason':f'This conflicts with an earlier statement about {variable}. Should I use the new value?','choices':[]}
            unchanged=deepcopy(knowledge);unchanged['pending']=pending
            return unchanged,'CLARIFICATION_REQUIRED',pending
        supersedes=[]
        for f in relevant:
            if (c['retract'] and f['value']==value and f['polarity']==polarity) or (not c['retract'] and (f in conflicts or (f['value']==value and f['polarity']==polarity))):
                next['facts'][next['facts'].index(f)]['active']=False;supersedes.append(f['id'])
        if not c['retract']:
            fact={'variable':variable,'value':value,'polarity':polarity,'kind':'asserted',
                  'source':message_id,'dependencies':[],'active':True,'supersedes':supersedes}
            fact['id']=digest('moth-fact/5.3',fact);next['facts'].append(fact);changed.append(fact['id'])
        else:changed.extend(supersedes)
    valid={f['id'] for f in active_facts(next)}
    for f in next['facts']:
        if f['active'] and f['id'] not in valid:f['active']=False
    next['pending']=None
    if interpretation.entities:next['focus']=interpretation.entities
    return next,'ACKNOWLEDGED',{'changed':changed}

def state_from(knowledge):
    return {f['variable']:f['value'] for f in active_facts(knowledge) if f['polarity']}
