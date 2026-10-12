# Runtime 5.0 adversarial semantic-invariance conclusion 001

## Verdict

`ADVERSARIAL_SEMANTIC_INVARIANCE_CONFIRMED`

Runtime 5.0 passed the frozen hard test on a separate temporary store and World
bundle. The campaign did not modify the Runtime 5.0 implementation,
configuration, architecture lock, launcher, or production store.

## Decisive results

| Gate | Result |
|---|---:|
| Frozen cases | 50/50 passed |
| Equivalent novel compositions accepted | 40/40 |
| Valid meaning contrasts correctly changed | 3/3 |
| Expected ambiguity/unsupported refusals | 7/7 |
| Unsafe acceptances | 0 |
| Delivery semantic graph count | 1 |
| Deployment semantic graph count | 1 |
| Shared Main program count | 1 |
| Encoder-free byte-exact replays | 50/50 |
| Semantic-trace tampering detected | yes |
| Execution / dispatch | 0 / 0 |
| Protected hash changes | 0 |

All 20 delivery paraphrases and all 20 deployment paraphrases converged to one
semantic graph within their domain despite recombined aliases, relation frames,
object names, intent wording, clause order, and bounded singular pronouns. The
two domains used one identical Main program in one Main World with hash
`4d9792bd04718073f2c3f0af127f1e05fa99922d901f3a103d2b04a638d82198`.

Three valid minimal contrasts changed polarity or role assignment and produced
the specified different semantic graph and factor result. Seven unsafe or
unsupported contrasts covering ambiguous reference, conflicting facts,
incomplete facts, unknown entity, modality, time/quantity, and unsupported
intent refused with their frozen codes.

Every case was persisted in the disposable store and replayed byte-for-byte
without an encoder. Altering one canonical fact in a stored semantic trace was
rejected by verification.

## Interpretation

This is strong evidence that Runtime 5.0 language fidelity is internal to its
compiled Input settlement rather than a prompt-string alias trick: different
compiled surface compositions reach the same graph and the unchanged Main
factor kernel, while nearby meanings do not collapse together.

The boundary remains important. Every accepted word, frame, entity, intent,
and projection was compiled beforehand. This campaign does not establish
arbitrary unseen vocabulary, unrestricted English, open-world reasoning, or
general linguistic inference outside the frozen contract.
