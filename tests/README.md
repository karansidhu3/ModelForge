# tests/

Mirrors the structure of `src/modelforge/`. See `docs/testing-strategy.md`
for the testing philosophy this suite follows, and `CLAUDE.md` for what's
required of every model's tests before it's considered done.

```
tests/
├── conftest.py    Shared fixtures, including the toy Factor used to
│                  exercise the pipeline without depending on a real model
├── fixtures/      Small, deterministic, reusable CSV fixtures
├── core/          config, factor, pipeline, validation
├── data/          loaders
├── models/        One test module per model in src/modelforge/models/
├── experiments/   tracker, benchmark
└── cli/           the `modelforge` command
```
