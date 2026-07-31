# examples/

Runnable, end-to-end scripts demonstrating the framework: load a CSV, run a
factor through the pipeline, inspect the validated result and the tracked
experiment it produced. Each example is small, self-contained (it generates
its own synthetic input data — no external files to keep in sync), and
runnable with no configuration beyond what's in the script itself:

```
python examples/moving_average.py
python examples/momentum.py
python examples/volatility.py
python examples/z_score.py
python examples/mean_reversion.py
```

Every model implemented in `src/modelforge/models/` has a corresponding
example here — an example without a real model behind it would just be a
mockup, which isn't in keeping with this project's validation philosophy.
