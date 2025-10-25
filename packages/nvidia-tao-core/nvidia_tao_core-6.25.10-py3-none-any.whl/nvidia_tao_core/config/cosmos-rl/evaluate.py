# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Default evaluation config file for Cosmos-RL"""

from typing import Optional
from dataclasses import dataclass

from nvidia_tao_core.config.utils.types import (
    BOOL_FIELD,
    FLOAT_FIELD,
    STR_FIELD,
    INT_FIELD,
    DATACLASS_FIELD,
)


@dataclass
class TaskConfig:
    """Task configuration for evaluation."""

    type: str = STR_FIELD(
        default_value="its_directionality",
        value="its_directionality",
        display_name="Task type",
        valid_options="its_directionality,general",
        description="Type of evaluation task (general, its_directionality)"
    )


@dataclass
class MetricsConfig:
    """Metrics configuration for general evaluation."""

    names: str = STR_FIELD(
        default_value="bleu,rouge,bertscore",
        value="bleu,rouge,bertscore",
        display_name="Metric names",
        valid_options="bleu,rouge,bertscore",
        description="Comma-separated list of metrics to compute (bleu, rouge, bertscore)"
    )
    bertscore_model: Optional[str] = STR_FIELD(
        default_value="microsoft/deberta-xlarge-mnli",
        value="microsoft/deberta-xlarge-mnli",
        display_name="BERTScore model",
        description="Model to use for BERTScore computation (e.g., microsoft/deberta-xlarge-mnli)"
    )
    bertscore_lang: str = STR_FIELD(
        default_value="en",
        value="en",
        display_name="BERTScore language",
        description="Language for BERTScore computation"
    )


@dataclass
class SoftAccuracyConfig:
    """Soft accuracy configuration for general evaluation."""

    enabled: bool = BOOL_FIELD(
        default_value=True,
        value=True,
        display_name="Enable soft accuracy",
        description="Enable soft accuracy computation based on token overlap F1"
    )
    f1_threshold: float = FLOAT_FIELD(
        default_value=0.8,
        value=0.8,
        valid_min=0.0,
        valid_max=1.0,
        display_name="F1 threshold",
        description="F1 threshold for soft accuracy (predictions with F1 >= threshold are considered correct)"
    )


@dataclass
class DatasetConfig:
    """Dataset configuration for evaluation."""

    annotation_path: str = STR_FIELD(
        default_value="",
        value="",
        display_name="Annotation path",
        description="Path to the annotation JSON file containing evaluation samples"
    )
    media_dir: Optional[str] = STR_FIELD(
        default_value="",
        value="",
        display_name="Media directory",
        description="Optional path to media files directory (if different from annotation paths)"
    )
    system_prompt: str = STR_FIELD(
        default_value="You are a helpful assistant that can answer questions about a street-view CCTV footage. "
                      "The vehicles that need attention are marked with bounding boxes and IDs.",
        value="You are a helpful assistant that can answer questions about a street-view CCTV footage. "
              "The vehicles that need attention are marked with bounding boxes and IDs.",
        display_name="System prompt",
        description="System prompt for the evaluation tasks"
    )


@dataclass
class ModelConfig:
    """Model configuration for evaluation."""

    model_name: str = STR_FIELD(
        default_value="nvidia/Cosmos-Reason1-7B",
        value="nvidia/Cosmos-Reason1-7B",
        display_name="Model name",
        description="Model name or path to safetensors directory"
    )
    save_folder: str = STR_FIELD(
        default_value="cr1_1_zero_shot",
        value="cr1_1_zero_shot",
        display_name="Save folder",
        description="Folder name to save the output results"
    )
    tokenizer_model_name: str = STR_FIELD(
        default_value="qwen2.5-vl-7b",
        value="qwen2.5-vl-7b",
        display_name="Tokenizer model name",
        description="Tokenizer model name (qwen2.5-vl-7b, qwen2-vl-2b, qwen2.5-vl-32b, qwen2.5-vl-72b)"
    )
    dtype: str = STR_FIELD(
        default_value="bfloat16",
        value="bfloat16",
        display_name="Data type",
        description="Data type for model weights (bfloat16, float16)"
    )
    tp_size: int = INT_FIELD(
        default_value=1,
        value=1,
        valid_min=1,
        valid_max=8,
        display_name="Tensor parallel size",
        description="Tensor parallel size for distributed inference"
    )
    max_length: int = INT_FIELD(
        default_value=128000,
        value=128000,
        valid_min=1024,
        valid_max=1000000,
        display_name="Maximum sequence length",
        description="Maximum sequence length for the model"
    )
    enable_lora: bool = BOOL_FIELD(
        default_value=False,
        value=False,
        display_name="Enable LoRA merging",
        description="Enable LoRA model merging (merge LoRA weights with base model before evaluation)"
    )
    base_model_path: Optional[str] = STR_FIELD(
        default_value="",
        value="",
        display_name="Base model path",
        description="Path to base model for LoRA merging (used when enable_lora is True)"
    )


@dataclass
class EvaluationConfig:
    """Evaluation parameters configuration."""

    answer_type: str = STR_FIELD(
        default_value="freeform",
        value="freeform",
        display_name="Answer type",
        description="Expected answer format (letter, reasoning, freeform)"
    )
    num_processes: int = INT_FIELD(
        default_value=40,
        value=40,
        valid_min=1,
        valid_max=128,
        display_name="Number of processes",
        description="Number of parallel workers for evaluation"
    )
    skip_saved: bool = BOOL_FIELD(
        default_value=False,
        value=False,
        display_name="Skip saved results",
        description="Skip tasks for which results are already saved"
    )
    seed: int = INT_FIELD(
        default_value=1,
        value=1,
        valid_min=0,
        valid_max=999999,
        display_name="Random seed",
        description="Random seed for reproducibility"
    )
    limit: int = INT_FIELD(
        default_value=-1,
        value=-1,
        valid_min=-1,
        valid_max=999999,
        display_name="Task limit",
        description="Limit the number of tasks to evaluate (-1 for no limit, useful for debugging)"
    )
    total_shard: int = INT_FIELD(
        default_value=1,
        value=1,
        valid_min=1,
        valid_max=64,
        display_name="Total shards",
        description="Total number of shards for distributed evaluation"
    )
    shard_id: int = INT_FIELD(
        default_value=0,
        value=0,
        valid_min=0,
        valid_max=63,
        display_name="Shard ID",
        description="Current shard ID (0-based)"
    )
    soft_accuracy: SoftAccuracyConfig = DATACLASS_FIELD(
        SoftAccuracyConfig(),
        description="Soft accuracy configuration for general evaluation"
    )


@dataclass
class VisionConfig:
    """Vision processing configuration."""

    fps: int = INT_FIELD(
        default_value=4,
        value=4,
        valid_min=1,
        valid_max=30,
        display_name="Video FPS",
        description="Downsample video frame rate"
    )
    total_pixels: int = INT_FIELD(
        default_value=3136000,
        value=3136000,
        valid_min=100000,
        valid_max=10000000,
        display_name="Total pixels",
        description="Video or image resolution in total pixels"
    )


@dataclass
class GenerationConfig:
    """Generation parameters configuration."""

    max_retries: int = INT_FIELD(
        default_value=10,
        value=10,
        valid_min=0,
        valid_max=50,
        display_name="Maximum retries",
        description="Maximum number of retries for failed generations"
    )
    max_tokens: int = INT_FIELD(
        default_value=1024,
        value=1024,
        valid_min=1,
        valid_max=8192,
        display_name="Maximum tokens",
        description="Maximum number of tokens in the generated response"
    )
    temperature: float = FLOAT_FIELD(
        default_value=0.0,
        value=0.0,
        valid_min=0.0,
        valid_max=2.0,
        display_name="Temperature",
        description="Temperature for sampling (0.0 for greedy decoding)"
    )
    repetition_penalty: float = FLOAT_FIELD(
        default_value=1.0,
        value=1.0,
        valid_min=0.1,
        valid_max=2.0,
        display_name="Repetition penalty",
        description="Repetition penalty for generation"
    )
    presence_penalty: float = FLOAT_FIELD(
        default_value=0.0,
        value=0.0,
        valid_min=-2.0,
        valid_max=2.0,
        display_name="Presence penalty",
        description="Presence penalty for generation"
    )
    frequency_penalty: float = FLOAT_FIELD(
        default_value=0.0,
        value=0.0,
        valid_min=-2.0,
        valid_max=2.0,
        display_name="Frequency penalty",
        description="Frequency penalty for generation"
    )


@dataclass
class ResultsConfig:
    """Results and output configuration."""

    save_individual_results: bool = BOOL_FIELD(
        default_value=True,
        value=True,
        display_name="Save individual results",
        description="Save individual result JSON files for each sample"
    )
    save_confusion_matrix: bool = BOOL_FIELD(
        default_value=True,
        value=True,
        display_name="Save confusion matrix",
        description="Generate and save confusion matrix visualization"
    )
    save_metrics_summary: bool = BOOL_FIELD(
        default_value=True,
        value=True,
        display_name="Save metrics summary",
        description="Save overall metrics summary JSON file"
    )


@dataclass
class EvaluateConfig:
    """Main evaluation configuration."""

    task: TaskConfig = DATACLASS_FIELD(
        TaskConfig(),
        description="Task configuration for evaluation"
    )
    dataset: DatasetConfig = DATACLASS_FIELD(
        DatasetConfig(),
        description="Dataset configuration for evaluation"
    )
    model: ModelConfig = DATACLASS_FIELD(
        ModelConfig(),
        description="Model configuration"
    )
    evaluation: EvaluationConfig = DATACLASS_FIELD(
        EvaluationConfig(),
        description="Evaluation parameters"
    )
    vision: VisionConfig = DATACLASS_FIELD(
        VisionConfig(),
        description="Vision processing configuration"
    )
    generation: GenerationConfig = DATACLASS_FIELD(
        GenerationConfig(),
        description="Generation parameters"
    )
    metrics: MetricsConfig = DATACLASS_FIELD(
        MetricsConfig(),
        description="Metrics configuration for general evaluation"
    )
    results: ResultsConfig = DATACLASS_FIELD(
        ResultsConfig(),
        description="Results and output configuration"
    )


@dataclass
class ExperimentConfig:
    """Experiment configuration for Cosmos-RL evaluation."""

    results_dir: str = STR_FIELD(
        default_value="/results",
        value="/results",
        display_name="Results directory",
        description="Directory to save evaluation results"
    )
    evaluate: EvaluateConfig = DATACLASS_FIELD(
        EvaluateConfig(),
        description="Evaluation configuration"
    )
