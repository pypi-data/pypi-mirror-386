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

"""Cloud storage fsspec client"""
import os
import copy
import time
import fsspec
import logging
import functools
from datetime import datetime

from nvidia_tao_core.microservices.handlers.encrypt import NVVaultEncryption
from nvidia_tao_core.distributed.decorators import master_node_only

NUM_RETRY = 5

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudStorageCredentialError(Exception):
    """Exception raised for invalid cloud storage credentials."""

    pass


class CloudStorageConnectionError(Exception):
    """Exception raised when unable to connect to cloud storage."""

    pass


def clear_fsspec_caches():
    """Clear all fsspec caches to prevent state corruption."""
    try:
        # Clear fsspec registry caches
        if hasattr(fsspec, 'registry') and hasattr(fsspec.registry, 'clear_cache'):
            fsspec.registry.clear_cache()

        # Clear s3fs specific caches
        try:
            import s3fs
            if hasattr(s3fs, 'S3FileSystem'):
                if hasattr(s3fs.S3FileSystem, 'clear_instance_cache'):
                    s3fs.S3FileSystem.clear_instance_cache()
                if hasattr(s3fs.S3FileSystem, '_cache'):
                    s3fs.S3FileSystem._cache.clear()
            # Clear session pools in s3fs core
            if hasattr(s3fs, 'core') and hasattr(s3fs.core, '_cache'):
                s3fs.core._cache.clear()
        except ImportError:
            pass

        # Clear generic fsspec filesystem caches
        try:
            if hasattr(fsspec, 'filesystem'):
                # Clear any cached filesystem instances
                if hasattr(fsspec.filesystem, '_cache'):
                    fsspec.filesystem._cache.clear()
        except Exception:
            pass

        logger.info("Cleared all fsspec caches")
    except Exception as e:
        logger.warning(f"Could not clear some fsspec caches: {e}")


def reset_storage_state():
    """Reset storage client state to prevent corruption."""
    clear_fsspec_caches()

    # Force garbage collection to clean up any hanging connections
    import gc
    gc.collect()

    logger.info("Reset storage state and caches")


def retry_method(func):
    """Retry Cloud storage methods for NUM_RETRY times"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(NUM_RETRY):
            try:
                if attempt > 0:
                    # Clear caches before retry
                    logger.warning(f"Retrying {func.__name__} attempt {attempt + 1}/{NUM_RETRY}")
                    clear_fsspec_caches()
                    time.sleep(1)
                return func(*args, **kwargs)
            except Exception as e:
                # Log or handle the exception as needed
                logger.error("Exception in %s (attempt %d/%d): %s", func.__name__, attempt + 1, NUM_RETRY, e)
                if attempt == NUM_RETRY - 1:
                    # Last attempt failed
                    raise
        # If all retries fail, raise an exception or handle it accordingly
        raise ValueError(f"Failed to execute {func.__name__} after multiple retries")
    return wrapper


def create_cs_instance_with_decrypted_metadata(decrypted_metadata):
    """Create a cloud storage instance with decrypted metadata"""
    handler_metadata_copy = copy.deepcopy(decrypted_metadata)
    cloud_type = handler_metadata_copy.get("cloud_type", "aws")
    cloud_specific_details = handler_metadata_copy.get("cloud_specific_details", {})
    cloud_bucket_name = cloud_specific_details.get("cloud_bucket_name")

    # Original cloud providers
    cs_instance = None
    if cloud_specific_details and cloud_bucket_name:
        if cloud_type == "aws":
            cs_instance = CloudStorage(
                cloud_type="aws",
                bucket_name=cloud_bucket_name,
                region=cloud_specific_details.get("cloud_region"),
                key=cloud_specific_details.get("access_key"),
                secret=cloud_specific_details.get("secret_key"),
                client_kwargs={"endpoint_url": cloud_specific_details.get("endpoint_url")}
            )
        elif cloud_type == "azure":
            cs_instance = CloudStorage(
                cloud_type="azure",
                bucket_name=cloud_bucket_name,
                region=cloud_specific_details.get("cloud_region"),
                key=cloud_specific_details.get("account_name"),
                secret=cloud_specific_details.get("access_key"),
                client_kwargs={"endpoint_url": cloud_specific_details.get("endpoint_url")}
            )
        elif cloud_type == "seaweedfs":
            return _create_seaweedfs_instance(cloud_specific_details)
        else:
            raise ValueError(f"Unsupported cloud_type: {cloud_type}")

    return cs_instance, cloud_specific_details


def create_cs_instance(handler_metadata):
    """Create a cloud storage instance based on handler metadata

    Args:
        handler_metadata (dict): Metadata containing cloud configuration

    Returns:
        tuple: (CloudStorage instance, cloud_specific_details dict)

    Raises:
        CloudStorageCredentialError: If credentials are invalid
        CloudStorageConnectionError: If unable to connect to cloud storage
        ValueError: If configuration is invalid
    """
    # Clear caches before creating new instance
    clear_fsspec_caches()

    handler_metadata_copy = copy.deepcopy(handler_metadata)
    cloud_type = handler_metadata_copy.get("cloud_type", "aws")
    cloud_specific_details = handler_metadata_copy.get("cloud_specific_details", {})

    # Decrypt cloud details for original cloud providers
    config_path = os.getenv("VAULT_SECRET_PATH", None)
    if config_path:
        encryption = NVVaultEncryption(config_path)
        for key, encrypted_value in cloud_specific_details.items():
            if encryption.check_config()[0]:
                cloud_specific_details[key] = encryption.decrypt(encrypted_value)

    cloud_bucket_name = cloud_specific_details.get("cloud_bucket_name")

    cs_instance = None
    if cloud_specific_details:
        if cloud_type == "aws":
            cs_instance = CloudStorage(
                cloud_type="aws",
                bucket_name=cloud_bucket_name,
                region=cloud_specific_details.get("cloud_region"),
                key=cloud_specific_details.get("access_key"),
                secret=cloud_specific_details.get("secret_key"),
                client_kwargs={"endpoint_url": cloud_specific_details.get("endpoint_url")}
            )
        elif cloud_type == "azure":
            cs_instance = CloudStorage(
                cloud_type="azure",
                bucket_name=cloud_bucket_name,
                region=cloud_specific_details.get("cloud_region"),
                key=cloud_specific_details.get("account_name"),
                secret=cloud_specific_details.get("access_key"),
                client_kwargs={"endpoint_url": cloud_specific_details.get("endpoint_url")}
            )
        elif cloud_type == "seaweedfs":
            cs_instance, _ = _create_seaweedfs_instance(cloud_specific_details)
        else:
            raise ValueError(f"Unsupported cloud_type: {cloud_type}")

    if cs_instance and cloud_bucket_name:
        logger.info(f"Validating {cloud_type} credentials...")
        try:
            # Directly validate the connection using the instance method
            cs_instance.validate_connection()
            logger.info("Credentials validated successfully")
        except (CloudStorageCredentialError, CloudStorageConnectionError) as e:
            logger.error(f"Credential validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during credential validation: {e}")
            raise CloudStorageConnectionError(f"Failed to validate credentials: {e}") from e

    return cs_instance, cloud_specific_details


def _create_seaweedfs_instance(cloud_specific_details):
    """Create a SeaweedFS storage instance"""
    # SeaweedFS configuration with environment variable fallbacks
    endpoint = cloud_specific_details.get("endpoint_url", "http://seaweedfs-s3:8333")
    bucket_name = cloud_specific_details.get("cloud_bucket_name", "tao-storage")
    access_key = cloud_specific_details.get("access_key", "")
    secret_key = cloud_specific_details.get("secret_key", "")
    region = cloud_specific_details.get("cloud_region", "us-east-1")

    # Create SeaweedFS-compatible storage instance
    seaweedfs_instance = CloudStorage(
        cloud_type="seaweedfs",
        bucket_name=bucket_name,
        region=region,
        key=access_key,
        secret=secret_key,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': endpoint,
            'addressing_style': 'path'
        }
    )

    return seaweedfs_instance, cloud_specific_details


def get_date_time():
    """Get current date and time"""
    now = datetime.now()
    return now.strftime("%m/%d/%Y"), now.strftime("%H:%M:%S")


class CloudStorage:
    """Cloud storage CRUD operations using fsspec for S3, Azure, and SeaweedFS."""

    @retry_method
    def __init__(self, cloud_type, bucket_name, region=None, **kwargs):
        """Initialize the CloudStorage object.

        cloud_type: 'aws', 'azure', or 'seaweedfs'.
        bucket_name: Name of the bucket/container.
        region: Region for the cloud storage provider.
        kwargs: Additional arguments for fsspec.filesystem
        """
        # Clear caches before creating filesystem
        clear_fsspec_caches()

        self.cloud_type = cloud_type
        self.bucket_name = bucket_name
        self.region = region
        self.fs = None

        # Prepare client_kwargs with region if provided
        if 'client_kwargs' not in kwargs:
            kwargs['client_kwargs'] = {}
        if region:
            kwargs['client_kwargs']['region_name'] = region

        # Configure for reliability - disable filesystem caching
        fsspec_config = {
            'use_listings_cache': False,  # Disable listings cache
            'listings_expiry_time': 0,    # Immediately expire any cached listings
            'skip_instance_cache': True   # Skip fsspec instance caching
        }

        if cloud_type == 'aws':
            # Merge fsspec config with user kwargs
            aws_kwargs = {**kwargs, **fsspec_config}
            self.fs = fsspec.filesystem('s3', **aws_kwargs)
            self.root = f'{bucket_name}/'
        elif cloud_type == 'azure':
            # Merge fsspec config with user kwargs
            azure_kwargs = {**kwargs, **fsspec_config}
            self.fs = fsspec.filesystem('az', **azure_kwargs)
            self.root = f'{bucket_name}/'
        elif cloud_type == 'seaweedfs':
            # SeaweedFS uses S3-compatible API
            fsspec_kwargs = kwargs.copy()
            client_kwargs = fsspec_kwargs.pop('client_kwargs', {})

            # Use client_kwargs approach for maximum compatibility (works in both local and Docker)
            if client_kwargs:
                # Filter out incompatible parameters like 'addressing_style'
                client_kwargs_filtered = {
                    k: v for k, v in client_kwargs.items()
                    if k != 'addressing_style'
                }
                if client_kwargs_filtered:
                    fsspec_kwargs['client_kwargs'] = client_kwargs_filtered

            # Merge fsspec config for SeaweedFS reliability
            seaweedfs_kwargs = {**fsspec_kwargs, **fsspec_config}

            self.fs = fsspec.filesystem('s3', **seaweedfs_kwargs)
            self.root = f'{bucket_name}/'
        else:
            raise ValueError("Unsupported cloud_type. Use 'aws', 'azure', or 'seaweedfs'.")

    def reset_filesystem_state(self):
        """Reset the filesystem state to clear any corrupted caches."""
        try:
            # Clear filesystem-specific caches
            if hasattr(self.fs, 'invalidate_cache'):
                self.fs.invalidate_cache()
            if hasattr(self.fs, '_cache') and hasattr(self.fs._cache, 'clear'):
                self.fs._cache.clear()

            # Clear global fsspec caches
            clear_fsspec_caches()

            logger.info("Filesystem state reset complete")
        except Exception as e:
            logger.warning(f"Error resetting filesystem state: {e}")

    def validate_connection(self):
        """Validate the connection to cloud storage by performing a basic operation.

        Raises:
            CloudStorageCredentialError: If credentials are invalid
            CloudStorageConnectionError: If unable to connect to cloud storage
        """
        try:
            # Test basic connectivity by listing the bucket
            bucket_path = f"{self.bucket_name}/"
            self.fs.ls(bucket_path, detail=False)
            logger.info(f"Successfully validated connection to {self.cloud_type} bucket: {self.bucket_name}")
        except Exception as e:
            error_msg = str(e).lower()
            if "nosuchbucket" in error_msg or "containernotfound" in error_msg or "does not exist" in error_msg:
                raise CloudStorageConnectionError(
                    f"Bucket/container '{self.bucket_name}' does not exist or is not accessible"
                ) from e
            if any(keyword in error_msg for keyword in [
                "invalidaccesskeyid", "signaturedoesnotmatch", "authenticationfailed", "unauthorized", "forbidden"
            ]):
                raise CloudStorageCredentialError(
                    f"Invalid credentials for {self.cloud_type}: {str(e)}"
                ) from e
            raise CloudStorageConnectionError(
                f"Failed to connect to {self.cloud_type}: {str(e)}"
            ) from e

    @retry_method
    def is_file(self, cloud_path):
        """Check if the given cloud path is a file."""
        full_path = self.root + cloud_path.strip('/')
        try:
            return self.fs.isfile(full_path)
        except Exception as e:
            logger.error(f"is_file error: {e}")
            return False

    @retry_method
    def is_folder(self, cloud_path):
        """Check if the given cloud path is a folder."""
        full_path = self.root + cloud_path.strip('/') + '/'
        try:
            return self.fs.isdir(full_path)
        except Exception as e:
            logger.error(f"is_folder error: {e}")
            return False

    @retry_method
    def glob_files(self, pattern):
        """Return a list of files matching the pattern."""
        full_pattern = self.root + pattern
        try:
            return [p[len(self.root):] for p in self.fs.glob(full_pattern) if self.fs.isfile(p)]
        except Exception as e:
            logger.error(f"glob_files error: {e}")
            return []

    @retry_method
    def list_files_in_folder(self, folder):
        """Recursively list files in the specified folder and its subfolders."""
        try:
            # Normalize folder path
            folder_normalized = folder.strip('/')
            full_path = self.root + folder_normalized + '/' if folder_normalized else self.root

            # Clear filesystem cache before operation for SeaweedFS
            if self.cloud_type == 'seaweedfs':
                try:
                    if hasattr(self.fs, 'invalidate_cache'):
                        self.fs.invalidate_cache()
                    if hasattr(self.fs, '_cache') and hasattr(self.fs._cache, 'clear'):
                        self.fs._cache.clear()
                except Exception as cache_err:
                    logger.warning(f"Could not clear filesystem cache: {cache_err}")

            # Use fsspec for all cloud providers (unified approach)
            all_paths = self.fs.find(full_path)
            logger.info(f"Found {len(all_paths)} paths total")

            file_names = []
            for p in all_paths:
                try:
                    if self.fs.isfile(p):
                        file_names.append(p[len(self.root):])
                except Exception as file_check_err:
                    logger.warning(f"Error checking if {p} is file: {file_check_err}")

            logger.info(f"Found {len(file_names)} files: {file_names[:5]}{'...' if len(file_names) > 5 else ''}")
            return file_names, []  # Details not available recursively
        except Exception as e:
            logger.error(f"list_files_in_folder error: {e}")
            return [], []

    @retry_method
    def download_file(self, cloud_file_path, local_destination):
        """Download a file from cloud storage to local destination."""
        full_path = self.root + cloud_file_path.strip('/')
        try:
            if os.path.exists(local_destination):
                logger.info(f"File {local_destination} already exists, skipping download")
                return
            self.fs.download(full_path, local_destination)
            logger.info(f"Downloaded {cloud_file_path} to {local_destination}")
        except Exception as e:
            logger.error(f"download_file error: {e}")
            raise

    @retry_method
    def download_folder(self, cloud_folder, local_destination, maintain_src_folder_structure=False):
        """Download a folder from cloud storage to local destination."""
        # Normalize path to avoid double slashes
        cloud_folder_normalized = cloud_folder.strip('/')
        full_path = self.root + cloud_folder_normalized + '/' if cloud_folder_normalized else self.root

        try:
            # Use fsspec for all cloud providers (unified approach)
            if maintain_src_folder_structure:
                if os.path.exists(local_destination):
                    logger.info(f"Folder {local_destination} already exists, skipping download")
                    return
                # Download maintaining the source folder structure
                self.fs.download(full_path, local_destination, recursive=True)
            else:
                # Download contents without the source folder structure
                files = self.fs.find(full_path)
                os.makedirs(local_destination, exist_ok=True)
                for file_path in files:
                    if self.fs.isfile(file_path):
                        relative_path = file_path[len(full_path):]
                        local_file_path = os.path.join(local_destination, relative_path)
                        if os.path.exists(local_file_path):
                            logger.info(
                                f"File {local_file_path} in folder {local_destination} "
                                f"already exists, skipping download"
                            )
                            continue
                        # Create directory if needed
                        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                        self.fs.download(file_path, local_file_path)
                        logger.debug(f"Downloaded {file_path} to {local_file_path}")

            logger.info(f"Downloaded folder {cloud_folder} to {local_destination} using fsspec")
        except Exception as e:
            logger.error(f"download_folder error: {e}")
            raise

    @retry_method
    @master_node_only
    def create_folder_in_bucket(self, folder):
        """Create a folder in the bucket."""
        full_path = self.root + folder.rstrip('/') + '/'
        try:
            # Create an empty object to represent the folder
            self.fs.makedirs(full_path, exist_ok=True)
            logger.info(f"Created folder {folder}")
        except Exception as e:
            logger.error(f"create_folder_in_bucket error: {e}")
            raise

    @retry_method
    @master_node_only
    def upload_file(self, local_file_path, cloud_file_path):
        """Upload a file from local storage to cloud."""
        full_path = self.root + cloud_file_path.strip('/')
        try:
            self.fs.upload(local_file_path, full_path)
            logger.info(f"Uploaded {local_file_path} to {cloud_file_path}")
        except Exception as e:
            logger.error(f"upload_file error: {e}")
            raise

    @retry_method
    @master_node_only
    def upload_folder(self, local_folder, cloud_subfolder):
        """Upload a folder from local storage to cloud."""
        full_path = self.root + cloud_subfolder.strip('/').rstrip('/') + '/'
        try:
            self.fs.upload(local_folder, full_path, recursive=True)
            logger.info(f"Uploaded folder {local_folder} to {cloud_subfolder}")
        except Exception as e:
            logger.error(f"upload_folder error: {e}")
            raise

    @retry_method
    @master_node_only
    def delete_folder(self, folder):
        """Delete a folder and its contents from cloud storage."""
        full_path = self.root + folder.strip('/').rstrip('/') + '/'
        try:
            self.fs.rm(full_path, recursive=True)
            logger.info(f"Deleted folder {folder}")
        except Exception as e:
            logger.error(f"delete_folder error: {e}")
            raise

    @retry_method
    @master_node_only
    def delete_file(self, file_path):
        """Delete a file from cloud storage."""
        full_path = self.root + file_path.strip('/')
        try:
            self.fs.rm(full_path)
            logger.info(f"Deleted file {file_path}")
        except Exception as e:
            logger.error(f"delete_file error: {e}")
            raise

    @retry_method
    @master_node_only
    def move_file(self, source_path, destination_path):
        """Move a file within cloud storage."""
        full_source = self.root + source_path.strip('/')
        full_destination = self.root + destination_path.strip('/')
        try:
            self.fs.mv(full_source, full_destination)
            logger.info(f"Moved {full_source} to {full_destination}")
        except Exception as e:
            logger.error(f"move_file error: {e}")
            raise

    @retry_method
    @master_node_only
    def move_folder(self, source_path, destination_path):
        """Move a folder within cloud storage."""
        full_source = self.root + source_path.strip('/').rstrip('/') + '/'
        full_destination = self.root + destination_path.strip('/').rstrip('/') + '/'

        try:
            logger.info(f"Moving folder {full_source} to {full_destination}")

            # Get all files in source
            all_files = self.fs.find(full_source)
            files_only = [f for f in all_files if self.fs.isfile(f)]

            logger.info(f"Attempting to move {len(files_only)} files individually")

            # Create destination directory
            self.fs.makedirs(full_destination, exist_ok=True)

            # Move files one by one
            moved_files = 0
            for file_path in files_only:
                try:
                    relative_path = file_path[len(full_source):]
                    dest_file = full_destination + relative_path

                    # Create intermediate directories if needed
                    dest_dir = '/'.join(dest_file.split('/')[:-1])
                    if dest_dir:
                        self.fs.makedirs(dest_dir, exist_ok=True)

                    # Copy then delete individual file
                    self.fs.cp(file_path, dest_file)
                    self.fs.rm(file_path)
                    moved_files += 1

                except Exception as file_err:
                    logger.warning(f"Could not move file {file_path}: {file_err}")

            if moved_files > 0:
                try:
                    self.fs.rm(full_source, recursive=True)
                except Exception:
                    logger.warning("Could not remove source directory after file moves")

                logger.info(f"Successfully moved {moved_files} files using file-by-file approach")
            else:
                raise Exception("No files could be moved using any method")
        except Exception as e:
            logger.error(f"move_folder error: {e}")
            raise

    @retry_method
    @master_node_only
    def copy_file(self, source_object_name, destination_object_name):
        """Copy a file within cloud storage."""
        full_source = self.root + source_object_name.strip('/')
        full_destination = self.root + destination_object_name.strip('/')
        try:
            self.fs.cp(full_source, full_destination)
            logger.info(f"Copied {source_object_name} to {destination_object_name}")
        except Exception as e:
            logger.error(f"copy_file error: {e}")
            raise

    @retry_method
    @master_node_only
    def copy_folder(self, source_path, destination_path):
        """Copy a folder within cloud storage."""
        full_source = self.root + source_path.strip('/').rstrip('/') + '/'
        full_destination = self.root + destination_path.strip('/').rstrip('/') + '/'
        try:
            self.fs.cp(full_source, full_destination, recursive=True)
            logger.info(f"Copied folder {source_path} to {destination_path}")
        except Exception as e:
            logger.error(f"copy_folder error: {e}")
            raise

    @retry_method
    def search_for_ptm(self, root="", network="", parameter_name=""):
        """Return path of the PTM file under the PTM root folder (cloud version)"""
        try:
            # Normalize root path
            root_normalized = root.strip('/')
            search_path = root_normalized + '/' if root_normalized else ''

            # Search for common model file extensions (mimic utils.py)
            models = []
            models.extend(self.glob_files(search_path + "**/*.tlt"))
            models.extend(self.glob_files(search_path + "**/*.hdf5"))
            models.extend(self.glob_files(search_path + "**/*.pth"))
            models.extend(self.glob_files(search_path + "**/*.pth.tar"))
            models.extend(self.glob_files(search_path + "**/*.pt"))

            # Special cases for specific networks (mimic utils.py)
            if network in ("classification_pyt", "visual_changenet_classify", "visual_changenet_segment", "nvdinov2"):
                models.extend(self.glob_files(search_path + "**/*.ckpt"))

            if network == "stylegan_xl":
                if parameter_name == "inception_fid_path":
                    models.extend(self.glob_files(search_path + "**/*Inception*.pth"))
                if parameter_name == "input_embeddings_path":
                    models.extend(self.glob_files(search_path + "**/*tf_efficientnet*.pth"))

            if models:
                model_path = models[0]  # pick one arbitrarily
                logger.info(f"Found valid PTM at {model_path}")
                return model_path

            # If no models found but root exists, handle special cases
            if self.is_folder(root_normalized):
                if network == "vila":
                    # For vila, return first item in directory
                    files, dirs = self.list_files_in_folder(root_normalized)
                    if files:
                        return files[0]
                    if dirs:
                        return dirs[0]
                return root_normalized

            logger.info("PTM can't be found")
            return None

        except Exception as e:
            logger.error(f"search_for_ptm error: {e}")
            return None
