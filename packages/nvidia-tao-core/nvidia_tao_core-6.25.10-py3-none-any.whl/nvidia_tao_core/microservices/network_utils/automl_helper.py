# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

"""Helper constants for automl."""

automl_list_helper = {
    "deformable_detr": {
        "list_2": {
            "dataset.augmentation.scales": ("img_size", "base_parameter"),
            "train.optim.lr_steps": ("lr_steps", "train.num_epochs"),
        }
    },
    "ml_recog": {
        "list_3": {
            "dataset.gaussian_blur.kernel": ("img_size", "model.input_height"),
        }
    },
    "centerpose": {
        "list_2": {
            "train.optim.lr_steps": ("lr_steps", "train.num_epochs")
        }
    },
    "ocrnet": {
        "list_2": {
            "dataset.augmentation.gaussian_radius_list": ("img_size", "model.input_height"),
        }
    },
    "action_recognition": {
        "list_2": {
            "train.optim.lr_steps": ("lr_steps", "train.num_epochs"),
        }
    },
    "pointpillars": {
        "list_2": {
            "train.decay_step_list": ("lr_steps", "train.num_epochs"),
        }
    },
    "pose_classification": {
        "list_2": {
            "train.optim.lr_steps": ("lr_steps", "train.num_epochs"),
        }
    },
    "re_identification": {
        "list_2": {
            "train.optim.lr_steps": ("lr_steps", "train.num_epochs"),
        }
    },
    "mal": {
        "list_1_backbone": {
            "model.frozen_stages": {
                "vit-deit-tiny/16": (-1, 12),
                "vit-deit-small/16": (-1, 12),
                "vit-mae-base/16": (-1, 12),
                'vit-mae-large/16': (-1, 12),
                'vit-mae-huge/14': (-1, 12),
                "fan_tiny_12_p16_224": (-1, 8),
                "fan_small_12_p16_224": (-1, 8),
                "fan_base_18_p16_224": (-1, 8),
                "fan_large_24_p16_224": (-1, 8),
                "fan_tiny_8_p4_hybrid": (-1, 8),
                "fan_small_12_p4_hybrid": (-1, 8),
                "fan_base_16_p4_hybrid": (-1, 8),
                "fan_large_16_p4_hybrid": (-1, 8)
            },
        },
    },
    "cosmos-rl": {
        "list_2": {
            "train.optm_betas": ("optimizer_betas", None),
        }
    },
}
