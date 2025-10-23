"""强化学习训练模块（第11章：Agentic RL）

本模块提供基于TRL的强化学习训练功能，包括：
- SFT (Supervised Fine-Tuning): 监督微调
- GRPO (Group Relative Policy Optimization): 群体相对策略优化
- PPO (Proximal Policy Optimization): 近端策略优化
- Reward Modeling: 奖励模型训练
"""

# 检查TRL是否可用
try:
    import trl
    TRL_AVAILABLE = True
except ImportError:
    TRL_AVAILABLE = False

from .trainers import SFTTrainerWrapper, GRPOTrainerWrapper, PPOTrainerWrapper
from .datasets import (
    GSM8KDataset,
    create_math_dataset,
    create_sft_dataset,
    create_rl_dataset,
    preview_dataset,
    format_math_dataset
)
from .rewards import (
    MathRewardFunction,
    create_accuracy_reward,
    create_length_penalty_reward,
    create_step_reward,
    evaluate_rewards
)
from .utils import TrainingConfig, setup_training_environment

__all__ = [
    # 可用性标志
    "TRL_AVAILABLE",

    # 训练器
    "SFTTrainerWrapper",
    "GRPOTrainerWrapper",
    "PPOTrainerWrapper",

    # 数据集
    "GSM8KDataset",
    "create_math_dataset",
    "create_sft_dataset",
    "create_rl_dataset",
    "preview_dataset",
    "format_math_dataset",

    # 奖励函数
    "MathRewardFunction",
    "create_accuracy_reward",
    "create_length_penalty_reward",
    "create_step_reward",
    "evaluate_rewards",

    # 工具函数
    "TrainingConfig",
    "setup_training_environment",
]

