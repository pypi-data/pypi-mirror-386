"""
Nthuku-Fast: Efficient Multimodal Vision-Language Model with MoE Architecture

A fast, efficient model with:
- Mixture of Experts (MoE) for efficiency
- Flash Attention for 2-4x speedup
- Extended 8K context window
- Prompt caching for 10x cost reduction
- Optimized MoE routing
"""

__version__ = "0.1.0"

# Import from core module
from .core import (
    # Model creation
    create_nthuku_fast_model,
    get_model_preset,
    
    # Main model class
    NthukuFast,
    
    # Configuration classes
    NthukuFastConfig,
    VisionEncoderConfig,
    TextDecoderConfig,
    MoEConfig,
    
    # Components
    VisionEncoder,
    TextDecoder,
    MixtureOfExperts,
    
    # Training
    NthukuFastTrainer,
    train_nthuku_fast,
    
    # Dataset management
    MultiDatasetManager,
    VisionLanguageDataset,
    MultimodalDataLoader,
    
    # Utility functions
    count_parameters,
    setup_google_drive,
    get_drive_save_path,
    clear_gpu_memory,
    optimize_for_colab,
    
    # HuggingFace integration
    NthukuFastHFConfig,
    NthukuFastForConditionalGeneration,
    save_model_to_huggingface,
)

# Import advanced features
from .kv_cache import (
    KVCache,
    PromptCache,
    CachedAttention,
    estimate_cache_savings,
)

from .optimized_moe import (
    OptimizedRouter,
    OptimizedMixtureOfExperts,
)

from .speculative_decoding import (
    SpeculativeDecoder,
    estimate_speculative_speedup,
)

from .thinking_traces import (
    ThinkingTrace,
    ThinkingStep,
    ChainOfThoughtGenerator,
    ToolUseWithReasoning,
)

__all__ = [
    # Version
    "__version__",
    
    # Model creation
    "create_nthuku_fast_model",
    "get_model_preset",
    
    # Main classes
    "NthukuFast",
    "NthukuFastConfig",
    "VisionEncoderConfig",
    "TextDecoderConfig",
    "MoEConfig",
    
    # Components
    "VisionEncoder",
    "TextDecoder",
    "MixtureOfExperts",
    
    # Training
    "NthukuFastTrainer",
    "train_nthuku_fast",
    
    # Dataset
    "MultiDatasetManager",
    "VisionLanguageDataset",
    "MultimodalDataLoader",
    
    # Utils
    "count_parameters",
    "setup_google_drive",
    "get_drive_save_path",
    "clear_gpu_memory",
    "optimize_for_colab",
    
    # HuggingFace
    "NthukuFastHFConfig",
    "NthukuFastForConditionalGeneration",
    "save_model_to_huggingface",
    
    # Advanced features
    "KVCache",
    "PromptCache",
    "CachedAttention",
    "estimate_cache_savings",
    "OptimizedRouter",
    "OptimizedMixtureOfExperts",
    "SpeculativeDecoder",
    "estimate_speculative_speedup",
    "ThinkingTrace",
    "ThinkingStep",
    "ChainOfThoughtGenerator",
    "ToolUseWithReasoning",
]
