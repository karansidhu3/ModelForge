# Project Philosophy

## The problem this project is a response to

Quantitative research code has a well-earned reputation for being fragile:
notebooks with hidden state, results that depend on the order cells were run in,
"it worked when I ran it in March" bugs, and implementations that were never
checked against a known answer. None of that is a math problem. It's an
engineering problem — the kind that shows up whenever research code is expected
to become production code without anyone deciding, on purpose, what standard it
has to meet along the way.

ModelForge is a small, deliberately narrow answer to that problem: take a few
simple, well-published models, and build the discipline around them that a
research-engineering team would build around anything going into production —
interfaces, validation, tests, tracked experiments, documentation — before
worrying about whether the models themselves are interesting.

## Why the models are intentionally simple

Moving average, momentum, volatility, z-score, mean reversion. None of these
are novel, and that's the point. If the framework can't make a five-line
formula trustworthy — provably correct against known inputs, reproducible run
to run, clearly documented — it has no business being trusted with anything
more complex. Sophistication in the model is not the goal here; sophistication
in the *scaffolding around* the model is.

## What "engineering discipline" means concretely, here

- A model isn't done when it runs. It's done when it's been checked against a
  known answer, tested for the edge cases that break naive implementations,
  and documented well enough that someone else could verify it without reading
  the code.
- A result isn't trusted because it "looks reasonable." It's trusted because
  the validation framework checked it against explicit criteria.
- A run isn't reproducible because "it should be." It's reproducible because
  its config and commit hash are recorded and running them again produces the
  same output.

## Why this matters for the kind of work it's meant to demonstrate

A research paper's model, translated directly into a notebook, tells you the
author understands the math. Translating that same model into something with a
stable interface, a validation layer, a test suite, and reproducible tracked
runs tells you something different: that the author understands how research
becomes software other people can build on. That gap — between "I can
implement the formula" and "I can build the system that makes the formula
trustworthy at scale" — is what this project exists to practice.

## What success looks like

Not a profitable model. Not a clever model. A repository where:

- Every model's correctness can be verified by someone who didn't write it.
- Every result can be reproduced exactly from its recorded config.
- Adding model six requires touching nothing that models one through five
  depend on.
- The documentation explains decisions well enough that six months from now,
  the reasoning isn't lost.
