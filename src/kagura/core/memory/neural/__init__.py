"""Neural Memory Network implementation.

This module implements a Hebbian learning-based neural memory system
that enables adaptive association learning through user interactions.

Key Components:
- Hebbian Learning: "Cells that fire together, wire together"
- Activation Spreading: Graph-based associative retrieval
- Co-Activation Tracking: Automatic association discovery
- Unified Scoring: Semantic + Temporal + Graph + Trust signals
- Forgetting Mechanism: Decay and selective pruning

References:
- Hopfield Networks is All You Need (arXiv:2008.02217)
- kNN-LM (arXiv:1911.00172)
- RETRO (arXiv:2112.04426)
- Memorizing Transformers (arXiv:2203.08913)
"""

from .activation import ActivationSpreader
from .co_activation import CoActivationTracker
from .config import NeuralMemoryConfig
from .decay import DecayManager
from .engine import NeuralMemoryEngine
from .hebbian import HebbianLearner
from .models import (
    ActivationState,
    CoActivationRecord,
    HebbianUpdate,
    MemoryKind,
    NeuralMemoryNode,
    RecallResult,
    SourceKind,
)
from .scoring import UnifiedScorer

__all__ = [
    # Main components
    "NeuralMemoryConfig",
    "NeuralMemoryEngine",
    # Subcomponents
    "ActivationSpreader",
    "CoActivationTracker",
    "DecayManager",
    "HebbianLearner",
    "UnifiedScorer",
    # Models
    "NeuralMemoryNode",
    "ActivationState",
    "CoActivationRecord",
    "HebbianUpdate",
    "RecallResult",
    "MemoryKind",
    "SourceKind",
]

__version__ = "0.1.0"
