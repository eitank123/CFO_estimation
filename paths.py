"""
Where every file of the project lives (paths are relative to this folder, so scripts work from any cwd):

    models/     trained networks (.pth)
    results/    simulation results and caches (.npy, .npz)
    logs/       run logs, Run:ai job output, progress files (.log, .out, .progress)
    jobs/       Run:ai job scripts (.sh)
    docs/       papers / references
    plots/<kind>/  figures, one folder per kind (see PLOT_KINDS)

The Python code, README.md and progress.txt stay in the project root.

A separate study (environment variable CFO_STUDY, e.g. "est256") keeps ALL its outputs in <study>/models,
<study>/results, <study>/logs and <study>/plots/<kind>. Reading a model falls back to the main models/ folder,
so a study can start from the main trained networks; results, logs and plots never mix.
"""

import os

ROOT = os.path.dirname(os.path.abspath(__file__))
STUDY = os.environ.get("CFO_STUDY", "")
BASE = os.path.join(ROOT, STUDY) if STUDY else ROOT
MAIN_MODELS = os.path.join(ROOT, "models")
MODELS, RESULTS, LOGS, PLOTS = (os.path.join(BASE, d) for d in ("models", "results", "logs", "plots"))
JOBS, DOCS = os.path.join(ROOT, "jobs"), os.path.join(ROOT, "docs")

# first match wins: (folder, substrings of the file name)
PLOT_KINDS = [
    ("adaptive_rate", ("adaptive",)),
    ("operating_points", ("operating_points",)),
    ("complexity", ("complexity",)),
    ("bler", ("bler",)),
    ("outage", ("outage",)),
    ("training", ("training", "loss_")),
    ("histograms", ("histogram",)),
    ("mse", ("mse", "crb", "accuracy", "cfo_performance")),
    ("ber", ("ber",)),
]


def _in(folder, name):
    if os.path.dirname(name):                 # an explicit path is kept as given
        return name
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, name)


def model(name):
    if STUDY and not os.path.dirname(name) and not os.path.exists(os.path.join(MODELS, name)) \
            and os.path.exists(os.path.join(MAIN_MODELS, name)):
        return os.path.join(MAIN_MODELS, name)           # a main model, read by the study
    return _in(MODELS, name)


def result(name):
    return _in(RESULTS, name)


def log(name):
    return _in(LOGS, name)


def plot_kind(name):
    low = os.path.basename(name).lower()
    return next((k for k, keys in PLOT_KINDS if any(s in low for s in keys)), "other")


def plot(name):
    """plots/<kind>/<name>, the kind from the file name (bler, ber, mse, outage, training, ...)."""
    return _in(os.path.join(PLOTS, plot_kind(name)), name)
