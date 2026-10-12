# Runtime 5.0 Product Contract

Runtime 5.0 lets an operator compile a bounded language once and then submit
different phrasings that settle to the same internal meaning. It retains the
closed-world guarantees and reasoning kernel of Runtime 4.9.

It is selected explicitly with `moth --runtime 5.0`. It ships with an empty
independent store, accepts existing 4.9 controlled prompts, and refuses prose
that cannot be mapped uniquely through a compiled semantic contract.

The product does not promise arbitrary English, new reasoning operations,
tools, execution, planning, learning, or generative Surface behavior.
