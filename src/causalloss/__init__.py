"""CausalLoss-Fin: attributing financial agent loss to decisions and to faults.

A causal layer over FinalityBench (P1).  Existing counterfactual attribution
for agent failures intervenes on the agent's own steps; when the environment is
itself a causal agent -- messages dropped, delayed, duplicated -- an agent-only
method has no variable to blame but the agent.  This package intervenes on both
and splits responsibility in money.
"""

from ._p1 import ensure_p1, p1_provenance  # noqa: F401

__version__ = "1.0.3"
