# Copyright 2025 CS Group
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

"""
This module contains the code that is related to dask and/or sent to the dask workers.
Avoid import unnecessary dependencies here.
"""
import ast
import importlib
import json
import logging
import os
import os.path as osp
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from dataclasses import dataclass
from datetime import timedelta
from importlib import reload
from pathlib import Path
from typing import Any

import yaml
from distributed.client import Client as DaskClient
from opentelemetry.trace.span import SpanContext

from rs_dpr_service.utils import init_opentelemetry, settings
from rs_dpr_service.utils.settings import ExperimentalConfig

SERVICE_NAME = "rs.dpr.dask"

# Don't use rs_dpr_service.utils.logging, it's not forwarded to the client
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_ip_address() -> str:
    """Return IP address, see: https://stackoverflow.com/a/166520"""
    return socket.gethostbyname(socket.gethostname())


def upload_this_module(dask_client: DaskClient):
    """
    Upload this current module from the caller environment to the dask client.

    WARNING: These modules should not import other modules that are not installed in the dask
    environment or you'll have import errors.

    Args:
        clients: list of dask clients to which upload the modules.
    """
    # Root of the current project
    root = Path(__file__).parent.parent

    # Files and dirs to upload and associated name in the zip archive
    files = {
        root / "__init__.py": "rs_dpr_service/__init__.py",
        root / "safe_to_zarr.py": "rs_dpr_service/safe_to_zarr.py",
        root / "dask/__init__.py": "rs_dpr_service/dask/__init__.py",
        root / "dask/call_dask.py": "rs_dpr_service/dask/call_dask.py",
        root / "utils/__init__.py": "rs_dpr_service/utils/__init__.py",
        root / "utils/init_opentelemetry.py": "rs_dpr_service/utils/init_opentelemetry.py",
        root / "utils/logging.py": "rs_dpr_service/utils/logging.py",
        root / "utils/settings.py": "rs_dpr_service/utils/settings.py",
    }

    # From a temp dir
    with tempfile.TemporaryDirectory() as tmpdir:

        # Create a zip with our files
        zip_path = f"{tmpdir}/{root.name}.zip"
        with zipfile.ZipFile(zip_path, "w") as zipped:

            # Zip all files
            for key, value in files.items():
                zipped.write(str(key), str(value))

        # Upload zip file to dask clients.
        # This also installs the zipped modules inside the dask python interpreter.
        try:
            dask_client.upload_file(zip_path)

        # We have this error if we scale up the number of workers.
        # But it's OK, the zip file is automatically uploaded to them anyway.
        except KeyError as e:
            logger.debug(f"Ignoring error {e}")


@dataclass
class ClusterInfo:
    """
    Information to connect to a DPR Dask cluster.

    Attributes:
        jupyter_token: JupyterHub API token. Only used in cluster mode, not local mode.
        cluster_label: Dask cluster label e.g. "dask-l0"
        cluster_instance: Dask cluster instance ID (something like "dask-gateway.17e196069443463495547eb97f532834").
        If instance is empty, the DPR processor will use the first cluster with the given label.
    """

    jupyter_token: str
    cluster_label: str
    cluster_instance: str | None = ""


def convert_safe_to_zarr(cfg):
    """
    Convert from legacy product (safe format) into Zarr format using EOPF in a subprocess.

    This runs the rs_dpr_service.safe_to_zarr module as a subprocess, passing config as JSON string.
    """

    # Serialize the config
    cfg_str = json.dumps(cfg)

    # Find the ZIP that this code lives in
    module_path = Path(__file__).resolve()
    zip_path = Path(str(module_path).split(".zip", maxsplit=1)[0] + ".zip")
    if not zip_path.is_file():
        raise RuntimeError(f"Cannot locate rs_dpr_service.zip at {zip_path}")

    # Prepare an env that lets Python import from inside the ZIP
    env = os.environ.copy()
    # prepend the zip onto PYTHONPATH (so zipimport will kick in)
    env["PYTHONPATH"] = str(zip_path) + os.pathsep + env.get("PYTHONPATH", "")

    # Run the converter as a module
    cmd = [sys.executable, "-m", "rs_dpr_service.safe_to_zarr", cfg_str]
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Conversion failed: {result.stderr.strip()}")
    return result.stdout.strip()


class ProcessorCaller:
    """
    Run the DPR processor.

    NOTE: All methods except __init__ are run from the dask pod.
    """

    def __init__(
        self,
        caller_env: dict[str, str],
        span_context: SpanContext,
        cluster_address: str,
        cluster_info: ClusterInfo,
        data: dict,
        use_mockup: bool,
    ):
        """
        Constructor.

        Attributes:
            caller_env: env variables coming from the caller
            span_context: OpenTelemetry caller span context
            cluster_address: Dask Gateway address
            cluster_info: Information to connect to a DPR Dask cluster.
            data: data to send to the processor
            use_mockup: use the mockup or real processor
            s3: Bucket access to read/write configuration and report files
            local_report_dir: Report directory on the local disk
            s3_report_dir: Report directory on the S3 bucket
            experimental_config: Experimental configuration, used only for testing
            payload_contents: Payload file contents
            command: Command used to trigger eopf-cpm
            log_path: Path of the logging file on local disk
            working_dir: Working directory on local disk
            to_be_uploaded: Output products to be uploaded to the s3 bucket at the end of the processor
            exec_times: Execution times with their description
            mockup_return_value: Mockup return value
        """
        # NOTE: some imports exists in the dask worker environment, not in the rs-dpr-service env,
        # so we cannot import them from the top of this module.
        import s3fs  # pylint: disable=import-outside-toplevel

        # This should run on the rs-dpr-service container
        logger.debug(f"Call 'ProcessorCaller.__init__' from {get_ip_address()!r}")

        self.caller_env: dict = caller_env
        self.span_context = span_context
        self.cluster_address: str = cluster_address
        self.cluster_info: ClusterInfo = cluster_info
        self.data: dict = data
        self.use_mockup: bool = use_mockup
        self.s3: Any | None = None  # AnyPath
        self.local_report_dir: str = ""
        self.s3_report_dir: str = ""
        self.experimental_config: ExperimentalConfig | None = None
        self.payload_contents: dict = {}
        self.command: list = []
        self.log_path: str = ""
        self.working_dir: str = ""
        self.to_be_uploaded: list[tuple[s3fs.S3FileSystem, str, str]] = []
        self.exec_times: list[tuple[str, float]] = []
        self.mockup_return_value: dict = {}

    def copy_caller_env(self):
        """
        Copy environment variables from the calling service environment to the dask client.
        This function is run from inside the dask pod.
        """
        local_mode = self.caller_env.get("RSPY_LOCAL_MODE") == "1"

        # Copy env vars from the caller
        keys = [
            "RSPY_LOCAL_MODE",
            "S3_ACCESSKEY",
            "S3_SECRETKEY",
            "S3_ENDPOINT",
            "S3_REGION",
            "PREFECT_BUCKET_NAME",
            "PREFECT_BUCKET_FOLDER",
            "AWS_REQUEST_CHECKSUM_CALCULATION",
            "AWS_RESPONSE_CHECKSUM_VALIDATION",
            "TEMPO_ENDPOINT",
            "OTEL_PYTHON_REQUESTS_TRACE_HEADERS",
            "OTEL_PYTHON_REQUESTS_TRACE_BODY",
        ]

        if local_mode:
            keys.extend(
                [
                    "LOCAL_DASK_USERNAME",
                    "LOCAL_DASK_PASSWORD",
                    "access_key",
                    "bucket_location",
                    "host_base",
                    "host_bucket",
                    "secret_key",
                ],
            )

        for key in keys:
            if value := self.caller_env.get(key):
                os.environ[key] = value

        # Reload this module to read updated env vars (local/cluster mode)
        reload(settings)

        # Init AWS env
        self.set_aws_env()

    def set_aws_env(self):
        """Init the AWS environment variables from the bucket credentials."""

        # In local mode, the env vars are read from the ~/.s3cfg
        # config file, that contains access to the "real" s3 bucket
        if settings.LOCAL_MODE:
            os.environ["AWS_ACCESS_KEY_ID"] = os.environ["access_key"]
            os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["secret_key"]
            os.environ["AWS_ENDPOINT_URL_S3"] = os.environ["host_bucket"]
            os.environ["AWS_DEFAULT_REGION"] = os.environ["bucket_location"]

        # In cluster mode, just use the "real" s3 bucket
        else:
            os.environ["AWS_ACCESS_KEY_ID"] = os.environ["S3_ACCESSKEY"]
            os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["S3_SECRETKEY"]
            os.environ["AWS_ENDPOINT_URL_S3"] = os.environ["S3_ENDPOINT"]
            os.environ["AWS_DEFAULT_REGION"] = os.environ["S3_REGION"]

        os.environ["AWS_DEFAULT_OUTPUT"] = "json"

    def hide_secrets(self, log: str) -> str:
        """The logs print secrets in clear e.g 'key': '<my-secret>'... so we hide them with a regex"""
        for key in (
            "key",
            "secret",
            "endpoint_url",
            "region_name",
            "api_token",
            "password",
        ):
            log = re.sub(rf"""(['"]{key}['"])\s*:\s*['"][^'"]*['"]""", r"\1: ***", log)
        return log

    def get_tasktable(
        self,
        module_name: str,
        class_name: str,
    ):
        """
        Return the DPR tasktable. This function is run from inside the dask pod.
        """
        # Copy env vars from the caller
        self.copy_caller_env()

        # Init opentelemetry and record all task in an Opentelemetry span
        init_opentelemetry.init_traces(None, SERVICE_NAME, logger)
        with init_opentelemetry.start_span(__name__, "dpr_tasktable", self.span_context):

            if self.use_mockup:
                time.sleep(1)
                return {}

            # Load the python class
            class_ = getattr(importlib.import_module(module_name), class_name)

            # Get the tasktable for default mode. See:
            # https://cpm.pages.eopf.copernicus.eu/eopf-cpm/main/processor-orchestration-guide/tasktables.html#tasktables
            logger.debug(f"Available modes for {class_}: {class_.get_available_modes()}")
            default_mode = class_.get_default_mode()
            tasktable = class_.get_tasktable_description(default_mode)
            return tasktable

    def run_processor(self) -> dict:
        """
        Run processor from the dask pod.
        """
        # Copy env vars from the caller
        self.copy_caller_env()

        # Init opentelemetry and record all task in an Opentelemetry span
        init_opentelemetry.init_traces(None, SERVICE_NAME, logger)
        with init_opentelemetry.start_span(__name__, "dpr_processor", self.span_context):
            try:
                # This should run on the dask worker
                logger.debug(f"Call 'ProcessorCaller.run' from {get_ip_address()!r}")

                self.init()

                start_time = time.time()
                self.trigger()
                self.exec_times.append(("Run processor", time.time() - start_time))

                return self.finalize()

            # In all cases, run the finalize function
            except Exception as e:  # pylint: disable=broad-exception-caught
                try:
                    self.finalize()
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.exception(traceback.format_exc())
                raise e

    def init(self):
        """
        Init from the dask pod.
        """
        # Mockup processor
        if self.use_mockup:
            try:
                payload_abs_path = osp.join("/", os.getcwd(), "payload.cfg")
                with open(payload_abs_path, "w+", encoding="utf-8") as payload:
                    payload.write(yaml.safe_dump(self.data))
            except Exception as e:
                logger.exception("Exception during payload file creation: %s", e)
                raise
            self.command = ["python3.11", "DPR_processor_mock.py", "-p", payload_abs_path]
            self.working_dir = "/src/DPR"
            self.log_path = "./mockup.log"  # not used
            logger.debug(f"Working directory for subprocess: {self.working_dir} (type: {type(self.working_dir)})")
            return

        #
        # Real processor

        # Read arguments
        s3_config_dir = self.data["s3_config_dir"]
        payload_subpath = self.data["payload_subpath"]
        self.s3_report_dir = self.data["s3_report_dir"]

        # Get S3 file handler.
        from eopf.common.file_utils import (  # pylint: disable=import-outside-toplevel
            AnyPath,
        )

        self.s3 = AnyPath(
            s3_config_dir,
            key=os.environ["S3_ACCESSKEY"],
            secret=os.environ["S3_SECRETKEY"],
            client_kwargs={
                "endpoint_url": os.environ["S3_ENDPOINT"],
                "region_name": os.environ["S3_REGION"],
            },
        )

        logger.info("The dpr processing task started")

        # Download the configuration folder from the S3 bucket into a local temp folder
        local_config_dir = self.s3.get(recursive=True)

        # Payload path and parent dir
        payload_file = osp.realpath(osp.join(local_config_dir, payload_subpath))
        payload_dir = osp.dirname(payload_file)

        # Change working directory
        self.working_dir = osp.join(local_config_dir, payload_dir)
        os.chdir(self.working_dir)

        # Create the reports dir
        # WARNING: fields from the payload file: dask__export_graphs, performance_report_file, ... should
        # also use this directory: ./reports
        self.local_report_dir = osp.realpath("./reports")
        self.log_path = osp.join(self.local_report_dir, Path(payload_file).with_suffix(".processor.log").name)
        shutil.rmtree(self.local_report_dir, ignore_errors=True)
        os.makedirs(self.local_report_dir, exist_ok=True)

        # Customize the payload file values
        self.customize_payload_file(payload_dir, payload_file)

        self.command = ["eopf", "trigger", "local", payload_file]

    def customize_payload_file(self, payload_dir: str, payload_file: str):
        """Customize the payload file values"""

        # Read the payload file contents
        with open(payload_file, encoding="utf-8") as opened:
            payload_contents = yaml.safe_load(opened)

        # Write the Dask context configuration in the payload file.
        self.write_dask_context(payload_contents)

        # Handle the experimental configuration
        self.handle_experimental_config(payload_contents)

        # Write the payload contents back to the file
        with open(payload_file, "w+", encoding="utf-8") as opened:
            opened.write(yaml.safe_dump(payload_contents))

        # Display the payload file contents in the log and log file
        with open(payload_file, encoding="utf-8") as opened:

            self.payload_contents = yaml.safe_load(opened)
            dumped = self.hide_secrets(json.dumps(self.payload_contents, indent=2))
            message = f"Dask cluster label: {self.cluster_info.cluster_label!r}\n"
            message += f"Dask cluster instance: {self.cluster_info.cluster_instance!r}\n"
            message += f"Payload file contents: {payload_file!r}\n{dumped}\n"

            logger.debug(message)

            with open(self.log_path, "w", encoding="utf-8") as log_file:
                log_file.write(message)

            # Get logging configuration file
            log_conf_file = self.payload_contents.get("logging")

        # Patch the log config to set "disable_existing_loggers" to False else the logs are disabled.
        # This is a workaround for https://gitlab.eopf.copernicus.eu/cpm/eopf-cpm/-/issues/837
        if log_conf_file:
            log_conf_file = osp.join(payload_dir, log_conf_file)
            logger.warning(f"Patching logging configuration to use 'disable_existing_loggers=False': {log_conf_file!r}")
            with open(log_conf_file, encoding="utf-8") as opened:
                log_conf_contents = yaml.safe_load(opened)
                log_conf_contents["disable_existing_loggers"] = False
            with open(log_conf_file, "w+", encoding="utf-8") as opened:
                opened.write(yaml.safe_dump(log_conf_contents))

    def write_dask_context(self, payload_contents: dict):
        """
        Write the Dask context configuration in the payload file.
        This Dask context is used by EOPF to connect to the Dask cluster.

        NOTE: rs-dpr-service connects to the Dask cluster, then submits an EOPF triggering to this cluster.
        Then EOPF reads the Dask context from the payload file to submit the DPR processor run to this cluster.

        We need to make sure that rs-dpr-service and EOPF use the same cluster.

        So it's safer that rs-dpr-service writes the Dask context in the payload file with the same configuration
        that is used to submit the EOPF triggering.
        """
        if settings.LOCAL_MODE:
            auth = {
                "type": "basic",
                "username": os.environ["LOCAL_DASK_USERNAME"],
                "password": os.environ["LOCAL_DASK_PASSWORD"],
            }
        else:  # cluster mode
            auth = {
                "type": "jupyterhub",
                "api_token": self.cluster_info.jupyter_token,
            }

        payload_contents.update(
            {
                "dask_context": {
                    "cluster_type": "gateway",
                    "cluster_config": {
                        "address": self.cluster_address,
                        "reuse_cluster": self.cluster_info.cluster_instance,
                        "auth": auth,
                    },
                },
            },
        )

    def handle_experimental_config(self, payload_contents: dict):
        """Handle the experimental configuration"""

        # Check if an experimental configuraition is set (only for testing)
        self.experimental_config = ExperimentalConfig(**self.data.get("experimental_config", {}))
        if self.experimental_config == ExperimentalConfig():
            return

        # Hard replace the dask gateway configuration with a LocalCluster
        if self.experimental_config.local_cluster.enabled and (dask_context := payload_contents.get("dask_context")):
            dask_context["cluster_type"] = "local"
            if cluster_config := dask_context["cluster_config"]:
                cluster_config.pop("address", None)
                cluster_config.pop("reuse_cluster", None)
                cluster_config.pop("auth", None)
                cluster_config.pop("workers", None)

                cluster_config["n_workers"] = self.experimental_config.local_cluster.n_workers
                cluster_config["memory_limit"] = self.experimental_config.local_cluster.memory_limit
                cluster_config["threads_per_worker"] = self.experimental_config.local_cluster.threads_per_worker

        # Read/write on the local disk rather than on the S3 bucket. Only works with a LocalCluster.
        if self.experimental_config.local_files.local_dir:

            # For each input or output product
            start_time = time.time()
            for io_key, io_value in payload_contents.get("I/O", {}).items():
                for product in io_value:
                    self.handle_local_product(io_key, product)
            self.exec_times.append(("Download input files", time.time() - start_time))

    def handle_local_product(self, io_key: str, original_product: dict):
        """Handle local products for the experimental configuration"""

        import s3fs  # pylint: disable=import-outside-toplevel
        from eopf.common.env_utils import (  # pylint: disable=import-outside-toplevel
            resolve_env_vars,
        )

        if not self.experimental_config:
            return

        # resolve all env_vars in the payload
        product = resolve_env_vars(original_product)

        # Get product path
        if not (s3_path := product.get("path")):
            return

        # If the path is not on a s3 bucket, this means the path is already local, so we do nothing
        if not s3_path.lower().startswith("s3:/"):
            return

        # Corresponding path on the local disk
        local_path = Path(f"{self.experimental_config.local_files.local_dir}/{s3_path[4:].lstrip('/')}")

        # Read S3 credentials
        store_params = product["store_params"]
        if store_params.get("s3_secret_alias"):
            raise RuntimeError("TODO: handle bucket credentials from a 'secrets.json' file")
        credentials = s3fs.S3FileSystem(**store_params["storage_options"])

        # Input or output product ?
        is_output = io_key == "output_products"
        is_input = not is_output

        def remove_local_path():
            """Remove product on local disk"""
            if local_path.is_file() or local_path.is_symlink():
                local_path.unlink()
            elif local_path.is_dir():
                shutil.rmtree(local_path)

        if is_input:
            # Remove the existing input product on local disk
            if self.experimental_config.local_files.overwrite_input:
                remove_local_path()

            # Download the product locally if not already there
            if not local_path.exists():
                logger.info(f"Download {s3_path!r} to {str(local_path)!r}")
                local_path.parent.mkdir(parents=True, exist_ok=True)
                credentials.get(s3_path, local_path, recursive=True)

        if is_output:
            # Always remove the existing output product on local disk
            remove_local_path()

            # The output product will be uploaded at the end of the processor
            if self.experimental_config.local_files.upload_output:
                self.to_be_uploaded.append((credentials, str(local_path), s3_path))

        # Use the local path in the payload file
        original_product["path"] = str(local_path)

    def trigger(self):
        """Trigger eopf-cpm execution"""

        # Everything is run on the rs-dpr-service host machine.
        # This is used to debug in local mode / docker compose on your local machine.
        # We call eopf from python code.
        if (
            settings.LOCAL_MODE
            and (not self.use_mockup)
            and self.experimental_config
            and self.experimental_config.local_cluster.enabled
        ):
            from eopf.triggering.runner import (  # pylint: disable=import-outside-toplevel
                EORunner,
            )

            EORunner().run(self.payload_contents)
            return

        # Trigger EOPF processing, catch output
        # NOTE: we run it in a subprocess because this allows us to capture stdout and stderr more easily.
        with subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.working_dir,
        ) as proc:

            # Log contents
            log_str = ""

            # Write output to a log file and string + redirect to the prefect logger
            with open(self.log_path, "a", encoding="utf-8") as log_file:
                while proc.stdout and (line := proc.stdout.readline()) != "":

                    # Hide secrets from logs
                    line = self.hide_secrets(line)

                    # Write to log file and string
                    log_file.write(line)
                    log_str += line

                    # Write to logger if not empty
                    line = line.rstrip()
                    if line:
                        logger.info(line)

            # Wait for the execution to finish
            status_code = proc.wait()

            # Raise exception if the status code is != 0
            if status_code:
                raise RuntimeError(f"EOPF error, status code {status_code!r}, please see the log.")
            logger.info(f"EOPF finished successfully with status code {status_code!r}")

            # search for the JSON-like part, parse it, and ignore the rest.
            if self.use_mockup:
                match = re.search(r"(\[\s*\{.*\}\s*\])", log_str, re.DOTALL)
                if not match:
                    raise ValueError(f"No valid dpr_payload structure found in the output:\n{log_str}")

                payload_str = match.group(1)

                # Use `ast.literal_eval` to safely evaluate the structure
                try:
                    # payload_str is a string that looks like a JSON, extracted from the dpr mockup's raw output.
                    # ast.literal_eval() parses that string and returns the actual Python object (not just the string).
                    self.mockup_return_value = ast.literal_eval(payload_str)
                except Exception as e:
                    raise ValueError(f"Failed to parse dpr_payload structure: {e}") from e

    def finalize(self) -> dict:
        """Code to run at the end of the processor."""

        if self.use_mockup:
            return self.mockup_return_value

        try:
            # Upload the reports dir to the s3 bucket
            if self.s3:
                logger.info(f"Upload reports {self.local_report_dir!r} to {self.s3_report_dir!r}")
                self.s3._fs.put(  # pylint: disable=protected-access
                    self.local_report_dir,
                    self.s3_report_dir,
                    recursive=True,
                )

            # Upload local output products to the s3 bucket
            start_time = time.time()
            for credentials, local_path, s3_path in self.to_be_uploaded:
                logger.info(f"Upload {local_path!r} to {s3_path!r}")
                try:
                    credentials.rm(s3_path, recursive=True)  # remove existing from s3 bucket
                except FileNotFoundError:
                    pass
                credentials.put(str(local_path), s3_path, recursive=True)

            if self.to_be_uploaded:
                self.exec_times.append(("Upload output files", time.time() - start_time))

        except Exception as exception:  # pylint: disable=broad-exception-caught
            logger.error(exception)

        for description, exec_time in self.exec_times:
            logger.info(f"[TIME] {description}: {str(timedelta(seconds=exec_time))}")

        # NOTE: with the real processor, what should we return ?
        return {}
