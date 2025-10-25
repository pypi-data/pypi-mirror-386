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

"""Tensorboard handler."""

import json
import os
from time import sleep
from copy import deepcopy
import logging
import sysconfig

from nvidia_tao_core.microservices.constants import TENSORBOARD_EXPERIMENT_LIMIT
from nvidia_tao_core.microservices.handlers.mongo_handler import MongoHandler
from nvidia_tao_core.microservices.handlers.stateless_handlers import get_user, get_handler_metadata, serialize_object
from nvidia_tao_core.microservices.handlers.utilities import Code, decrypt_handler_metadata
from nvidia_tao_core.microservices.handlers.docker_images import DOCKER_IMAGE_MAPPER
from nvidia_tao_core.microservices.job_utils import executor as jobDriver

release_name = os.getenv("RELEASE_NAME", 'tao-api')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TensorboardHandler:
    """Handler class for managing Tensorboard Services.

    This class provides methods to start, stop, and manage
    Tensorboard services tied to experiments.

    - `start`: Starts a Tensorboard service for an experiment.
    - `stop`: Stops a running Tensorboard service for an experiment.
    - `start_tb_service`: Helper to start the Tensorboard service component.
    - `add_to_user_metadata`: Increments the Tensorboard experiment count.
    - `remove_from_user_metadata`: Decrements the Tensorboard experiment count.
    - `check_user_metadata`: Verifies if a user can start more Tensorboard experiments.
    """

    @staticmethod
    def start(org, experiment_id, user_id, workspace_id, replicas=1):
        """Start Tensorboard service for a given experiment."""
        logger.info(f'Starting Tensorboard Service for experiment {experiment_id}')
        tb_deployment_name = f'{release_name}-tb-deployment-{experiment_id}'
        tb_service_name = f"{release_name}-tb-service-{experiment_id}"
        tb_ingress_name = f'{release_name}-tb-ingress-{experiment_id}'
        tb_ingress_path = f'/tensorboard/v1/orgs/{org}/experiments/{experiment_id}'
        command = f"tensorboard --logdir /tfevents --bind_all --path_prefix={tb_ingress_path}"
        workspace_metadata = get_handler_metadata(workspace_id, "workspaces")
        decrypted_workspace_metadata = deepcopy(workspace_metadata)
        decrypt_handler_metadata(decrypted_workspace_metadata)
        decrypted_workspace_metadata.pop('_id', None)
        python_lib_path = sysconfig.get_path('purelib')
        tensorboard_script_path = os.path.join(python_lib_path, "nvidia_tao_core/microservices/tb_events_pull_start.py")
        logs_command = (
            f"umask 0 && python3 {tensorboard_script_path} "
            f"--experiment_id={experiment_id} "
            f"--org_name={org} "
            f"--decrypted_workspace_metadata='{json.dumps(decrypted_workspace_metadata, default=serialize_object)}'"
        )
        tb_image = DOCKER_IMAGE_MAPPER["tensorboard"]
        logs_image = DOCKER_IMAGE_MAPPER["API"]
        jobDriver.create_tensorboard_deployment(
            tb_deployment_name,
            tb_image,
            command,
            logs_image,
            logs_command,
            replicas=replicas
        )
        timeout = 120
        not_ready_log = False
        logger.info("Check deployment status")
        while (timeout > 0):
            stat_dict = jobDriver.status_tensorboard_deployment(tb_deployment_name, replicas=replicas)
            status = stat_dict.get("status", "Unknown")
            if status == "Running":
                logger.info(f"Deployed Tensorboard for {experiment_id}")
                TensorboardHandler.add_to_user_metadata(user_id)
                return TensorboardHandler.start_tb_service(
                    tb_service_name,
                    deploy_label=tb_deployment_name,
                    tb_ingress_name=tb_ingress_name,
                    tb_ingress_path=tb_ingress_path
                )
            if status == "ReplicaNotReady" and not_ready_log is False:
                logger.warning("TensorboardService is deployed but replica not ready.")
                not_ready_log = True
            sleep(1)
            timeout -= 1
        logger.error(f"Failed to deploy Tensorboard {experiment_id}")
        return Code(500, {}, f"Timeout Error: Tensorboard status: {status} after {timeout} seconds")

    @staticmethod
    def stop(experiment_id, user_id):
        """Stop a running Tensorboard service for a given experiment."""
        logger.info(f"Stopping Tensorboard job for {experiment_id}")
        deployment_name = f'{release_name}-tb-deployment-{experiment_id}'
        tb_service_name = f"{release_name}-tb-service-{experiment_id}"
        tb_ingress_name = f'{release_name}-tb-ingress-{experiment_id}'
        jobDriver.delete_tensorboard_deployment(deployment_name)
        jobDriver.delete_tensorboard_service(tb_service_name)
        jobDriver.delete_tensorboard_ingress(tb_ingress_name)
        TensorboardHandler.remove_from_user_metadata(user_id)
        return Code(200, {}, "Delete Tensorboard Started")

    @staticmethod
    def start_tb_service(tb_service_name, deploy_label, tb_ingress_name, tb_ingress_path):
        """Start the Tensorboard service component."""
        jobDriver.create_tensorboard_service(tb_service_name, deploy_label)
        timeout = 60
        logger.info("Check TB Service status")
        not_ready_log = False
        while (timeout > 0):
            service_stat_dict = jobDriver.status_tb_service(tb_service_name)
            service_status = service_stat_dict.get("status", "Unknown")
            if service_status == "Running":
                jobDriver.create_tensorboard_ingress(tb_service_name, tb_ingress_name, tb_ingress_path)
                tb_service_ip = service_stat_dict.get("tb_service_ip", None)
                logger.info(f"Created Tensorboard service {tb_service_name} at {tb_service_ip}")
                return Code(200, "Created Tensorboard Service")
            if service_status == "NotReady" and not_ready_log is False:
                logger.warning("TB Service is started but not ready.")
                not_ready_log = True
            sleep(1)
            timeout -= 1
        logger.error(f"Failed to create Tensorboard service {tb_service_name}")
        return Code(500, {}, f"Error: Tensorboard service status: {service_status}")

    @staticmethod
    def add_to_user_metadata(user_id):
        """Increment the Tensorboard experiment count for a user."""
        mongo_users = MongoHandler("tao", "users")
        user_metadata = get_user(user_id, mongo_users)
        tensorboard_experiment_count = user_metadata.get("tensorboard_experiment_count", 0)
        tensorboard_experiment_count += 1
        user_metadata["tensorboard_experiment_count"] = tensorboard_experiment_count
        mongo_users.upsert({'id': user_id}, user_metadata)
        logger.info(
            f"Number of Tensorboard Experiments for user {user_id} is {tensorboard_experiment_count}"
        )

    @staticmethod
    def remove_from_user_metadata(user_id):
        """Decrement the Tensorboard experiment count for a user."""
        mongo_users = MongoHandler("tao", "users")
        user_metadata = get_user(user_id, mongo_users)
        tensorboard_experiment_count = user_metadata.get("tensorboard_experiment_count", 0)
        if tensorboard_experiment_count > 0:
            tensorboard_experiment_count -= 1
            user_metadata["tensorboard_experiment_count"] = tensorboard_experiment_count
            mongo_users.upsert({'id': user_id}, user_metadata)
            logger.info(
                f"Number of Tensorboard Experiments for user {user_id} is {tensorboard_experiment_count}"
            )

    @staticmethod
    def check_user_metadata(user_id):
        """Check if a user can create additional Tensorboard experiments."""
        user_metadata = get_user(user_id)
        tensorboard_experiment_count = user_metadata.get("tensorboard_experiment_count", 0)
        return tensorboard_experiment_count < TENSORBOARD_EXPERIMENT_LIMIT
