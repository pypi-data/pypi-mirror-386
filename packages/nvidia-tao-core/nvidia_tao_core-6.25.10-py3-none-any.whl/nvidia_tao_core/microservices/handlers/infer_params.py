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

"""Functions to infer values

Each function takes as input:
- handler (dataset / model)
- app_handler
- job_context
"""
import os
import logging

from nvidia_tao_core.microservices.constants import MONAI_NETWORKS

from nvidia_tao_core.microservices.handlers.utilities import (
    search_for_base_experiment, get_model_results_path,
    get_file_list_from_cloud_storage, search_for_checkpoint, filter_files
)
from nvidia_tao_core.cloud_handlers.utils import search_for_ptm
from nvidia_tao_core.microservices.handlers.cloud_storage import create_cs_instance
from nvidia_tao_core.microservices.handlers.stateless_handlers import (
    get_handler_root, get_jobs_root, get_handler_job_metadata,
    get_handler_metadata, get_handler_kind, get_base_experiment_metadata,
    get_automl_brain_info, get_workspace_string_identifier, base_exp_uuid
)
from nvidia_tao_core.microservices.handlers.monai.helpers import find_matching_bundle_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def infer_verbose(job_context, handler_metadata):
    """Return True to enable verbose commands"""
    return True


def infer_key(job_context, handler_metadata):
    """Returns the encryption key associated with the model"""
    try:
        return handler_metadata.get("encryption_key", "tlt_encode")
    except Exception as e:
        logger.error("Exception thrown in infer_key is %s", str(e))
        return None


def infer_create_od_tf_records(job_context, handler_metadata):
    """Returns TFRecords path"""
    kind = get_handler_kind(handler_metadata)
    od_tf_records_path = get_handler_root(job_context.org_name, kind, handler_metadata.get("id"), None) + "/tfrecords/"
    return od_tf_records_path


def infer_output_dir(job_context, handler_metadata):
    """Creates output directory within jobs root"""
    results_root = get_jobs_root(user_id=job_context.user_id, org_name=job_context.org_name)
    results_dir = os.path.join(results_root, job_context.id)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    workspace_id = handler_metadata.get("workspace")
    workspace_identifier = get_workspace_string_identifier(workspace_id, workspace_cache={})
    dnn_results_dir = f'{workspace_identifier}results/{job_context.id}'
    if job_context.network == "vila":
        llm_mode = job_context.specs.get("train", {}).get("llm_mode", "lora")
        vision_mode = job_context.specs.get("train", {}).get("vision_mode", "ft")
        dnn_results_dir = f'{workspace_identifier}results/{job_context.id}/{vision_mode}_{llm_mode}'
    return dnn_results_dir


def infer_stylegan_dsconvert_output(job_context, handler_metadata):
    """Returns path of label.json for auto_labeling"""
    zip_file = f"/results/{job_context.id}/ds_convert.zip"
    return zip_file


def infer_automl_output_dir(
    job_context,
    handler_metadata,
    job_root,
    rec_number,
    exp_job_id,
    workspace_prefix_enable=True
):
    """Creates output directory within jobs root for automl"""
    results_root = get_jobs_root(user_id=job_context.user_id, org_name=job_context.org_name)
    results_dir = os.path.join(results_root, job_context.id)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    workspace_id = handler_metadata.get("workspace")
    workspace_identifier = get_workspace_string_identifier(workspace_id, workspace_cache={})
    dnn_results_dir = f'{workspace_identifier}results/{exp_job_id}'
    if not workspace_prefix_enable:
        dnn_results_dir = f'/results/{exp_job_id}'
    return dnn_results_dir


# NOTE: Only supports those with ngc_path to be PTMs
def infer_ptm(job_context, handler_metadata):
    """Returns a list of path of the ptm files of a network"""
    network = job_context.network
    handler_ptms = handler_metadata.get("base_experiment", None)
    if handler_ptms is None:
        return None
    ptm_file = []
    for handler_ptm in handler_ptms:
        if handler_ptm:
            ptm_root = get_handler_root(base_exp_uuid, "experiments", base_exp_uuid, handler_ptm)
            if network in MONAI_NETWORKS:
                ptm_file.append(search_for_base_experiment(ptm_root, network=network))
            else:
                base_experiment_metadata = get_base_experiment_metadata(handler_ptm)
                ngc_path = base_experiment_metadata.get("ngc_path") if base_experiment_metadata else None
                workspace_metadata = get_handler_metadata(handler_metadata.get("workspace"), kind="workspaces")
                cloud_type = workspace_metadata.get("cloud_type", "aws")

                # Check if running in air-gapped mode
                if os.getenv("AIRGAPPED_MODE", "false").lower() == "true" and cloud_type == "seaweedfs":
                    # In air-gapped mode, check if local model exists, otherwise use the PTM root
                    cs_instance, _ = create_cs_instance(workspace_metadata)
                    model_registry = os.getenv('LOCAL_MODEL_REGISTRY')

                    # Check if this is a Hugging Face model or NGC model
                    source_type = base_experiment_metadata.get("source_type", "ngc")
                    if source_type == "huggingface" or (":" not in ngc_path and "/" in ngc_path):
                        # Handle Hugging Face models
                        model_name = ngc_path.replace("/", "_")
                        root_path = f"{model_registry}/huggingface/{model_name}"
                    else:
                        # Handle NGC models (original logic)
                        path_part, version = ngc_path.split(":", 1)
                        model_name = path_part.split("/")[-1]
                        root_path = f"{model_registry}/{path_part}/{version}/{model_name}_v{version}"

                    cloud_path = cs_instance.search_for_ptm(root=root_path, network=network)
                    if cloud_path:
                        bucket_name = workspace_metadata.get('cloud_specific_details').get('cloud_bucket_name')
                        ptm_file.append(f"seaweedfs://{bucket_name}/{cloud_path}")
                else:
                    # Original cloud mode behavior
                    source_type = base_experiment_metadata.get("source_type", "ngc")
                    if source_type == "huggingface":
                        ptm_file.append(f"hf_model://{ngc_path}")
                    else:
                        ptm_file.append(f"ngc://{ngc_path}")
    return ",".join(ptm_file)


def _get_local_model_path_for_job(ngc_path, ptm_root, network=""):
    """Get local model path for job execution in air-gapped mode.

    Args:
        ngc_path (str): NGC path of the model
        ptm_root (str): PTM root directory
        network (str): Network architecture name for network-specific search

    Returns:
        str: Local model path if found, None otherwise
    """
    try:
        # Parse NGC path to construct local registry path
        from nvidia_tao_core.microservices.pretrained_models import split_ngc_path
        org, team, model_version = split_ngc_path(ngc_path)
        model_name, version = model_version.split(':')

        # Get local model registry path
        local_registry = os.getenv("LOCAL_MODEL_REGISTRY", "/shared-storage/models")
        local_model_path = os.path.join(local_registry, org, team, model_name, version)

        # First try the structured local registry path
        if os.path.exists(local_model_path):
            found_model = search_for_ptm(local_model_path, network=network)
            if found_model:
                return found_model

        # Fallback to ptm_root (previously downloaded models)
        if os.path.exists(ptm_root):
            found_model = search_for_ptm(ptm_root, network=network)
            if found_model:
                return found_model

        return None
    except Exception as e:
        logger.error(f"Error getting local model path for {ngc_path}: {e}")
        return None


def infer_pruned_model(job_context, handler_metadata):
    """Returns path of the pruned model"""
    jobs_root = get_jobs_root(user_id=job_context.user_id, org_name=job_context.org_name)
    if not jobs_root:
        return None
    workspace_id = handler_metadata.get("workspace")
    workspace_identifier = get_workspace_string_identifier(workspace_id, workspace_cache={})
    parent_job_metadata = get_handler_job_metadata(job_context.parent_id)
    parent_action = parent_job_metadata.get("action", "")
    pruned_model = None
    if parent_action == "retrain":
        pruned_model = f'{workspace_identifier}results/{job_context.parent_id}/pruned_model.pth'
    return pruned_model


def infer_parent_model(job_context, handler_metadata):
    """Returns path of the weight file of the parent job"""
    parent_model = get_model_results_path(handler_metadata, job_context.parent_id)
    return parent_model


def infer_parent_model_folder(job_context, handler_metadata):
    """Returns path of the weight file of the parent job"""
    parent_model = get_model_results_path(handler_metadata, job_context.parent_id, folder=True)
    return parent_model


def infer_resume_model(job_context, handler_metadata):
    """Returns path of the weight file of the current job"""
    parent_model = get_model_results_path(handler_metadata, job_context.id)
    return parent_model


def infer_resume_model_or_ptm(job_context, handler_metadata):
    """Returns path of the weight file of the current job if exists else returns path of the ptm files"""
    resume_model = infer_resume_model(job_context, handler_metadata)
    if resume_model:
        return resume_model
    return infer_ptm(job_context, handler_metadata)


def infer_ptm_if_no_resume_model(job_context, handler_metadata):
    """Returns path of path of the ptm files if there is no model to resume"""
    resume_model = infer_resume_model(job_context, handler_metadata)
    if resume_model:
        return None
    return infer_ptm(job_context, handler_metadata)


def infer_automl_assign_ptm(job_context, handler_metadata, job_root, rec_number, exp_job_id):
    """Returns path of path of the ptm files if there is no model to resume for AutoML"""
    expt_root = infer_automl_output_dir(
        job_context,
        handler_metadata,
        job_root,
        rec_number,
        exp_job_id=exp_job_id,
        workspace_prefix_enable=False
    )
    workspace_id = handler_metadata.get("workspace")
    workspace_metadata = get_handler_metadata(workspace_id, "workspaces")
    files = get_file_list_from_cloud_storage(workspace_metadata, expt_root)
    resume_model = search_for_checkpoint(handler_metadata, job_context.id, expt_root, files, "latest_model")
    if not resume_model:
        return infer_ptm(job_context, handler_metadata)
    return None


def infer_automl_resume_model(job_context, handler_metadata, job_root, rec_number, exp_job_id):
    """Returns path of the checkpoint file for the automl recommendation to resume on"""
    expt_root = infer_automl_output_dir(
        job_context,
        handler_metadata,
        job_root,
        rec_number,
        exp_job_id=exp_job_id,
        workspace_prefix_enable=False
    )
    workspace_id = handler_metadata.get("workspace")
    workspace_metadata = get_handler_metadata(workspace_id, "workspaces")
    files = get_file_list_from_cloud_storage(workspace_metadata, expt_root)
    resume_model = filter_files(files)
    resume_model.sort(reverse=False)
    if resume_model:
        resume_model = resume_model[0]
        workspace_identifier = get_workspace_string_identifier(workspace_id, workspace_cache={})
        resume_model = f"{workspace_identifier}/{resume_model}"
    return resume_model


def infer_automl_ptm_if_no_resume_model(job_context, handler_metadata, job_root, rec_number, exp_job_id):
    """Returns path of the checkpoint file for the automl recommendation to resume on"""
    expt_root = infer_automl_output_dir(
        job_context,
        handler_metadata,
        job_root,
        rec_number,
        exp_job_id=exp_job_id,
        workspace_prefix_enable=False
    )
    workspace_id = handler_metadata.get("workspace")
    workspace_metadata = get_handler_metadata(workspace_id, "workspaces")
    files = get_file_list_from_cloud_storage(workspace_metadata, expt_root)
    resume_model = filter_files(files)
    resume_model.sort(reverse=False)
    if resume_model:
        workspace_identifier = get_workspace_string_identifier(workspace_id, workspace_cache={})
        resume_model = f"{workspace_identifier}/{resume_model[0]}"
        return resume_model
    return infer_ptm(job_context, handler_metadata)


def infer_automl_assign_resume_epoch(job_context, handler_metadata, job_root, rec_number, exp_job_id):
    """Returns path automl spec file"""
    additional_epoch = 1  # epoch numbers indexed by 1
    resume_epoch_number = 0 + additional_epoch
    if infer_automl_resume_model(job_context, handler_metadata, job_root, rec_number, exp_job_id):
        brain_dict = get_automl_brain_info(job_context.id)
        resume_epoch_number = int(brain_dict.get("resume_epoch_number", -1)) + additional_epoch
    return resume_epoch_number


def infer_parent_model_evaluate(job_context, handler_metadata):
    """Returns path of the weight file of the parent job if exists else returns path of the ptm files"""
    # Assumes: <results_dir/weights> is stored
    # If extension is None: output is based on RESULTS_RELPATH
    # If extension exists, then search for that extension
    parent_job_id = job_context.parent_id
    parent_action = get_handler_job_metadata(parent_job_id).get("action")

    if parent_action == "export":
        results_root = get_jobs_root(user_id=job_context.user_id, org_name=job_context.org_name)
        parent_model = os.path.join(results_root, str(job_context.parent_id), "model.engine")
    else:
        parent_model = get_model_results_path(handler_metadata, job_context.parent_id)

    return parent_model


def infer_framework_evaluate(job_context):
    """Returns framework to evaluate model on based on the parent action"""
    parent_job_id = job_context.parent_id
    parent_action = get_handler_job_metadata(parent_job_id).get("action")

    if parent_action == "export":
        return "tensorrt"
    return "tlt"


def infer_framework_evaluate_storetrue(job_context, handler_metadata):
    """Returns whether the evaluation framework is tensorrt or not"""
    framework = infer_framework_evaluate(job_context)
    return framework == "tensorrt"


def infer_output_file(job_context, handler_metadata, extension):
    """Create output folder based on the filepath"""
    # Create all directories up until the file name
    outdir = f'/results/{job_context.id}'
    path = os.path.join(outdir, extension)
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return path


def infer_output_hdf5(job_context, handler_metadata):
    """Calls infer_output_file for model.hdf5"""
    return infer_output_file(job_context, handler_metadata, "model.hdf5")


def infer_output_pth(job_context, handler_metadata):
    """Calls infer_output_file for model.pth"""
    return infer_output_file(job_context, handler_metadata, "model.pth")


def infer_output_onnx(job_context, handler_metadata):
    """Calls infer_output_file for model.onnx"""
    return infer_output_file(job_context, handler_metadata, "model.onnx")


def infer_output_trt(job_context, handler_metadata):
    """Calls infer_output_file for model.engine"""
    return infer_output_file(job_context, handler_metadata, "model.engine")


def infer_output_weights_tlt(job_context, handler_metadata):
    """Calls infer_output_file for weights/model.tlt"""
    return infer_output_file(job_context, handler_metadata, "weights/model.tlt")


def infer_merged_json(job_context, handler_metadata):
    """Calls infer_output_file for merged.json"""
    return infer_output_file(job_context, handler_metadata, "merged.json")


def infer_cal_cache(job_context, handler_metadata):
    """Calls infer_output_file for cal.bin"""
    return infer_output_file(job_context, handler_metadata, "cal.bin")


def infer_cal_data_file(job_context, handler_metadata):
    """Calls infer_output_file for calibration.tensorfile"""
    return infer_output_file(job_context, handler_metadata, "calibration.tensorfile")


def infer_create_inference_result_file_pose(job_context, handler_metadata):
    """Calls infer_output_file for results.txt"""
    return infer_output_file(job_context, handler_metadata, "results.txt")


def infer_create_evaluate_matches_plot_reid(job_context, handler_metadata):
    """Calls infer_output_file for sampled_matches.png"""
    return infer_output_file(job_context, handler_metadata, "sampled_matches.png")


def infer_create_evaluate_cmc_plot_reid(job_context, handler_metadata):
    """Calls infer_output_file for cmc_curve.png"""
    return infer_output_file(job_context, handler_metadata, "cmc_curve.png")


def infer_create_inference_result_file_json(job_context, handler_metadata):
    """Calls infer_output_file for inference.json"""
    return infer_output_file(job_context, handler_metadata, "inference.json")


# OD helper functions

def infer_od_dir(job_context, handler_metadata, dirname):
    """Returns joined-path of handler_root and dirname"""
    handler_root = get_jobs_root(user_id=job_context.user_id, org_name=job_context.org_name)
    path = f"{handler_root}/{dirname}"
    return path


def infer_od_images(job_context, handler_metadata):
    """Calls infer_od_dir on images directory"""
    return infer_od_dir(job_context, handler_metadata, "images/")


def infer_od_labels(job_context, handler_metadata):
    """Calls infer_od_dir on labels directory"""
    return infer_od_dir(job_context, handler_metadata, "labels/")


def infer_od_annotations(job_context, handler_metadata):
    """Calls infer_od_dir on annotations.json file"""
    return infer_od_dir(job_context, handler_metadata, "annotations.json")


def infer_label_output(job_context, handler_metadata):
    """Returns path of label.json for auto_labeling"""
    results_dir = infer_output_dir(job_context, handler_metadata)
    label_output = os.path.join(results_dir, "label.json")
    return label_output


# MONAI helper functions

def infer_monai_output_dir(job_context, handler_metadata):
    """Returns path of monai output dir by appending bundle name to results dir"""
    results_dir = infer_output_dir(job_context, handler_metadata)
    ptm_model_list = get_handler_metadata(job_context.handler_id, "experiments")["base_experiment"]
    ptm_model = ptm_model_list[0] if ptm_model_list else ""
    ptm_model_path = get_handler_root(base_exp_uuid, "experiments", base_exp_uuid, ptm_model) if ptm_model else ""
    if ptm_model and not ptm_model_path:
        # If ptm_model is not found in the admin's experiments, then search in the user's experiments
        ptm_model_path = get_handler_root(org_name=job_context.org_name, kind="experiments", handler_id=ptm_model)
    if not os.path.isdir(ptm_model_path):
        # the ptm_model_path is not a directory.
        return None, None, results_dir + "/"
    bundle_name = find_matching_bundle_dir(ptm_model_path, [r'(.+?)_v\d+\.\d+\.\d+'])
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    return ptm_model_path, bundle_name, results_dir + "/"


CLI_CONFIG_TO_FUNCTIONS = {"output_dir": infer_output_dir,
                           "automl_output_dir": infer_automl_output_dir,
                           "key": infer_key,
                           "pruned_model": infer_pruned_model,
                           "parent_model": infer_parent_model,
                           "parent_model_folder": infer_parent_model_folder,
                           "parent_model_evaluate": infer_parent_model_evaluate,
                           "resume_model": infer_resume_model,
                           "resume_model_or_ptm": infer_resume_model_or_ptm,
                           "ptm_if_no_resume_model": infer_ptm_if_no_resume_model,
                           "automl_assign_ptm": infer_automl_assign_ptm,
                           "automl_resume_model": infer_automl_resume_model,
                           "automl_ptm_if_no_resume_model": infer_automl_ptm_if_no_resume_model,
                           "automl_assign_resume_epoch": infer_automl_assign_resume_epoch,
                           "framework": infer_framework_evaluate,
                           "framework_storetrue": infer_framework_evaluate_storetrue,
                           "verbose": infer_verbose,
                           "ptm": infer_ptm,
                           "create_hdf5_file": infer_output_hdf5,
                           "create_pth_file": infer_output_pth,
                           "create_onnx_file": infer_output_onnx,
                           "create_engine_file": infer_output_trt,
                           "create_weights_tlt_file": infer_output_weights_tlt,
                           "create_cal_cache": infer_cal_cache,
                           "create_cal_data_file": infer_cal_data_file,
                           "merged_json": infer_merged_json,
                           "create_inference_result_file_pose": infer_create_inference_result_file_pose,
                           "create_evaluate_matches_plot_reid": infer_create_evaluate_matches_plot_reid,
                           "create_evaluate_cmc_plot_reid": infer_create_evaluate_cmc_plot_reid,
                           "create_inference_result_file_reid": infer_create_inference_result_file_json,
                           "create_inference_result_file_mal": infer_create_inference_result_file_json,
                           "od_images": infer_od_images,
                           "od_labels": infer_od_labels,
                           "od_annotations": infer_od_annotations,
                           "create_od_tfrecords": infer_create_od_tf_records,
                           "output_dir_images_annotated": lambda a, b: infer_output_dir(a, b) + "/images_annotated/",
                           "output_dir_labels": lambda a, b: infer_output_dir(a, b) + "/labels/",
                           "output_dir_inference_json": lambda a, b: infer_output_dir(a, b) + "/annotations_mal.json",
                           "from_csv": lambda a, b: None,  # Used to infer the param from spec sheet
                           "auto_label_output": infer_label_output,
                           "stylegan_dsconvert_output": infer_stylegan_dsconvert_output,
                           "monai_output_dir": infer_monai_output_dir}
