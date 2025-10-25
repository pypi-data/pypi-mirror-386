#!/usr/bin/env python3

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

"""Start Tensorboard Events pulling from cloud storage"""
import argparse
import json
from time import sleep
import os
import logging
from datetime import datetime, timezone

from nvidia_tao_core.microservices.handlers.stateless_handlers import get_handler_metadata_with_jobs
from nvidia_tao_core.microservices.handlers.utilities import filter_file_objects
from nvidia_tao_core.microservices.handlers.cloud_storage import create_cs_instance_with_decrypted_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def pull_tf_events(results_dir, action, cs_instance, experiment_id):
    """Function to pull .tfevents from cloud to local path"""
    tf_events_path = results_dir + "/" + action
    tf_events_path = tf_events_path.lstrip('/')
    if cs_instance.is_folder(tf_events_path):
        _, objects = cs_instance.list_files_in_folder(tf_events_path)
        tf_events_objects = filter_file_objects(objects, regex_pattern=r'.*\.tfevents.+$')
        if len(tf_events_objects) == 0:
            logger.info("No tfevents files present in %s", tf_events_path)
        for obj in tf_events_objects:
            file = obj.name
            basename = os.path.basename(file)
            destination = f'/tfevents/{action}/{basename}'
            if not os.path.exists(destination):
                cs_instance.download_file(file, destination)
                logger.info("Downloaded tfevents file to %s", destination)
            else:
                current_last_modified = os.path.getmtime(destination)
                if hasattr(obj, 'last_modified'):
                    obj_last_modified = obj.last_modified
                else:
                    obj_last_modified = obj.extra['last_modified']
                date_obj = datetime.strptime(obj_last_modified, '%Y-%m-%dT%H:%M:%S.%fZ')
                timestamp_float = date_obj.replace(tzinfo=timezone.utc).timestamp()
                if timestamp_float > current_last_modified:
                    logger.info("File has been modified, downloading file now")
                    cs_instance.download_file(file, destination)
                    logger.info("Downloaded tfevents file to %s", destination)
    else:
        logger.warning(
            "Path %s does not exist in cloud storage for experiment %s",
            tf_events_path,
            experiment_id
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Tensorboard Events Controller',
        description='Periodically pull tfevents files from cloud storage'
    )
    parser.add_argument(
        '--experiment_id',
        type=str,
    )
    parser.add_argument(
        '--org_name',
        type=str,
    )
    parser.add_argument(
        '--decrypted_workspace_metadata',
        type=json.loads,
    )
    args = parser.parse_args()
    experiment_id = args.experiment_id
    org_name = args.org_name
    decrypted_workspace_metadata = args.decrypted_workspace_metadata
    cs_instance, _ = create_cs_instance_with_decrypted_metadata(decrypted_workspace_metadata)

    if not cs_instance:
        logger.error(
            "Unable to create cloud storage instance for Tensorboard Events Pull for experiment %s",
            experiment_id
        )
    else:
        logger.info("Starting Tensorboard Events Pull for experiment %s", experiment_id)
    while cs_instance is not None:
        sleep(30)
        handler_metadata = get_handler_metadata_with_jobs(experiment_id, "experiment")
        automl_enabled = handler_metadata.get("automl_settings", {}).get("automl_enabled", False)
        results_root = "/results"
        jobs = handler_metadata.get("jobs", [])
        if len(jobs) == 0:
            logger.info("No jobs found for experiment %s", experiment_id)
            continue
        for job in jobs:
            action = job.get('action', None)
            job_id = job.get('id', None)
            if action and job_id:
                if automl_enabled:
                    job_details = job.get('job_details', {})
                    if not job_details:
                        logger.info("No jobs found for AutoML experiment %s", experiment_id)
                        continue
                    for automl_job_id in job_details:
                        results_dir = os.path.join(results_root, automl_job_id)
                        pull_tf_events(results_dir, action, cs_instance, experiment_id)
                else:
                    results_dir = os.path.join(results_root, job_id)
                    pull_tf_events(results_dir, action, cs_instance, experiment_id)
