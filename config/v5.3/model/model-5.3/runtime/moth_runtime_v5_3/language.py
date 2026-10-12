"""Compiled finite-domain English grounding with explicit reference ambiguity."""
from dataclasses import dataclass, asdict
import re
from .legacy.canonical import digest

@dataclass(frozen=True)
class MessageInterpretation:
    message: str
    clauses: list
    entities: list
    evidence: list
    pending: dict | None = None

    def canonical(self):return asdict(self)

class Clarify(ValueError):
    def __init__(self,reason,choices=()):
        self.reason=reason;self.choices=list(choices)
        super().__init__(reason)

class Grounder:
    def __init__(self, source):
        self.source=source
        self.frames=[(f,re.compile(f['pattern'],re.I)) for f in source['frames']]
        self.aliases={}
        for entity,info in source['entities'].items():
            for alias in [entity,*info['aliases']]:
                self.aliases.setdefault(alias.casefold(),[]).append(entity)

    def entity(self,raw,focus,expected=None):
        text=raw.strip().casefold()
        exact=self.aliases.get(text,[])
        if exact:
            choices=exact
        elif text in {'it','that','there','the package','that package','the parcel','the robot','that robot'}:
            typ=expected or ('package' if 'package' in text or 'parcel' in text else 'robot' if 'robot' in text else None)
            choices=[x for x in focus if typ is None or self.source['entities'][x]['type']==typ]
            if not choices:
                choices=[x for x,info in self.source['entities'].items() if info['type']==typ]
        else:
            raise Clarify('I do not recognize '+raw)
        choices=sorted(set(x for x in choices if expected is None or self.source['entities'][x]['type']==expected))
        if len(choices)!=1:raise Clarify('Which entity do you mean?',choices)
        return choices[0]

    def interpret(self,message,focus=(),pending=None):
        original=message.strip();text=original.casefold().replace('’',"'")
        if not text or len(text.split())>self.source['limits']['message_tokens']:
            return MessageInterpretation(original,[],[],[],{'kind':'limit','reason':'Message is empty or exceeds the token limit.','choices':[]})
        if pending and pending.get('kind')=='conflict' and text.strip('.?!') in {'yes','yes that is correct','use the new value'}:
            from copy import deepcopy
            clauses=deepcopy(pending['clauses'])
            for clause in clauses:clause['correction']=True
            return MessageInterpretation(original,clauses,[c['entity'] for c in clauses if 'entity' in c],
                [{'confirmation':True,'source_clauses':pending['clauses']}])
        if pending and pending.get('kind')=='reference' and text.strip('.?!') in self.aliases:
            selected=self.entity(text.strip('.?!'),focus)
            if pending.get('choices') and selected not in pending['choices']:
                return MessageInterpretation(original,[],[],[],pending)
            interpreted=self.interpret(pending['message'],[selected])
            return MessageInterpretation(original,interpreted.clauses,interpreted.entities,
                [{'clarifies':pending['message'],'selection':selected},*interpreted.evidence],interpreted.pending)
        # Sentence/clause boundaries are explicit; no unknown clause can be discarded.
        pieces=list(re.finditer(r'[^.;!?]+(?:[!?])?',text))
        segments=[]
        for piece in pieces:
            for segment in re.finditer(r'.+?(?=\s+(?:and then|then|and)\s+|$)',piece.group()):
                s=segment.group().strip()
                s=re.sub(r'^(?:and then|then|and)\s+','',s)
                if s:segments.append((s.strip('!? '),piece.start()+segment.start(),bool(re.search(r'\bthen\b',segment.group()))))
        if len(segments)>self.source['limits']['clauses']:
            return MessageInterpretation(original,[],[],[],{'reason':'Too many clauses.','choices':[]})
        clauses=[];entities=[];evidence=[];current_focus=list(focus)
        try:
            for clause,start,_ in segments:
                correction=bool(re.match(r'^(?:actually[, ]+|correction[: ,]+)',clause))
                retract=bool(re.match(r'^(?:forget that |retract |forget )',clause))
                body=re.sub(r'^(?:actually[, ]+|correction[: ,]+|forget that |retract |forget )','',clause)
                matches=[(f,m) for f,pattern in self.frames if (m:=pattern.fullmatch(body))]
                if len(matches)!=1:raise Clarify('Please rephrase this clause: '+clause)
                frame,m=matches[0];kind=frame['id'];g=m.groupdict();c={'kind':kind,'correction':correction,'retract':retract}
                if 'entity' in g:
                    expected='room' if kind=='locked' else 'robot' if kind in ('battery','key') else None
                    entity=self.entity(g['entity'],current_focus,expected)
                    c['entity']=entity;entities.append(entity)
                    if 'value' in g:
                        val=g['value']
                        if kind in ('location','deliver','plan'):val=self.entity(val,current_focus,'room')
                        if kind=='locked':val='yes' if val=='locked' else 'no'
                        c['value']=val
                    if kind=='key':c['value']='no' if g['neg']=='does not have' else 'yes'
                    if kind in ('location','battery','key','locked'):
                        c['variable']=entity+'.'+frame['predicate']
                        c['polarity']=not bool(g.get('neg')) if kind!='key' else True
                        if c['variable'] not in self.source['domain']['variables'] or c['value'] not in self.source['domain']['variables'][c['variable']]:
                            raise Clarify('That property is not supported for '+entity)
                    current_focus=[entity]
                clauses.append(c);evidence.append({'frame':kind,'span':[start,start+len(clause)]})
            # Conjoined goals are simultaneous unless the user explicitly says then.
            if sum(c['kind'] in ('deliver','plan') for c in clauses)>1:
                for c in clauses:c['ordered']=bool(re.search(r'\bthen\b',text))
            return MessageInterpretation(original,clauses,sorted(set(entities)) if ' and ' in text else current_focus,evidence)
        except Clarify as exc:
            return MessageInterpretation(original,[],[],evidence,{'kind':'reference' if exc.choices else 'unsupported','message':original,'reason':exc.reason,'choices':exc.choices})


def validate_source(source):
    from .reasoning import ReasoningRequest, validate_request, LIMITS
    if set(source) != {'schema','entities','domain','defaults','frames','limits'} or source['schema']!='moth-chat-source/5.3':
        raise ValueError('invalid conversational source')
    if source['limits']!=LIMITS:
        raise ValueError('release limits differ from the frozen contract')
    if not source['entities'] or not source['frames']:
        raise ValueError('empty conversational foundation')
    for entity,record in source['entities'].items():
        if record['type'] not in {'room','robot','package'} or not record['aliases']:
            raise ValueError('invalid entity declaration')
    if len(source['domain']['actions'])>LIMITS['actions']:
        raise ValueError('too many grounded actions')
    if set(source['defaults'])!=set(source['domain']['variables']):
        raise ValueError('initial world defaults are incomplete')
    key=next(iter(source['defaults']))
    validate_request(ReasoningRequest(source['domain'],source['defaults'],[{key:source['defaults'][key]}]))
    if len({f['id'] for f in source['frames']})!=len(source['frames']):
        raise ValueError('duplicate language frame')
    Grounder(source)
