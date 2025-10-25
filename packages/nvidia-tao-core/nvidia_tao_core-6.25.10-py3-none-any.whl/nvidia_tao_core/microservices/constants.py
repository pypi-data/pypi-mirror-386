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

"""Constants values"""

TAO_NETWORKS = set([
    "action_recognition", "bevfusion", "classification_pyt", "grounding_dino", "mal", "mask2former",
    "mask_grounding_dino", "ml_recog", "ocdnet", "ocrnet", "optical_inspection", "pointpillars",
    "pose_classification", "re_identification", "centerpose", "visual_changenet_classify",
    "visual_changenet_segment", "deformable_detr",
    "depth_net_mono", "depth_net_stereo", "dino", "rtdetr", "segformer",  # PYT CV MODELS
    "annotations", "analytics", "augmentation", "auto_label", "image"  # Data_Service tasks.
])
MAXINE_NETWORKS = set(["maxine_eye_contact"])  # Maxine networks
VLM_NETWORKS = set(["vlm"])  # VLM networks

_OD_NETWORKS = set(["deformable_detr", "dino", "grounding_dino", "rtdetr"])
_PURPOSE_BUILT_MODELS = set([
    "action_recognition", "depth_net_mono", "depth_net_stereo", "bevfusion", "ml_recog", "ocdnet", "ocrnet",
    "optical_inspection", "pose_classification", "re_identification", "centerpose", "visual_changenet_classify",
    "visual_changenet_segment"
])

_PYT_TAO_NETWORKS = set([
    "action_recognition", "bevfusion", "depth_net_mono", "depth_net_stereo", "deformable_detr", "dino",
    "grounding_dino", "mask_grounding_dino", "mal", "mask2former", "ml_recog", "ocdnet", "ocrnet", "optical_inspection",
    "pointpillars", "pose_classification", "re_identification", "rtdetr", "centerpose", "segformer",
    "visual_changenet_classify", "visual_changenet_segment"
])
_DATA_SERVICES_ACTIONS = set([
    "annotation_format_convert", "auto_label", "augment", "analyze",
    "validate_images", "validate_annotations"
])
_DATA_GENERATE_ACTIONS = set(["dataset_convert_gaze", "augment", "validate_images"])

MEDICAL_CUSTOM_ARCHITECT = ["monai_custom", "monai_classification", "monai_detection", "monai_segmentation"]
MEDICAL_NETWORK_ARCHITECT = [
    "monai_vista3d", "monai_vista2d", "monai_annotation", "monai_genai", "monai_maisi"
] + MEDICAL_CUSTOM_ARCHITECT
MEDICAL_AUTOML_ARCHITECT = ["monai_automl", "monai_automl_generated"]
MONAI_NETWORKS = set(MEDICAL_NETWORK_ARCHITECT + MEDICAL_AUTOML_ARCHITECT)  # Data_Service tasks.
NO_SPEC_ACTIONS_MODEL = (
    "dataset_convert_gaze", "evaluate", "retrain", "export", "gen_trt_engine", "inference"
)  # Actions with **optional** specs
NO_PTM_MODELS = set([])  # These networks don't have a pretrained model that can be downloaded from ngc model registry
_ITER_MODELS = set([])  # These networks operate on iterations instead of epochs

# These networks have fields in their config file which has both backbone only loading weights
# as well as full architecture loading;
# ex: model.pretrained_backbone_path and train.pretrained_model_path in dino
BACKBONE_AND_FULL_MODEL_PTM_SUPPORTING_NETWORKS = set([
    "dino", "grounding_dino", "mask_grounding_dino", "classification_pyt"
])

AUTOML_DISABLED_NETWORKS = ["mal", "maxine_eye_contact"]  # These networks can't support AutoML
TENSORBOARD_DISABLED_NETWORKS = [
    'classification_pyt',
]  # These networks currently don't produce tfevents logs as they are third party models
TENSORBOARD_EXPERIMENT_LIMIT = 10  # Maximum number of Tensorboard enabled experiments per user
# These networks can't support writing validation metrics at regular intervals during training,
# only at end of training they run evaluation
NO_VAL_METRICS_DURING_TRAINING_NETWORKS = set([])
MISSING_EPOCH_FORMAT_NETWORKS = set([
    "pointpillars", "bevfusion", "cosmos-rl"
])  # These networks have the epoch/iter number not following a format; ex: 1.pth instead of 001.pth
STATUS_CALLBACK_MISMATCH_WITH_CHECKPOINT_EPOCH = set([
    "pointpillars"
])  # status json epoch number is 1 less than epoch number generated in checkppoint file
STATUS_CALLBACK_MISMATCH_WITH_CHECKPOINT_EPOCH_TMP = set(["ml_recog"])

COPY_MODEL_PARAMS_FROM_TRAIN_NETWORKS = [
    "centerpose", "deformable_detr", "dino", "grounding_dino",
    "mask_grounding_dino", "mask2former", "visual_changenet_classify", "visual_changenet_segment"
]

MONAI_DATASET_DEFAULT_SPECS = {
    "next_image_strategy": "sequential",
    "cache_image_url": "",
    "cache_force": False,
    "notify_study_urls": [],
    "notify_image_urls": [],
    "notify_label_urls": [],
}

VALID_MODEL_DOWNLOAD_TYPE = ("monai_bundle", "tao")
CACHE_TIME_OUT = 60 * 60  # cache timeout period in second
LAST_ACCESS_TIME_OUT = 60  # last access timeout period in second

CONTINUOUS_STATUS_KEYS = ["cur_iter", "epoch", "max_epoch", "eta", "time_per_epoch", "time_per_iter", "key_metric"]

NETWORK_CONTAINER_MAPPING = {"action_recognition": "TAO_PYTORCH",
                             "depth_net_mono": "TAO_PYTORCH",
                             "depth_net_stereo": "TAO_PYTORCH",
                             "annotations": "TAO_DS",
                             "auto_label": "TAO_DS",
                             "analytics": "TAO_DS",
                             "augmentation": "TAO_DS",
                             "bevfusion": "TAO_PYTORCH",
                             "centerpose": "TAO_PYTORCH",
                             "classification_pyt": "TAO_PYTORCH",
                             "deformable_detr": "TAO_PYTORCH",
                             "dino": "TAO_PYTORCH",
                             "grounding_dino": "TAO_PYTORCH",
                             "image": "TAO_DS",
                             "mal": "TAO_PYTORCH",
                             "mask2former": "TAO_PYTORCH",
                             "mask_grounding_dino": "TAO_PYTORCH",
                             "ml_recog": "TAO_PYTORCH",
                             "ocdnet": "TAO_PYTORCH",
                             "ocrnet": "TAO_PYTORCH",
                             "optical_inspection": "TAO_PYTORCH",
                             "pointpillars": "TAO_PYTORCH",
                             "pose_classification": "TAO_PYTORCH",
                             "re_identification": "TAO_PYTORCH",
                             "rtdetr": "TAO_PYTORCH",
                             "segformer": "TAO_PYTORCH",
                             "visual_changenet_classify": "TAO_PYTORCH",
                             "visual_changenet_segment": "TAO_PYTORCH",
                             "maxine_eye_contact": "MAXINE_DLDK",
                             "mae": "TAO_PYTORCH",
                             "vila": "VILA"}

CV_ACTION_RULES = {
    'train': [],
    'distill': ["train", "retrain"],
    'quantize': ["train", "retrain"],
    'evaluate': ["train", "prune", "retrain", "export", "gen_trt_engine", "trtexec"],
    'prune': ["train", "retrain"],
    'inference': ["train", "prune", "retrain", "export", "gen_trt_engine", "trtexec"],
    'retrain': ["train", "prune"],
    'export': ["train", "prune", "retrain"],
    'gen_trt_engine': ['export'],
    'trtexec': ['export'],
}

CV_ACTION_CHAINED_ONLY = {"prune", "distill", "quantize", "retrain", "export", "gen_trt_engine", "trtexec"}

AIRGAP_DEFAULT_USER = 'anonymous'
