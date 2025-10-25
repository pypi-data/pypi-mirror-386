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

"""Configuration hyperparameter schema to visualize the model results."""

from dataclasses import dataclass

from nvidia_tao_core.config.utils.types import (
    STR_FIELD,
    INT_FIELD,
    BOOL_FIELD,
    FLOAT_FIELD,
)


@dataclass
class Sparse4DVisualizeConfig:
    """Visualization configuration for Sparse4D."""

    show: bool = BOOL_FIELD(
        value=False,
        default_value=False,
        description="Show visualization",
        display_name="Show visualization"
    )
    vis_dir: str = STR_FIELD(
        value="./vis",
        default_value="./vis",
        description="Visualization directory",
        display_name="Visualization directory"
    )
    vis_score_threshold: float = FLOAT_FIELD(
        value=0.25,
        default_value=0.25,
        valid_min=0,
        valid_max=1,
        description="Visualization score threshold",
        display_name="Visualization score threshold"
    )
    n_images_col: int = INT_FIELD(
        value=6,
        default_value=6,
        valid_min=1,
        valid_max="inf",
        description="Number of images per column",
        display_name="Number of images per column"
    )
    viz_down_sample: int = INT_FIELD(
        value=3,
        default_value=3,
        valid_min=1,
        valid_max="inf",
        description="Visualization down sample",
        display_name="Visualization down sample"
    )
