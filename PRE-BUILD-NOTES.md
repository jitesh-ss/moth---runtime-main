# Moth Pre-Build Notes

**Purpose:** Read this document before building, qualifying, or sealing the
final deployment model.

This is the shared record for qualified findings that affect the final build
without necessarily changing Moth's reasoning mechanism. Add future findings as
dated entries, preserve immutable experimental evidence, and always distinguish
a proven experimental mechanism from production promotion.

## Document rules

- Add new findings as dated entries; do not overwrite earlier evidence.
- State whether each finding changes reasoning, compiled instructions, fields,
  Surface behavior, storage, or deployment only.
- Link the frozen experiment, conclusion, and result manifest.
- Record exact qualification gates and outcomes.
- State clearly whether the mechanism is experimental, qualified, promoted, or
  sealed.

## 2026-09-02 — Runtime 5.0 compiled language fidelity

### Change classification

This work is a **compiled instruction and language-field change**, not a Main
reasoning mechanism change.

It does not modify:

- Main factor settlement or allowed-tuple propagation.
- Surface semantic preservation.
- Planning, tools, execution, dispatch, search, or learning.
- Closed-world membership or the meaning of existing entities and relations.
- BGE thresholds or the rule that vectors may only retrieve typed candidates.

The change belongs in Input World semantic compilation and settlement.

### Architectural finding

Language fidelity inside a closed field requires compiling both:

1. The meanings, entities, relations, roles, intents, and constraints.
2. Reusable instructions for identifying and composing their linguistic forms.

The qualified experimental field included:

- Typed entity and capability descriptions.
- Typed relation-identification rules.
- Subject inheritance across bounded coordination.
- Singular reference resolution.
- Compositional intent identification.
- Polarity, modality, time, quantity, role, and direction enforcement.
- Typed grammatical operators such as optional determiners.

Equivalent language then settles to the same canonical facts instead of
requiring every complete prompt sentence to be compiled separately.

### Required typed determiner rule

The final field needs this reusable grammatical operator:

```text
CAPABILITY_NOUN_PHRASE :=
    DETERMINER? + COMPILED_CAPABILITY_SURFACE

DETERMINER := a | an | the
```

Requirements:

- Apply only to compiled typed capabilities and explicitly permitted roles.
- Permit at most one determiner prefix.
- Give the determiner no semantic contribution.
- Preserve the capability ID and role exactly.
- Record the consumed determiner and rule ID in settlement evidence.
- Treat surfaces already containing a determiner as exact-only.
- Never implement this as unrestricted stop-word removal.

Examples that must converge:

```text
delivery deadline      == the delivery deadline
delivery authorization == the delivery authorization
refrigeration          == the refrigeration
```

Examples that must refuse:

```text
the the delivery deadline
delivery the deadline
the unknown deadline
the backup carrier used as a RESOURCE
```

### Qualification evidence

The first sealed blind compositional campaign exposed the missing determiner
operator without changing its field or prompts:

```text
blind equivalents:       8/12 correct
semantic contrasts:      6/6 correct
unsafe refusals:         10/10 correct
unsafe acceptances:      0
```

After compiling the typed determiner operator into a new sealed field, a fresh
blind campaign produced:

```text
previous failures repaired:       4/4
base-field control accepted:      0/12
extended-field equivalents:      12/12
unique equivalent graphs:         1
meaning-changing contrasts:       6/6 with 6 distinct graphs
unsafe/unsupported refusals:      10/10
unsafe acceptances:               0
determiner causal ablation:       passed
encoder-free nested replay:       32/32 byte-exact
network/execution/dispatch:       0
```

The experiment recorded 82 causal uses of the determiner rule. Removing the
rule made its dependent prompt refuse again.

Evidence:

- [Initial blind closure conclusion](experiments/runtime_v5_0_blind_compositional_closure/reports/CONCLUSION-001.md)
- [Corrective typed-determiner conclusion](experiments/runtime_v5_0_typed_determiner_closure/reports/CONCLUSION-001.md)
- [Corrective result manifest](experiments/runtime_v5_0_typed_determiner_closure/reports/RESULT-001.json)

### Supported architectural claim

The evidence supports this bounded claim:

> Inside a closed field, when meanings and their reusable lexical,
> relational, referential, coordination, intent, and grammatical identification
> rules are compiled, novel compositions of those defined elements settle to
> the same canonical internal meaning while semantic contrasts remain distinct
> and unsupported language safely refuses.

Prompt fidelity is a consequence inside that field: differently phrased prompts
expressing the same compiled meaning produce the same verified semantic graph,
Main result, and Surface value.

Do not broaden this into a claim of unrestricted English or open-world
understanding.

### Final-build integration guidance

When building the deployment candidate:

1. Promote the grammar mechanism through the normal experiment and
   qualification lifecycle; do not copy experimental code directly without a
   promotion record.
2. Keep the mechanism in Input semantic settlement. Main and Surface should
   remain byte-equivalent unless a separately qualified change requires
   otherwise.
3. Compile grammatical operators as typed, content-addressed field assets.
4. Include grammatical rule IDs and transformations in semantic traces, graph
   commitments, archives, handoffs, store verification, and encoder-free replay.
5. Make malformed, duplicated, ambiguous, or role-incompatible grammar rules
   fail compilation atomically.
6. Preserve legacy-envelope precedence and zero semantic cost for exact legacy
   prompts.
7. Keep BGE restricted to typed candidate retrieval. Grammatical rules and hard
   semantic constraints dominate vector similarity.
8. Preserve safe refusal for unknown meanings, unsupported operators, role
   reversal, polarity changes, modality, time, ambiguity, and incomplete facts.
9. Use previous failed prompts as regression evidence, not as the only final
   qualification prompts.
10. Seal the final field before generating a fresh blind qualification set.

### Required pre-deployment gates

- Every equivalent blind prompt converges to one semantic graph and output.
- Every valid semantic contrast produces the expected different graph/result.
- Every ambiguous or unsupported prompt refuses.
- Unsafe semantic acceptance remains zero.
- Causal ablation of each required identification subsystem breaks only its
  dependent cases.
- Repeated compilation and settlement are byte-deterministic.
- Encoder-free replay reconstructs grammatical composition and Runtime results.
- Composition-trace, vector, semantic-trace, handoff, Main, and Surface
  tampering are detected.
- Network, execution, and dispatch remain zero.
- Protected runtime and store hashes change only through an explicit promotion.
- A final architecture lock is created only after the fresh qualification passes.

### Current promotion status

The mechanism is proven in independent Runtime 5.0 experimental instances. It
has **not** been promoted into production Runtime 5.0. The production runtime,
configuration, architecture lock, and store remained unchanged during testing.

## 2026-09-02 — Hierarchical instruction compression and skill fidelity

### Change classification

This work is a **compiled instruction-field, skill-compilation, and policy-
composition change**. It is not a Main reasoning, Surface realization, model,
storage-migration, tool-execution, or deployment change.

The mechanism belongs above language settlement and before task behavior:

```text
ordinary skill source
        |
        v
canonical instruction clauses
        |
        v
typed action / control / policy graph
        |
        v
verified granular skill program
        |
        v
bounded task settlement
```

Language fidelity supplies stable instruction meanings across equivalent
wording. Instruction compression expands those meanings into the granular
prerequisites, policies, ordering, verification, and completion gates required
for behavior.

### Architectural finding

A closed bounded runtime can acquire substantially higher behavioral capability
by compiling reusable instruction fundamentals once and compiling ordinary
agent skills against that base field.

The required hierarchy is:

1. Atomic actions, observable states, resources, inputs, and outputs.
2. Control and policy operators: sequence, dependency, condition, prohibition,
   authority, refusal, completion, bounded repetition, priority, and conflict.
3. Reusable workflow expansions built only from lower-level meanings.
4. Rules that interpret ordinary skill-document clauses into those meanings.
5. Content-addressed compiled skill policies with clause-level provenance.
6. Typed composition of compatible skills with explicit conflict detection.

Each layer must use only qualified meanings from lower layers. A higher-level
instruction is compression over a recoverable granular expansion, not new
unverified authority.

The initial manually authored base field is the root of trust. Incoming skill
documents remain inert source data until compilation, completeness checking,
conflict checking, and policy verification succeed. Skills must never rewrite
the interpreter or introduce undeclared actions merely by naming them.

### Qualification evidence

The frozen isolated experiment compiled one complete ordinary text-patching
skill, one independently worded equivalent, and one composable evidence skill.
It imported no production runtime and executed only in temporary instances.

```text
hierarchy gates:                         6/6 passed
causal hierarchy ablations:              6/6 passed
ordinary skill clauses:                  12
compiled granular policy units:          30
instruction expansion:                   2.5x
complete skill clauses in base field:    0
primary policy versus granular oracle:   exact
paraphrase versus primary policy:        exact
composite versus granular oracle:        exact
behavioral oracle comparisons:           36/36 byte-identical
successful intended changes:             3/3 per policy form
authority requests:                      1/1 per policy form
safe refusals:                           8/8 per policy form
unsafe acceptances:                      0
invalid skill rejections:                4/4
deterministic compilations:              10/10 byte-identical
archived replays:                        36/36 byte-exact
archive tampering:                       detected
network / dispatch / production imports: 0 / 0 / 0
protected production hash changes:       0
```

The primary skill and its paraphrase produced the same canonical policy hash:

```text
e9bd5922821e577a35cb3d968827c5d9c27e0bdf2d45e53ec2959e8c3340a36a
```

Their source and compilation-trace hashes remained different, preserving
provenance while demonstrating invariant instruction meaning.

Evidence:

- [Experiment specification](experiments/runtime_v5_0_instruction_compression/SPEC.md)
- [Frozen fixture commitments](experiments/runtime_v5_0_instruction_compression/fixtures/FREEZE.json)
- [Decisive conclusion](experiments/runtime_v5_0_instruction_compression/reports/CONCLUSION-001.md)
- [Result manifest](experiments/runtime_v5_0_instruction_compression/reports/RESULT-001.json)

### Supported architectural claim

The evidence supports this bounded claim:

> Inside a compiled instruction field, a complete ordinary agent skill can
> identify reusable action, control, policy, workflow, and composition meanings;
> compile into the same canonical policy as a manually granular expansion; and
> perform the same intention on accepted, authority-gated, and refused tasks.

This establishes the mechanism for hierarchical instruction compression. It
does not yet establish that arbitrary third-party skills or unrestricted prose
compile faithfully. The tested field contains one operational skill family and
one evidence extension.

### Future-runtime integration guidance

When adding instruction compression to a future runtime:

1. Implement it first as a versioned experiment and independent store. Do not
   modify or alias an existing sealed runtime.
2. Preserve the phase boundary `language settlement -> instruction compilation
   -> policy verification -> task settlement`. Never execute raw skill text.
3. Compile atomic actions, states, resources, control operators, policies,
   prerequisites, verification, and completion semantics as typed,
   content-addressed field assets.
4. Make workflow macros explicit recoverable expansions. Every expanded action
   must resolve to a lower-layer meaning with no dangling dependency.
5. Derive prerequisite closure from the base field. A compact instruction may
   inherit declared lower-level safety and verification requirements, but the
   compiler must not invent an undeclared prerequisite or permission.
6. Preserve `MUST_NOT` and `ASK_FIRST` constraints through every expansion and
   composition. Preference or convenience rules must never outrank them.
7. Treat missing, ambiguous, contradictory, cyclic, unbounded, or unsupported
   instructions as typed compilation failures.
8. Record source hashes, clause spans, selected interpretation rules, macro
   expansions, inherited prerequisites, policy decisions, and graph hashes in
   the compilation trace.
9. Bind the compiled policy hash into archives, handoffs, receipts, results,
   store verification, and encoder-free replay.
10. Compile a skill once, verify it, and execute only the frozen compiled
    artifact. Do not reinterpret its prose independently on every task.
11. Compose skills only through declared typed composition rules. Detect
    duplicate authority, incompatible effects, priority inversion, conflicting
    completion conditions, and ambiguous ordering before activation.
12. Keep the interpreter immutable during skill compilation. Self-hosting or
    compiler self-description requires a later separate qualification and may
    not be used as the initial root of trust.
13. Keep language retrieval subordinate to hard instruction type, scope,
    policy, and authority constraints. Similar wording cannot create a new
    operation or weaken a refusal boundary.
14. Prefer generic fundamentals and generic composition rules over
    skill-profile-specific templates. Profile-specific rules may be used in
    early experiments but do not establish cross-domain instruction fidelity.
15. Create a new runtime architecture lock only after blind cross-domain skill
    qualification passes.

### Required future qualification gates

- Freeze the base field before selecting or revealing the counted skill panel.
- Use multiple previously unseen skill families from different domains.
- Author and seal granular policy oracles before compiling the ordinary skills.
- Require equivalent skill paraphrases to converge to one canonical policy.
- Require meaningful instruction contrasts to produce different policies.
- Compare compiled and oracle behavior on accepted, authority-gated, refused,
  failed, and recovery cases.
- Require every normative clause either to have explicit provenance in the
  compiled graph or to fail compilation; silent clause dropping is forbidden.
- Require prerequisite closure, termination, cycle, priority, scope, and
  conflict checks to pass before a policy becomes active.
- Require causal ablation of every hierarchy layer and every claimed reusable
  instruction subsystem.
- Test skill injection, interpreter self-modification, undeclared operations,
  prohibition weakening, authority escalation, ambiguous scope, contradictory
  requirements, and unbounded iteration.
- Require zero unsafe behavioral acceptances and zero unauthorized effects.
- Require repeated compilation and execution replay to be deterministic.
- Detect source, compilation-trace, policy-graph, archive, handoff, receipt,
  result, and stored-state tampering.
- Preserve network, dispatch, execution, and tool counts at zero unless a
  separately specified future runtime explicitly qualifies those effects.
- Preserve all prior runtime and production-store hashes throughout the
  experiment.

### Current promotion status

The hierarchical instruction-compression mechanism is **experimentally proven
for one bounded skill family and one typed composition**. It has not been
promoted into Runtime 5.0 or any other production runtime. Cross-domain blind
skill transfer, broader generic instruction semantics, and production
integration remain unqualified future work.

## 2026-09-03 — Output Surface fidelity and bounded LLM-like realization

### Change classification

This work is a **compiled output-instruction field and Surface realization
change**. It is not a Main reasoning, Input semantic settlement, production
storage, tool-authority, or deployment change.

The Surface must receive an already verified semantic result. It may choose how
to express that result, but it must not change the result, add unsupported
knowledge, reinterpret the original prompt, or weaken a Runtime refusal.

The required boundary is:

```text
Input language settlement
        |
        v
verified semantic graph
        |
        v
Main reasoning result
        |
        v
verified semantic output
        |
        v
compiled output skill policy
        |
        v
Surface planning and realization
        |
        v
inverse semantic recovery and format verification
        |
        v
emitted output artifact + replay archive
```

### Architectural finding

LLM-like output fidelity does not require the Surface to perform reasoning a
second time. It requires a compiled field of reusable output fundamentals and
output-specific skills that control discourse, language, size, tone, structure,
serialization, code shape, verification, and completion.

The qualified mechanism compiled ordinary-language skills into granular
policies and applied those policies only after Runtime 5.0 produced a verified
four-field decision. The same semantic decision was expressed as natural prose,
different length bands, formal and conversational tone, multi-section text,
bullets, tables, prose with JSON, action plans, strict JSON, inert Python, and
bounded executable Python.

Meaning and presentation must remain separate:

```text
same verified semantics + different compiled output policies
                           |
                           v
different language and structure, identical recoverable meaning
```

An output is not complete merely because it is fluent or parses. It is complete
only when its material claims can be recovered and shown equal to the verified
Runtime result, its requested layout and size gates pass, and its artifact is
bound to the semantic and policy hashes.

### Required pre-build nodes

The final deployment design needs the following nodes in this order. Each node
must have an explicit typed input, output, failure state, trace, and hash
commitment.

#### Node 1 — Verified semantic-output boundary

Accept only a sealed Runtime output envelope with a supported result kind and
schema. Validate every material field, type, value domain, and cross-field
invariant before Surface work begins.

Requirements:

- Never realize directly from unresolved prompt text.
- Never allow the Surface to repair or reinterpret malformed Main output.
- Refuse unsupported result kinds and inconsistent semantic combinations.
- Preserve the Runtime episode ID, result hash, semantic-output hash, and field
  version through realization and replay.

#### Node 2 — Output-skill compilation

Treat skill documents as inert source until they compile into a complete
granular Surface policy.

The output instruction field must define:

- atomic validation, routing, discourse, lexicalization, formatting,
  verification, binding, and emission actions;
- sequence, dependency, prohibition, refusal, default, and completion operators;
- recoverable workflow macros built only from those atomic actions;
- interpretation rules for ordinary skill language;
- skill profiles with required rules, policies, and completion conditions;
- size signals, exact layout routes, resource limits, and supported formats.

Every normative skill clause must select exactly one declared interpretation or
fail compilation. Missing required clauses, ambiguous clauses, undeclared
actions, self-modification, fact invention, network research, authority
expansion, and prohibition weakening must fail closed.

Equivalent skill wordings should retain different source/trace hashes while
converging to the same policy hash. The policy must also match a frozen granular
oracle before activation.

#### Node 3 — Presentation-route selection

Map the normalized presentation request to exactly one route declared for the
compiled skill profile.

The route selects only presentation behavior, including:

- output family;
- format and layout;
- concise, standard, or detailed size mode;
- formal, conversational, technical, or other compiled tone;
- prose, list, table, mixed, data, or code realization;
- applicable parser, verifier, and resource bounds.

An absent or ambiguous route must refuse. A skill compiled for one family must
not silently handle another family's request.

#### Node 4 — Material-claim ledger

Convert the verified semantic result into an explicit ledger of every fact the
output must communicate. Mark facts as required, optional supporting material,
or prohibited additions.

For the qualified decision result, the required ledger was:

```text
proposed-valid
backup-valid
selected-plan
failure-reason
```

The ledger is the semantic contract between reasoning and language. Size or
style transformations may change wording and ordering, but cannot remove a
required fact or create a fact outside this contract.

#### Node 5 — Discourse and size planning

Build a response plan before lexicalization. The plan determines outcome order,
claim grouping, paragraph or section structure, and the detail permitted by the
selected size band.

Required size behavior:

- Concise output states the decision and minimum supporting facts.
- Standard output gives a direct result and a compact explanation.
- Detailed output expands assessment, evidence, qualification, and next action
  without changing the underlying claims.
- Compression must remove optional explanation before any required fact.
- Expansion may restate or organize verified facts but may not invent evidence.

Size bands require measurable minimum/maximum words, sentences or lines, and
bytes. A request for brevity must not be implemented as unchecked truncation.

#### Node 6 — Lexical and tone realization

Realize each claim through compiled lexical choices and grammatical operators.
Tone changes vocabulary and syntax, not semantics.

The field should support, qualify, and trace transformations such as:

- direct versus explanatory phrasing;
- formal versus conversational register;
- active recommendation versus neutral assessment;
- connective choice and reference resolution across sentences;
- headings, transitions, and outcome-first ordering;
- deterministic capitalization, punctuation, and terminology.

Equivalent output instructions should select the same policy. Meaning-changing
instructions must remain distinct. Unsupported style requests must refuse rather
than falling through to an uncontrolled default.

#### Node 7 — Structural and mixed-format realization

Use format-specific realizers with independent structural verification for:

- natural prose;
- headings and multi-section responses;
- Markdown bullets;
- Markdown tables;
- prose plus machine-readable JSON;
- action plans and ordered steps;
- strict JSON;
- inert Python data;
- bounded executable code.

Mixed responses must expose independently parseable regions. For example, a
prose-plus-JSON response needs a verified natural-language explanation and a JSON
region that parses to the exact Runtime value.

#### Node 8 — Structured-data serialization

JSON and other data formats must use a frozen schema, deterministic field order,
canonical escaping, exact types, and requested compact or readable layout.

Required checks:

- parse with the standard format parser;
- recover exactly the material value;
- reject missing or extra fields;
- reject type changes and non-canonical unsupported values;
- bind the artifact to both semantic-result and policy hashes;
- enforce byte and layout bounds.

#### Node 9 — Code realization and execution boundary

Code output requires a separate capability contract. Parsing source is not proof
of behavioral fidelity.

For bounded Python, require:

- an explicit allowed AST subset;
- named variables, function definitions, signatures, local variables, call
  graph, return paths, and final observable value;
- disallowed imports, attributes, dynamic calls, filesystem access, networking,
  subprocesses, reflection, classes, loops, comprehensions, and exceptions
  unless a later field explicitly qualifies them;
- AST verification before execution;
- hidden behavioral comparison against the verified Runtime value;
- isolated flags, minimal environment, resource limits, timeout, output limits,
  and disposable working directory;
- deterministic replay and cleanup verification.

The qualified local subprocess boundary is not a hardened arbitrary-code
sandbox. General or user-authored code execution requires a separate container
or sandbox qualification before deployment.

#### Node 10 — Inverse semantic recovery

Every output mode needs a verifier capable of recovering its material meaning.
The recovered value must equal the verified Runtime result exactly.

For structured formats, use independent parsers. For bounded natural-language
modes, use a frozen inverse grammar, claim extractor, or uniquely decodable
realization contract. Exact-text matching alone is insufficient evidence for a
future generative Surface.

Reject outputs when recovery is absent, ambiguous, incomplete, inconsistent, or
contains an unsupported proposition.

#### Node 11 — Layout, size, and quality verification

Before emission, verify:

- semantic equality and complete claim coverage;
- zero unsupported additions;
- format parser success;
- requested tone and discourse plan;
- exact structural layout;
- word, line, sentence, and byte bands;
- no template leakage, internal trace leakage, or unrequested metadata;
- code safety and behavioral tests where applicable.

Naturalness is not fully captured by structural checks. A later promotion-grade
qualification should also add a frozen blind human evaluation against a template
baseline and a capable LLM baseline.

#### Node 12 — Artifact binding, archive, and replay

The emitted artifact must commit to:

- Runtime episode and result hashes;
- verified semantic-output hash;
- input and Surface field versions;
- compiled skill policy hash;
- presentation request and selected route;
- output mode, text, metrics, and recovered-value hash;
- execution metadata for executable formats.

Replay must reconstruct the Runtime result encoder-free, revalidate the artifact,
regenerate the output, and produce byte-identical archive bytes. Source, policy,
route, mode, text, claims, metrics, execution result, and archive tampering must
all be detected.

#### Node 13 — Refusal preservation

Runtime refusals bypass Surface realization. The Surface must not convert an
ambiguous, unsupported, unauthorized, or malformed result into a fluent answer.

Required behavior:

```text
Runtime refusal -> byte-identical refusal
                -> no output artifact
                -> no execution
                -> no external effect
```

#### Node 14 — Isolated qualification and promotion

Develop and test new Surface capabilities only in versioned experiments using
fresh temporary stores. Freeze the question, skills, granular oracles, panels,
and protected hashes before the counted run.

Promotion requires a separate qualification record. Do not copy candidate
skills, fields, or realizer code into canonical locations merely because an
experiment passes.

### Qualification evidence

The frozen multi-phase Runtime 5.0 campaign tested seven compiled skill families
and fourteen independently worded source-skill variants.

```text
presentation modes:                   16
realized outputs:                    168
Runtime byte parity:             168/168
natural prose outputs:                48
new rich outputs:                     64
JSON and inert-Python artifacts:      40
executable Python programs:           16
exact inverse recovery, rich phase: 64/64
deterministic compilation trials:     70
adversarial gates:                 92/92
semantic omissions:                    0
unsupported additions:                 0
semantic drift:                        0
unsafe Python accepted:                 0
refusals converted to outputs:          0
production-store accesses:              0
protected hash changes:                  0
```

The new rich-output phase covered compact prose, detailed prose, formal tone,
conversational tone, Markdown bullets, Markdown tables, explanation plus JSON,
and action plans. Every mode preserved all material facts and stayed inside its
frozen layout, word, and byte bands.

Evidence:

- [Mega-campaign specification](experiments/runtime_v5_0_output_fidelity_mega_campaign/SPEC.md)
- [Full decisive report](experiments/runtime_v5_0_output_fidelity_mega_campaign/reports/FULL-REPORT-001.md)
- [Machine result](experiments/runtime_v5_0_output_fidelity_mega_campaign/reports/RESULT-001.json)
- [Output gallery](experiments/runtime_v5_0_output_fidelity_mega_campaign/reports/SAMPLE-GALLERY-001.md)
- [Natural Surface conclusion](experiments/runtime_v5_0_compiled_surface_skill/reports/CONCLUSION-001.md)
- [JSON/Python conclusion](experiments/runtime_v5_0_compiled_json_python_surface/reports/CONCLUSION-001.md)
- [Executable Python conclusion](experiments/runtime_v5_0_compiled_python_function_surface/reports/CONCLUSION-001.md)

### Required final-build field assets

The deployment candidate should not embed one monolithic output prompt. It needs
versioned, content-addressed assets for:

1. Surface atomic actions and states.
2. Output control and policy operators.
3. Discourse and verification workflow macros.
4. Skill interpretation rules with clause provenance.
5. Output-family profiles and route definitions.
6. Material-claim schemas per Runtime result kind.
7. Size signals and measurable size bands.
8. Lexical, grammatical, register, and connective choices.
9. Format-specific layout schemas and parsers.
10. Natural-language inverse recovery or claim-extraction rules.
11. Code AST and execution-capability contracts.
12. Semantic, policy, artifact, execution, and archive hash domains.

All assets must be explicitly versioned. A field change that affects output bytes
requires a new field version and qualification; it must not silently mutate a
sealed Surface contract.

### Required pre-deployment gates

- Multiple independently authored skill families compile to frozen granular
  oracles.
- Equivalent skill paraphrases converge to one policy; meaningful instruction
  contrasts do not.
- Previously unseen semantic/presentation combinations preserve every material
  claim.
- Concise, standard, and detailed responses satisfy both size and semantic
  retention gates.
- Tone changes are observable while recovered semantics remain identical.
- Multi-sentence and multi-section outputs preserve reference and discourse
  consistency.
- Every structured or mixed region parses independently and recovers exact
  values.
- Generated code passes AST, capability, hidden behavioral, resource, cleanup,
  and replay checks.
- Unsupported style, format, schema, or code requests fail closed.
- Runtime refusals remain byte-identical and create no artifact or effect.
- Causal ablation of routing, planning, realization, recovery, size, format,
  safety, and binding nodes breaks their dependent outputs.
- Skill injection, fact invention, self-modification, network research,
  undeclared format, policy weakening, and archive tampering are detected.
- Repeated compilation, realization, execution where allowed, and encoder-free
  replay are deterministic.
- Candidate runs use independent stores and leave every protected runtime and
  production-store hash unchanged.
- Blind human naturalness evaluation, multilingual qualification, multi-turn
  state, uncertainty calibration, citations, long-form generation, and
  open-domain transfer are completed before making claims in those areas.

### Supported architectural claim

The evidence supports this bounded claim:

> Within a compiled closed field, output-specific skills can reduce to verified
> granular Surface policies that transform one verified Runtime result into
> multiple natural, sized, styled, structured, mixed, data, and bounded-code
> representations while preserving exactly recoverable meaning, refusal
> behavior, deterministic replay, and runtime isolation.

Do not broaden this into a claim of unrestricted language generation, arbitrary
code synthesis, general knowledge, persistent conversation, or
human-indistinguishability from an open-domain LLM.

### Current promotion status

The output mechanism is **experimentally proven across seven bounded compiled
skill families and sixteen presentation modes**. It has not been promoted into
Runtime 5.0. Runtime code, canonical configuration, production store,
architecture documentation, and predecessor evidence remained unchanged.

The next permissible step is a new promotion qualification or a separate blind
held-out expansion. The experiment itself must not be treated as the canonical
Surface implementation.

## Future-entry template

Add future entries using this structure:

```markdown
## YYYY-MM-DD — Short title

### Classification
Reasoning change, compiled instruction change, field change, Surface change,
storage change, or deployment-only change.

### Finding
What was learned and why it matters to the final build.

### Evidence
Frozen experiment, result counts, hashes, replay, and safety outcome.

### Final-build guidance
Exactly what must be included, excluded, or preserved.

### Qualification gates
Specific conditions required before promotion or deployment.

### Promotion status
Experimental, qualified, promoted, or sealed.
```
