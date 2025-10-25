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

"""API Stateless handlers modules"""
import os
import copy
import json
import uuid
import orjson
import traceback
import subprocess
from pathlib import Path
from collections import OrderedDict
from datetime import datetime, timezone
import logging

from nvidia_tao_core.microservices.constants import CV_ACTION_CHAINED_ONLY, CV_ACTION_RULES
from nvidia_tao_core.microservices.handlers.encrypt import NVVaultEncryption
from nvidia_tao_core.microservices.handlers.mongo_handler import MongoHandler

BACKEND = os.getenv("BACKEND", "local-k8s")
tao_root = os.environ.get("TAO_ROOT", "/tmp/shared/orgs/")
base_exp_uuid = "00000000-0000-0000-0000-000000000000"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_root():
    """Return root path"""
    return tao_root


def __pathlib_glob(rootdir, handler_id, job_id):
    try:
        for entry in rootdir.glob('**/' + f"{handler_id}/{job_id}"):
            if entry.is_dir():
                return str(entry.resolve())
        return ""
    except Exception as e:
        logger.error("Exception thrown in pathlob glob is %s", str(e))
        logger.error("Issue during finding handler_root: %s", traceback.format_exc())
        return ""


def validate_automl_settings(automl_settings):
    """Validate automl algorithm settings to make sure algorithm, max_recommendations, R, nu are valid"""
    if type(automl_settings) is not dict and type(automl_settings) is not OrderedDict:
        return f"validation input automl_settings must be a dict, instead is {type(automl_settings)}"
    automl_enabled = automl_settings.get("automl_enabled", False)
    if automl_enabled:
        if automl_settings.get("automl_algorithm", "") in ("hyperband", "h"):
            r = automl_settings.get("automl_R", 27)
            nu = automl_settings.get("automl_nu", 3)
            epoch_multiplier = automl_settings.get("epoch_multiplier", 1)
            if r <= 1 or nu <= 1:
                return "automl_R, automl_nu must be greater than 1"
            if nu > r:
                return "automl_nu must be less than or equal to automl_R"
            if epoch_multiplier <= 0:
                return "epoch_multiplier must be greater than 0"
        elif automl_settings.get("automl_algorithm", "") in ("bayesian", "b"):
            if automl_settings.get("automl_max_recommendations", 20) <= 0:
                return "automl_max_recommendations must be greater than 0"
        else:
            return "automl_algorithm must be 'hyperband' or 'bayesian'"
    return None


def get_handler_root(org_name=None, kind=None, handler_id=None, job_id=None):
    """Return handler root path"""
    handler_id = handler_id if handler_id else ""
    job_id = job_id if job_id else ""
    rootdir = Path(get_root())
    if not rootdir.exists():
        return ""
    if org_name:
        rootdir = rootdir / org_name
    else:
        return __pathlib_glob(rootdir, handler_id, job_id)
    if kind:
        if kind[-1] != 's':
            kind += 's'
        rootdir = rootdir / f"{kind}/{handler_id}"
        if job_id:
            rootdir = rootdir / f"{job_id}"
        rootdir = str(rootdir.resolve())
        if os.path.exists(rootdir):
            return rootdir
    else:
        return __pathlib_glob(rootdir, handler_id, job_id)
    return ""


def get_jobs_root(user_id=None, org_name=None):
    """Return handler root path"""
    return os.path.join(get_root(), org_name, "users", user_id, "jobs")


def get_base_experiment_path(handler_id, create_if_not_exist=True):
    """Return base_experiment root path"""
    base_experiment_path = f"{tao_root}/{base_exp_uuid}/experiments/{base_exp_uuid}/{handler_id}"
    if not os.path.exists(base_experiment_path) and create_if_not_exist:
        os.makedirs(base_experiment_path, exist_ok=True)
        subprocess.getoutput(f"chmod -R 777 {base_experiment_path}")
    return base_experiment_path


def get_base_experiments_metadata_path():
    """Return base_experiment root path"""
    base_experiments_metadata_path = f"{tao_root}/{base_exp_uuid}/experiments/{base_exp_uuid}/ptm_metadatas.json"
    return base_experiments_metadata_path


def get_job_specs(job_id, automl=False, automl_experiment_id="0"):
    """Return specs used to run the job"""
    if automl:
        mongo_jobs = MongoHandler("tao", "automl_jobs")
        job_query = {'id': job_id}
        automl_info = mongo_jobs.find_one(job_query)
        return automl_info.get("specs", {}).get(automl_experiment_id, {})
    job_metadata = get_job(job_id)
    return job_metadata.get("specs", {})


def save_job_specs(job_id, specs, automl=False, automl_experiment_id="0"):
    """Save specs used to run the job"""
    if isinstance(specs, str):
        try:
            import toml
            specs = toml.loads(specs)
        except Exception as e:
            logger.error(f"Failed to parse TOML spec: {e}")

    # Ensure spec is a dictionary
    if not isinstance(specs, dict):
        raise ValueError(f"Spec is not a dictionary or parseable string: {type(specs)}")

    if automl:
        mongo_jobs = MongoHandler("tao", "automl_jobs")
        job_query = {'id': job_id}
        mongo_jobs.upsert(job_query, {"specs": {automl_experiment_id: specs}})
    else:
        mongo_jobs = MongoHandler("tao", "jobs")
        job_query = {'id': job_id}
        mongo_jobs.upsert(job_query, {"specs": specs})


def get_handler_log_root(user_id, org_name, handler_id):
    """Return path of logs folder under handler_root"""
    return os.path.join(get_root(), org_name, "users", user_id, "logs")


def get_log_file_path(user_id, org_name, handler_id, job_id, automl_expt_id, automl_experiment_number):
    """Return path of logs file"""
    if job_id == automl_expt_id:
        log_root = get_handler_log_root(user_id, org_name, handler_id)
        logfile = os.path.join(log_root, job_id + ".txt")
    else:
        job_root = get_jobs_root(user_id, org_name)
        experiment_dir = f"experiment_{automl_experiment_number}"
        logfile = os.path.join(job_root, job_id, experiment_dir, "log.txt")
    return logfile


def get_handler_job_metadata(job_id):
    """Return metadata info present in job_id.json inside jobs_metadata folder"""
    # Only metadata of a particular job
    metadata = {}
    if job_id:
        mongo_jobs = MongoHandler("tao", "jobs")
        job_query = {'id': job_id}
        metadata = mongo_jobs.find_one(job_query)
    return metadata


def get_toolkit_status(job_id):
    """Returns the status of the job reported from the frameworks container"""
    metadata_info = get_handler_job_metadata(job_id)
    toolkit_status = ""
    toolkit_detailed_status = metadata_info.get("job_details", {}).get(job_id, {}).get("detailed_status", {})
    if toolkit_detailed_status:
        toolkit_status = toolkit_detailed_status.get("status", "")
    return toolkit_status


def json_serializable(response):
    """Check if response is json serializable"""
    try:
        orjson.dumps(response.json())
        return True
    except Exception as e:
        logger.error("Exception thrown in json serializable is %s", str(e))
        return False


# Sub for handler.metadata_file with handler_root(handler_id)
def get_handler_metadata_file(org_name, handler_id, kind=None):
    """Return path of metadata.json under handler_root"""
    return get_handler_root(org_name, kind, handler_id, None) + "/metadata.json"


def get_handler_jobs_metadata_root(org_name, handler_id, kind=None):
    """Return path of job_metadata folder folder under handler_root"""
    return get_handler_root(org_name, kind, handler_id, None) + "/jobs_metadata/"


def get_base_experiment_metadata(base_experiment_id):
    """Read PTM metadata from DB"""
    mongo_experiments = MongoHandler("tao", "experiments")
    base_experiment_metadata = mongo_experiments.find_one({'id': base_experiment_id})
    return base_experiment_metadata


def update_base_experiment_metadata(base_experiment_id, base_experiment_metadata_update):
    """Read PTM metadata file and update the metadata info of a particular base_experiment"""
    mongo_experiments = MongoHandler("tao", "experiments")
    mongo_experiments.upsert({'id': base_experiment_id}, base_experiment_metadata_update)


def get_handler_metadata(handler_id, kind):
    """Return metadata info present in DB"""
    if not kind:
        return {}
    if kind[-1] != 's':
        kind += 's'
    mongo = MongoHandler("tao", kind)
    handler_query = {'id': handler_id}
    metadata = mongo.find_one(handler_query)
    return metadata


def write_handler_metadata(handler_id, metadata, kind):
    """Write metadata info to DB"""
    if kind[-1] != 's':
        kind += 's'
    mongo = MongoHandler("tao", kind)
    handler_query = {'id': handler_id}
    mongo.upsert(handler_query, metadata)


def get_handler_metadata_with_jobs(handler_id, kind=""):
    """Return a list of job_metadata info of multiple jobs"""
    metadata = get_handler_metadata(handler_id, kind=kind)
    metadata["jobs"] = []
    jobs = get_jobs_for_handler(handler_id, kind)
    for job in jobs:
        metadata["jobs"].append(job)
    return metadata


def write_job_metadata(job_id, metadata):
    """Write job metadata info present in jobs_metadata folder"""
    mongo_jobs = MongoHandler("tao", "jobs")
    jobs_query = {'id': job_id}
    mongo_jobs.upsert(jobs_query, metadata)


def get_job_id_of_action(handler_id, kind, action):
    """Find jobID within a handler matching an action"""
    handler_job_id = None
    jobs = get_jobs_for_handler(handler_id, kind)
    for job in jobs:
        job_id = job.get("id")
        if job.get("action") == action and job.get('status') == "Done":
            handler_job_id = job_id
            break
    if not handler_job_id:
        raise ValueError(
            f"No job found or no job with status Done found for action:{action}, handler:{handler_id}, kind:{kind}"
        )
    return handler_job_id


def update_handler_with_jobs_info(jobs_metadata, handler_id, job_id, kind):
    """Update jobs info in handler metadata"""
    handler_metadata = get_handler_metadata(handler_id, kind)
    if handler_metadata:
        if "jobs" not in handler_metadata:
            handler_metadata["jobs"] = {}
        if job_id not in handler_metadata["jobs"]:
            handler_metadata["jobs"][job_id] = {}
        handler_metadata["jobs"][job_id]["name"] = jobs_metadata.get("name")
        handler_metadata["jobs"][job_id]["status"] = jobs_metadata.get("status")
        handler_metadata["jobs"][job_id]["action"] = jobs_metadata.get("action")
        job_details = jobs_metadata.get("job_details", {}).get(job_id, {})
        detailed_status = job_details.get("detailed_status", {})
        handler_metadata["jobs"][job_id]["detailed_status_message"] = detailed_status.get("message")
        handler_metadata["jobs"][job_id]["eta"] = jobs_metadata.get("job_details", {}).get(job_id, {}).get("eta")
        handler_metadata["jobs"][job_id]["epoch"] = jobs_metadata.get("job_details", {}).get(job_id, {}).get("epoch")
        handler_metadata["jobs"][job_id]["max_epoch"] = job_details.get("max_epoch")
        write_handler_metadata(handler_id, handler_metadata, kind)


def get_handler_status(handler_metadata):
    """Compute experiment level status based on status of jobs"""
    if "jobs" in handler_metadata:
        status_set = set([])
        for job_id in handler_metadata["jobs"]:
            status = handler_metadata["jobs"][job_id].get("status", "")
            if status:
                status_set.add(status)
        if not status_set or len(status_set) == 0:
            return "Pending"
        if any(current_status == "Error" for current_status in status_set):
            return "Error"
        if any(current_status == "Pausing" for current_status in status_set):
            return "Pausing"
        if any(current_status == "Canceling" for current_status in status_set):
            return "Canceling"
        if any(current_status == "Resuming" for current_status in status_set):
            return "Resuming"
        if any(current_status == "Paused" for current_status in status_set):
            return "Paused"
        if any(current_status == "Canceled" for current_status in status_set):
            return "Canceled"
        if any(current_status == "Running" for current_status in status_set):
            return "Running"
        if len(status_set) == 2 and status_set == {"Done", "Pending"}:
            return "Running"
        success_jobs = sum(1 for current_status in status_set if current_status == "Done")
        if success_jobs == len(status_set):
            return "Done"
    return "Pending"


def update_job_status(handler_id, job_id, status, kind=""):
    """Update the job status in jobs_metadata/job_id.json"""
    metadata = get_handler_job_metadata(job_id)
    if metadata:
        current_status = metadata.get("status", "")
        if (current_status not in ("Canceled", "Canceling", "Pausing", "Paused") or
                (current_status == "Canceling" and status == "Canceled") or
                (current_status == "Pausing" and status == "Paused")):
            if status != current_status:
                metadata["last_modified"] = datetime.now(tz=timezone.utc)
            metadata["status"] = status
            if kind:
                update_handler_with_jobs_info(metadata, handler_id, job_id, kind)
            write_job_metadata(job_id, metadata)


def update_job_metadata(handler_id, job_id, metadata_key="job_details", data="", kind=""):
    """Update the job status in jobs_metadata/job_id.json"""
    metadata = get_handler_job_metadata(job_id)
    if metadata:
        if data != metadata.get(metadata_key, {}):
            metadata["last_modified"] = datetime.now(tz=timezone.utc)
        metadata[metadata_key] = data
        if metadata_key == "job_details" and kind:
            update_handler_with_jobs_info(metadata, handler_id, job_id, kind)
        write_job_metadata(job_id, metadata)


def update_job_message(handler_id, job_id, kind, message, automl_expt_job_id=None, update_automl_expt=False):
    """Update detailed status message"""
    metadata = get_handler_job_metadata(job_id)
    if metadata:
        if "job_details" not in metadata:
            metadata["job_details"] = {}
        update_job_id = job_id
        if update_automl_expt and automl_expt_job_id:
            update_job_id = automl_expt_job_id
        if update_job_id not in metadata["job_details"]:
            metadata["job_details"][update_job_id] = {}
        if "detailed_status" not in metadata["job_details"][update_job_id]:
            metadata["job_details"][update_job_id]["detailed_status"] = {}
        metadata["job_details"][update_job_id]["detailed_status"]["message"] = message
        update_handler_with_jobs_info(metadata, handler_id, job_id, kind)
        write_job_metadata(job_id, metadata)


def get_automl_brain_info(brain_job_id):
    """Get automl brain info"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    automl_info = mongo_jobs.find_one(job_query)
    return automl_info.get("brain", {})


def save_automl_brain_info(brain_job_id, brain_dict):
    """Save automl brain info"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    mongo_jobs.upsert(job_query, {"brain": brain_dict})


def get_automl_controller_info(brain_job_id):
    """Get automl controller info"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    automl_info = mongo_jobs.find_one(job_query)
    return automl_info.get("controller", {})


def save_automl_controller_info(brain_job_id, controller_list):
    """Save automl controller info"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    mongo_jobs.upsert(job_query, {"controller": controller_list})


def get_automl_current_rec(brain_job_id):
    """Get automl current recommendation"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    automl_info = mongo_jobs.find_one(job_query)
    return automl_info.get("current_rec", 0)


def save_automl_current_rec(brain_job_id, current_rec):
    """Save automl current recommendation"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    mongo_jobs.upsert(job_query, {"current_rec": current_rec})


def get_automl_best_rec_info(brain_job_id):
    """Get automl best recommendation info"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    automl_info = mongo_jobs.find_one(job_query)
    return automl_info.get("best_rec_number", "-1"), automl_info.get("best_rec_id", "-1")


def save_automl_best_rec_info(brain_job_id, best_rec_number, best_rec_job_id):
    """Save automl best recommendation info"""
    mongo_jobs = MongoHandler("tao", "automl_jobs")
    job_query = {'id': brain_job_id}
    mongo_jobs.upsert(job_query, {"best_rec_number": str(best_rec_number), "best_rec_id": str(best_rec_job_id)})


def is_request_automl(handler_id, action, kind):
    """Returns if the job requested is automl based train or not"""
    handler_metadata = resolve_metadata(kind, handler_id)
    if handler_metadata.get("automl_settings", {}).get("automl_enabled", False) and action == "train":
        return True
    return False


def update_automl_stats(job_id, automl_stats={}):
    """Write automl stats to job_metadata"""
    job_metadata = get_job(job_id)
    if not automl_stats:
        automl_stats["message"] = "Stats will be updated in a few seconds"

    if "job_details" not in job_metadata:
        job_metadata["job_details"] = {}
    if job_id not in job_metadata["job_details"]:
        job_metadata["job_details"][job_id] = {}
    job_metadata["job_details"][job_id]["automl_brain_info"] = []
    job_metadata["job_details"][job_id]["automl_result"] = []
    for key, value in automl_stats.items():
        if "best_" in key:
            job_metadata["job_details"][job_id]["automl_result"].append({"metric": key, "value": value})
        else:
            job_metadata["job_details"][job_id]["automl_brain_info"].append({"metric": key, "value": str(value)})
    write_job_metadata(job_id, job_metadata)


def status_lookup_job_id(job_id, automl=False, callback_data={}, experiment_number="0"):
    """Construct job id for indexing job_status table"""
    lookup_job_id = job_id
    if automl:
        if callback_data:
            experiment_number = callback_data.get("experiment_number", "0")
        lookup_job_id = f"{lookup_job_id}_{experiment_number}"
    return lookup_job_id


def get_internal_job_status_update_data(automl_experiment_number="0", message=""):
    """Get internal job status update data"""
    date_time = datetime.now()
    date_object = date_time.date()
    time_object = date_time.time()
    time = "{}:{}:{}".format(  # noqa pylint: disable=C0209
        time_object.hour,
        time_object.minute,
        time_object.second
    )
    date = "{}/{}/{}".format(  # noqa pylint: disable=C0209
        date_object.month,
        date_object.day,
        date_object.year
    )
    data = {
        "date": date,
        "time": time,
        "status": "FAILURE",
        "verbosity": "INFO",
    }
    if message:
        data["message"] = message
    data_string = json.dumps(data)
    return data_string


def internal_job_status_update(job_id, automl=False, automl_experiment_number="0", message="", logfile=""):
    """Post an status update to the job"""
    data_string = get_internal_job_status_update_data(
        automl_experiment_number=automl_experiment_number,
        message=message
    )
    callback_data = {
        "experiment_number": automl_experiment_number,
        "status": data_string,
    }
    save_dnn_status(job_id, automl=automl, callback_data=callback_data, experiment_number=automl_experiment_number)

    if logfile and os.path.exists(os.path.dirname(logfile)):
        with open(logfile, "a", encoding='utf-8') as f:
            f.write(f"\n{message}\n")


def save_dnn_status(job_id, automl=False, callback_data={}, experiment_number="0", handler_id=None, kind=None):
    """Update DNN status with callback data"""
    lookup_job_id = status_lookup_job_id(
        job_id,
        automl=automl,
        callback_data=callback_data,
        experiment_number=experiment_number
    )
    mongo_status_table_handler = MongoHandler("tao", "job_statuses")
    job_query = {'id': lookup_job_id}
    callback_data_dict = json.loads(callback_data["status"])
    update_job_message(
        handler_id,
        job_id,
        kind,
        callback_data_dict["message"],
        automl_expt_job_id=job_id,
        update_automl_expt=automl)
    mongo_status_table_handler.upsert_append(job_query, callback_data_dict)


def get_dnn_status(job_id, automl=False, experiment_number="0"):
    """Get DNN status contents"""
    lookup_job_id = status_lookup_job_id(job_id, automl=automl, experiment_number=experiment_number)
    mongo_status_table_handler = MongoHandler("tao", "job_statuses")
    job_query = {'id': lookup_job_id}
    status_lines = mongo_status_table_handler.find_one(job_query)
    return status_lines.get("status", [])


def delete_dnn_status(job_id, automl=False, experiment_number="0"):
    """Delete DNN status contents"""
    lookup_job_id = status_lookup_job_id(job_id, automl=automl, experiment_number=experiment_number)
    mongo_status_table_handler = MongoHandler("tao", "job_statuses")
    mongo_status_table_handler.delete_one({'id': lookup_job_id})


def update_job_details_with_microservices_response(error_message, job_id, automl_expt_job_id=None):
    """Update the job's detailed status fields with response from microservices"""
    job_metadata = get_handler_job_metadata(job_id)
    if error_message:
        update_job_id = job_id
        if automl_expt_job_id:
            update_job_id = automl_expt_job_id
        error_message = error_message[error_message.find('Invalid schema'):].split('",')[0]
        if "job_details" not in job_metadata:
            job_metadata["job_details"] = {}
        job_metadata["job_details"][update_job_id] = {
            "detailed_status": {
                "message": error_message,
                "status": "FAILURE"
            }
        }
    # For AutoML just because one experiment failed to launch doesn't mean the brain should be set to error
    if not automl_expt_job_id:
        job_metadata["status"] = "Error"
    write_job_metadata(job_id, job_metadata)


def infer_action_from_job(handler_id, job_id):
    """Takes handler, job_id (UUID / str) and returns action corresponding to that jobID"""
    job_id = str(job_id)
    action = ""
    all_jobs = get_jobs_for_handler(handler_id, "experiment")
    for job in all_jobs:
        if job["id"] == job_id:
            action = job["action"]
            break
    return action


def get_handler_id(job_id):
    """Return handler_id of the provided job"""
    job_metadata = get_handler_metadata(job_id, "jobs")
    for kind in ("experiment", "dataset", "workspace"):
        if f"{kind}_id" in job_metadata:
            return job_metadata[f"{kind}_id"]
    return None


def get_handler_org(handler_id, kind):
    """Return the org for the handler id provided"""
    if kind[-1] != 's':
        kind += 's'
    metadata = get_handler_metadata(handler_id, kind)
    org_name = metadata.get("org_name", None)
    return org_name


def get_handler_kind(handler_metadata):
    """Return the handler type for the handler id provided"""
    # Get the handler_root in all the paths
    if "network_arch" in handler_metadata.keys():
        return "experiments"
    if "cloud_type" in handler_metadata.keys():
        return "workspaces"
    return "datasets"


def get_handler_type(handler_metadata):
    """Return the handler type"""
    network = handler_metadata.get("network_arch", None)
    if not network:
        network = handler_metadata.get("type", None)
    return network


def make_root_dirs(user_id, org_name, kind, handler_id):
    """Create root dir followed by logs, jobs_metadata and specs folder"""
    log_root = os.path.join(get_root(), org_name, "users", user_id, "logs/")
    jobs_meta_root = os.path.join(get_root(), org_name, kind, handler_id, "jobs_metadata/")
    for directory in [log_root, jobs_meta_root]:
        if not os.path.exists(directory):
            os.makedirs(directory)


def check_existence(handler_id, kind):
    """Check if dataset or experiment exists"""
    if kind not in ["dataset", "experiment", "workspace"]:
        return False

    # first check in the base experiments
    if kind == "experiment":
        model_metadata = get_base_experiment_metadata(handler_id)
        if model_metadata:
            return True
    # check in DB
    model_metadata = get_handler_metadata(handler_id, kind)
    if model_metadata:
        return True
    return False


def check_read_access(user_id, org_name, handler_id, base_experiment=False, kind=""):
    """Check if the user has read access to this particular handler"""
    handler_org = get_handler_org(handler_id, kind)

    if base_experiment:
        handler_metadata = get_base_experiment_metadata(handler_id)
    else:
        handler_metadata = get_handler_metadata(handler_id, kind)
    public = handler_metadata.get("public", False)  # Default is False
    shared = handler_metadata.get("shared", False)  # Default is False
    handler_user_id = handler_metadata.get("user_id", "")
    under_user = (handler_org is not None and handler_org == org_name) and (user_id and user_id == handler_user_id)

    # Users can always write to their own files
    # Read-only restrictions only apply to non-owners
    if under_user:
        return True
    if public:
        return True
    if shared:
        return True
    return False


def check_write_access(user_id, org_name, handler_id, base_experiment=False, kind=""):
    """Check if the user has write access to this particular handler"""
    handler_org = get_handler_org(handler_id, kind)
    if base_experiment:
        handler_metadata = get_base_experiment_metadata(handler_id)
    else:
        handler_metadata = get_handler_metadata(handler_id, kind)
    public = handler_metadata.get("public", False)  # Default is False
    read_only = handler_metadata.get("read_only", False)  # Default is False
    handler_user_id = handler_metadata.get("user_id", "")
    under_user = (handler_org is not None and handler_org == org_name) and (user_id and user_id == handler_user_id)
    # If under user, you can always write - no point in making it un-writable by owner. Read-only is for non-owners
    if under_user:
        return True
    if public:
        if read_only:
            return False
        return True
    return False


def get_public_experiments(maxine=False):
    """Get public experiments"""
    # Make sure to check if it exists
    public_experiments_metadata = []
    mongo_experiments = MongoHandler("tao", "experiments")
    base_experiments = mongo_experiments.find({'public': True})
    for base_experiment_metadata in base_experiments:
        if not maxine and base_experiment_metadata.get("network_arch", "").startswith("maxine"):
            continue
        public_experiments_metadata.append(base_experiment_metadata)
    return list(public_experiments_metadata)


def get_public_datasets():
    """Get public datasets"""
    public_datasets = []
    return list(set(public_datasets))


def add_public_experiment(experiment_id):
    """Add public experiment"""
    # if experiment_id in get_public_experiments():
    #     return
    return


def add_public_dataset(dataset_id):
    """Add public dataset"""
    # if dataset_id in get_public_datasets():
    #     return
    return


def remove_public_experiment(experiment_id):
    """Remove public experiment"""
    # if experiment_id not in get_public_experiments():
    #     return
    return


def remove_public_dataset(dataset_id):
    """Remove public dataset"""
    # if dataset_id not in get_public_datasets():
    #     return
    return


def decrypt_handler_metadata(workspace_metadata):
    """Decrypt NvVault encrypted values"""
    config_path = os.getenv("VAULT_SECRET_PATH", None)
    if config_path:
        cloud_specific_details = workspace_metadata.get("cloud_specific_details")
        if cloud_specific_details:
            encryption = NVVaultEncryption(config_path)
            for key, value in cloud_specific_details.items():
                if encryption.check_config()[0]:
                    workspace_metadata["cloud_specific_details"][key] = encryption.decrypt(value)
                else:
                    logger.warning("deencryption not possible")


def get_workspace_string_identifier(workspace_id, workspace_cache):
    """For the given workspace ID, constuct a unique string which can identify this workspace"""
    if workspace_id in workspace_cache:
        workspace_metadata = workspace_cache[workspace_id]
    else:
        workspace_metadata = get_handler_metadata(workspace_id, kind="workspaces")
        decrypt_handler_metadata(workspace_metadata)
        workspace_cache[workspace_id] = workspace_metadata
    workspace_identifier = ""
    if workspace_metadata:
        cloud_type = workspace_metadata.get('cloud_type')
        bucket_name = workspace_metadata.get('cloud_specific_details', {}).get('cloud_bucket_name')
        workspace_identifier = f"{cloud_type}://{bucket_name}/"
    return workspace_identifier


def check_dataset_type_match(user_id, org_name, experiment_meta, dataset_id, no_raw=None):
    """Checks if the dataset created for the experiment is valid dataset_type"""
    # If dataset id is None, then return True
    # Else, if all things match, return True
    # True means replace, False means skip and return a 400 Code
    if dataset_id is None:
        return True
    dataset_meta = get_handler_metadata(dataset_id, "datasets")
    if not dataset_meta:
        return False
    if not check_read_access(user_id, org_name, dataset_id, kind="datasets"):
        return False

    experiment_dataset_type = experiment_meta.get("dataset_type")
    network_arch = experiment_meta.get("network_arch")

    # Allow Image action from dataservices to run on any model's dataset
    if (network_arch == "image" and
            experiment_dataset_type == "not_restricted"):
        return True

    dataset_type = dataset_meta.get("type")
    dataset_format = dataset_meta.get("format")
    if experiment_dataset_type not in (dataset_type, "user_custom"):
        return False

    if no_raw:
        if dataset_format in ("raw", "coco_raw"):
            return False

    return True


def check_experiment_type_match(user_id, org_name, experiment_meta, base_experiment_ids):
    """Checks if the experiment created and base_experiment requested belong to the same network"""
    if base_experiment_ids is None:
        return True
    for base_experiment_id in base_experiment_ids:
        if not check_read_access(user_id, org_name, base_experiment_id, True, kind="experiments"):
            return False

        base_experiment_meta = get_base_experiment_metadata(base_experiment_id)
        if not base_experiment_meta:
            # Search in the base_exp_uuid fails, search in the org_name
            base_experiment_meta = get_handler_metadata(base_experiment_id, "experiments")

        experiment_arch = experiment_meta.get("network_arch")
        base_experiment_arch = base_experiment_meta.get("network_arch")
        if experiment_arch != base_experiment_arch:
            return False

    return True


def check_checkpoint_choose_match(technique):
    """Checks if technique chosen for checkpoint retrieve is a valid option"""
    if technique not in ("best_model", "latest_model", "from_epoch_number"):
        return False
    return True


def check_checkpoint_epoch_number_match(epoch_number_dictionary):
    """Checks if the epoch number requested to retrieve checkpoint is a valid number"""
    try:
        for key in epoch_number_dictionary.keys():
            _ = int(epoch_number_dictionary[key])
    except Exception as e:
        logger.error("Exception thrown in check checkpoint epoch number match is %s", str(e))
        return False
    return True


def check_base_experiment_support_realtime_infer(user_id, org_name, experiment_meta, realtime_infer):
    """Check if the PTM suppport realtime infer"""
    if realtime_infer is None or realtime_infer is False:  # no need to check
        return True

    base_experiment_ids = experiment_meta.get("base_experiment")
    if len(base_experiment_ids) != 1:
        return False
    base_experiment_id = base_experiment_ids[0]

    if not check_existence(base_experiment_id, "experiment"):
        return False

    if not check_read_access(user_id, org_name, base_experiment_id, True, kind="experiments"):
        return False

    base_experiment_meta = get_base_experiment_metadata(base_experiment_id)
    if not base_experiment_meta:
        # Search in the base_exp_uuid fails, search in the user_id
        base_experiment_meta = get_handler_metadata(base_experiment_id, "experiments")
    if not base_experiment_meta.get("realtime_infer_support", False):
        return False

    return True


def experiment_update_handler_attributes(user_id, org_name, experiment_meta, key, value):
    """Checks if the artifact provided is of the correct type"""
    # Returns value or False
    if key in ["train_datasets"]:
        if type(value) is not list:
            value = [value]
        for dataset_id in value:
            if not check_dataset_type_match(user_id, org_name, experiment_meta, dataset_id, no_raw=True):
                return False
    elif key in ["eval_dataset"]:
        if not check_dataset_type_match(user_id, org_name, experiment_meta, value, no_raw=True):
            return False
    elif key in ["calibration_dataset", "inference_dataset"]:
        if not check_dataset_type_match(user_id, org_name, experiment_meta, value):
            return False
    elif key in ["base_experiment"]:
        if not check_experiment_type_match(user_id, org_name, experiment_meta, value):
            return False
    elif key in ["checkpoint_choose_method"]:
        if not check_checkpoint_choose_match(value):
            return False
    elif key in ["checkpoint_epoch_number"]:
        if not check_checkpoint_epoch_number_match(value):
            return False
    elif key in ["realtime_infer"]:
        if not check_base_experiment_support_realtime_infer(user_id, org_name, experiment_meta, value):
            return False
    else:
        return False
    return True


def resolve_existence(kind, handler_id):
    """Check if the handler exists"""
    if kind not in ["dataset", "experiment", "workspace"]:
        return False
    metadata = resolve_metadata(kind, handler_id)
    if not metadata:
        return False
    return True


def resolve_root(org_name, kind, handler_id):
    """Resolve the root path of the handler"""
    return os.path.join(get_root(), org_name, kind + "s", handler_id)


def resolve_metadata(kind, handler_id):
    """Resolve the metadata of the handler"""
    if kind[-1] != 's':
        kind += 's'
    mongo = MongoHandler("tao", kind)
    handler_query = {'id': handler_id}
    metadata = mongo.find_one(handler_query)
    return metadata


def get_latest_ver_folder(tis_model_path):
    """Returns the latest version folder in the model directory"""
    try:
        entries = os.listdir(tis_model_path)

        # Find the maximum numeric value among the folder names
        numeric_folders = [int(folder) for folder in entries if folder.isnumeric()]
        latest_ver = max(numeric_folders)

    except ValueError:
        # If there are no numeric folders, return 0
        return 0

    return latest_ver


def is_valid_uuid4(uuid_string):
    """Check if the string is a valid UUID4"""
    try:
        val = uuid.UUID(uuid_string, version=4)
    except ValueError:
        return False

    # Return True if the UUID is of version 4
    return val.hex == uuid_string.replace('-', '') and val.version == 4


def printc(*args, **kwargs):
    """Print the contexts (uuid/handler_id/job_id) with the message."""
    context = kwargs.pop("context", {})
    if not isinstance(context, dict):
        logger.info(*args, **kwargs)
        return
    keys = kwargs.pop("keys", ["user_id", "handler_id", "id"])
    keys = keys if isinstance(keys, list) else [keys]
    context_str = ""
    for key, value in context.items():
        if key in keys:
            context_str += f"[{key}:{value}]"
    logger.info(context_str, *args, **kwargs)


def sanitize_handler_metadata(handler_metadata):
    """Remove sensitive information like cloud storage credentials to return as response"""
    return_metadata = handler_metadata.copy()
    if "cloud_specific_details" in return_metadata.get("cloud_details", {}):
        for key in ("access_key", "secret_key", "token"):
            return_metadata["cloud_details"]["cloud_specific_details"].pop(key, None)
    return_metadata.pop("client_secret", None)
    return return_metadata


def validate_chained_actions(actions):
    """Returns a list of valid chained actions with parent jobs assigned"""
    completed_tasks_master = []
    job_mapping = []
    for action in actions:
        completed_tasks_itr = copy.deepcopy(completed_tasks_master)
        found = False
        for i in range(len(completed_tasks_itr) - 1, -1, -1):
            parent_job = completed_tasks_itr[i]
            chainable = action in CV_ACTION_RULES and parent_job in CV_ACTION_RULES[action]
            if chainable:
                job_mapping.append({'child': action, 'parent': parent_job})
                completed_tasks_master.append(action)
                found = True
                break
        if not found:
            if action in CV_ACTION_CHAINED_ONLY:
                # Not a valid workflow chaining
                return []
            completed_tasks_master.append(action)
            job_mapping.append({'child': action})
    return job_mapping


def get_all_pending_jobs():
    """Returns a list of all jobs with status of Pending, Running, or Canceling"""
    mongo_jobs = MongoHandler("tao", "jobs")
    job_query = {
        'status': {
            '$in': ['Pending', 'Running', 'Canceling']
        }
    }
    jobs = mongo_jobs.find(job_query)
    return jobs


def get_user(user_id, mongo_users=None):
    """Returns user from DB"""
    if not mongo_users:
        mongo_users = MongoHandler("tao", "users")
    user_query = {'id': user_id}
    user = mongo_users.find_one(user_query)
    return user


def get_job(job_id):
    """Returns job metadata from DB"""
    mongo_jobs = MongoHandler("tao", "jobs")
    job_query = {'id': job_id}
    job = mongo_jobs.find_one(job_query)
    return job


def get_jobs_for_handler(handler_id, kind):
    """Return job metadatas associated with handler_id"""
    if kind[-1] == 's':
        kind = kind[:-1]
    mongo_jobs = MongoHandler("tao", "jobs")
    jobs = mongo_jobs.find({f"{kind}_id": handler_id})
    return jobs


def get_metrics():
    """Return metrics from DB"""
    mongo_metrics = MongoHandler("metrics", "metrics")
    metrics = mongo_metrics.find_one()
    return metrics


def set_metrics(metrics):
    """Set metrics to DB"""
    mongo_metrics = MongoHandler("metrics", "metrics")
    mongo_metrics.upsert({'name': 'metrics'}, metrics)


def get_user_telemetry_opt_out(user_id: str, org_name: str, user_db: MongoHandler = None) -> str:
    """Returns the telemetry opt out setting for a user"""
    # Skip sending telemetry for air-gapped environments
    if os.getenv("AIRGAPPED_MODE", "false").lower() == "true":
        return "yes"

    user = get_user(user_id, user_db)
    enable_telemetry = False
    if user:
        enable_telemetry = user.get("settings", {}).get(org_name, {}).get("enable_telemetry", True)
    return "no" if enable_telemetry else "yes"


def serialize_object(obj):
    """Serialize Database metadata to strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)
