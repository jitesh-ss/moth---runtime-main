"""Pure preparation and verified conversational realization."""
from copy import deepcopy
from dataclasses import asdict
from .knowledge import apply_interpretation, active_facts, state_from
from .language import Grounder
from .reasoning import Kernel53, ReasoningRequest, ReasoningResult, relevant_domain
from .checker import verify
from .legacy.canonical import canonical_bytes, digest

def prepare(source, knowledge, message, message_id, bindings):
    interpretation=Grounder(source).interpret(message,knowledge['focus'],knowledge['pending'])
    next,status,detail=apply_interpretation(knowledge,interpretation,message_id)
    result={'status':status,'detail':detail,'interpretation':interpretation.canonical(),'request':None,'reasoning':None}
    if interpretation.pending and interpretation.pending.get('kind')=='limit':
        return deepcopy(knowledge),{**result,'status':'BUDGET_EXHAUSTED'}
    if status=='CLARIFICATION_REQUIRED':return next,result
    if len(active_facts(next))>source['limits']['facts']:
        return deepcopy(knowledge),{**result,'status':'BUDGET_EXHAUSTED','detail':{'reason':'facts'}}
    goals=[]
    for c in interpretation.clauses:
        if c['kind'] in ('deliver','plan'):
            goals.append({c['entity']+'.location':c['value']})
    if goals:
        if len(goals)>1 and not any(c.get('ordered') for c in interpretation.clauses):
            merged={}
            for goal in goals:
                for k,v in goal.items():
                    if k in merged and merged[k]!=v:
                        pending={'kind':'goals','reason':'The simultaneous goals conflict; specify an order with then.','choices':[]}
                        prior=deepcopy(knowledge);prior['pending']=pending
                        return prior,{**result,'status':'CLARIFICATION_REQUIRED','detail':pending}
                    merged[k]=v
            goals=[merged]
        facts=active_facts(next)
        request=ReasoningRequest(source['domain'],state_from(next),goals,facts=facts,
            prior_results=[knowledge['last_result']] if knowledge['last_result'] else [],bindings=bindings,limits=source['limits'])
        keys,_=relevant_domain(request)
        request=ReasoningRequest(request.domain,{k:v for k,v in request.initial.items() if k in keys},goals,
            facts=[f for f in facts if f['variable'] in keys],prior_results=request.prior_results,bindings=bindings,limits=source['limits'])
        result['request']=asdict(request)
    else:
        questions=[c for c in interpretation.clauses if c['kind']=='where']
        if questions:
            answers=[];missing=[]
            for q in questions:
                variable=q['entity']+'.location'
                facts=[f for f in active_facts(next) if f['variable']==variable and f['polarity']]
                if facts:answers.append({'entity':q['entity'],'value':facts[0]['value'],'fact_id':facts[0]['id'],'source':facts[0]['source']})
                else:missing.append(variable)
            result.update(status='INSUFFICIENT_INFORMATION' if missing else 'ANSWER',detail={'answers':answers,'missing':missing})
        follow=[c for c in interpretation.clauses if c['kind'] in ('why','repeat')]
        if follow:
            previous=knowledge['last_result']
            result.update(status='ANSWER' if previous else 'INSUFFICIENT_INFORMATION',detail={'previous':previous,'reason':'previous_result'})
    return next,result

def solve(prepared):
    result=deepcopy(prepared)
    if result['request']:
        request=ReasoningRequest(**result['request'])
        reasoning=Kernel53().solve(request)
        verify(request,reasoning)
        result.update(status=reasoning.status,reasoning=reasoning.canonical(),detail=reasoning.detail)
    return result

def action_text(identifier):
    import re
    words=identifier.split()
    def name(value):
        return re.sub(r'^(robot|room)([0-9]+)$',r'\1 \2',value).replace('packagea','package A').replace('packageb','package B')
    if words[0]=='move':return f'Move {name(words[1])} from {name(words[2])} to {name(words[3])}.'
    if words[:2]==['pick','up']:return f'Pick up {name(words[2])} with {name(words[3])} in {name(words[4])}.'
    if words[0]=='drop':return f'Drop {name(words[1])} with {name(words[2])} in {name(words[3])}.'
    if words[0]=='unlock':return f'Unlock the door to {name(words[1])} with {name(words[2])} from {name(words[3])}.'
    if words[0]=='recharge':return f'Recharge {name(words[1])}.'
    raise ValueError('unsupported action surface')

def recover_plan(text):
    import re
    return re.findall(r'^\d+\. (.+)$',text,re.M)

def render(result, mode='concise'):
    """Each rendered answer carries a recoverable typed payload in its surface receipt."""
    status=result['status'];detail=result['detail']
    if status=='CLARIFICATION_REQUIRED':
        text=detail['reason']
        if detail.get('choices'):text+=' Options: '+', '.join(detail['choices'])+'.'
    elif status=='ACKNOWLEDGED':text='Noted. I updated the conversation facts.' if detail.get('changed') else 'Understood.'
    elif result.get('reasoning'):
        r=result['reasoning']
        if status=='ANSWER':
            text='Using the recorded facts and configured world defaults, this plan reaches the goal:\n'
            text+=('\n'.join(f'{i}. {action_text(a)}' for i,a in enumerate(r['plan'],1)) if r['plan'] else 'The goal is already satisfied.')
            text+='\nThis is a proposed plan; no actions have been executed.'
        elif status=='IMPOSSIBLE':text='No plan reaches the goal in this finite world. All reachable states were checked.'
        elif status=='INSUFFICIENT_INFORMATION':text='I need the following facts: '+', '.join(detail['missing'])+'.'
        else:text='I reached the computation limit before resolving this request. This does not prove it is impossible.'
    elif 'answers' in detail:
        text=' '.join(f"{a['entity']} is in {a['value']}." for a in detail['answers'])
        if detail.get('missing'):text+=' I do not know: '+', '.join(detail['missing'])+'.'
    elif detail.get('previous'):
        previous=detail['previous']
        text='The previous result was '+previous['status']+'. '+previous['response']
    elif status=='INSUFFICIENT_INFORMATION':text='There is no previous verified answer to refer to.'
    elif status=='BUDGET_EXHAUSTED':text='The request exceeds the configured resource limit.'
    else:text=detail.get('reason',status)
    if mode in {'structured','json_compact','json_readable'}:
        import json
        text=json.dumps({'status':status,'detail':detail,'reasoning':result.get('reasoning')},sort_keys=True,indent=2 if mode=='json_readable' else None)
    if mode in {'python_literal_compact','python_literal_readable','python_function'}:
        from .surface import _render, recover_surface_value
        material={'status':status,'detail':detail,'reasoning':result.get('reasoning')}
        text=_render(material,mode)
        if canonical_bytes(recover_surface_value(text,mode))!=canonical_bytes(material):
            raise ValueError('structured chat surface changed meaning')
    return text

def surface(result,mode):
    text=render(result,mode)
    # Reconstruct from the typed material, not from a second search.
    if result.get('reasoning') and result['status']=='ANSWER' and mode not in {'structured','json_compact','json_readable','python_literal_compact','python_literal_readable','python_function'}:
        if recover_plan(text)!=[action_text(a) for a in result['reasoning']['plan']]:
            raise ValueError('plan surface did not recover the selected actions')
    material={'status':result['status'],'detail':result['detail'],'reasoning':result.get('reasoning')}
    return {'text':text,'mode':mode,'material':material,'material_hash':digest('moth-chat-material/5.3',material),
            'text_hash':digest('moth-chat-text/5.3',text)}

def verify_surface(artifact,result):
    if canonical_bytes(artifact)!=canonical_bytes(surface(result,artifact['mode'])):
        raise ValueError('chat surface does not reconstruct from verified material')
