"""
This module provides functionality related to Kubeflow Pipelines.
"""

import inspect
import json
import logging
import os
import textwrap
import time
from datetime import datetime
from typing import Optional, Dict, Any, Mapping, Callable, Tuple
from inspect import Signature, Parameter
import kfp
from kfp import dsl
from kserve import (
    KServeClient,
    V1beta1InferenceService,
    V1beta1InferenceServiceSpec,
    V1beta1ModelFormat,
    V1beta1ModelSpec,
    V1beta1PredictorSpec,
    V1beta1SKLearnSpec,
    constants,
    utils,
)
from kubernetes import client, config
from kubernetes.client import V1ObjectMeta, V1ContainerPort, ApiException
from kubernetes.client.models import V1EnvVar
from kubernetes.config import ConfigException
from kubernetes.stream import stream

from .. import plugin_config
from ..pluginmanager import PluginManager


class CogContainer(kfp.dsl._container_op.Container):
    """
    Subclass of Container to add model access environment variables.
    """

    def __init__(self, name=None, image=None, command=None, args=None, **kwargs):
        """
        Initializes the CogContainer class.
        """
        super().__init__(name=name, image=image, command=command, args=args, **kwargs)

    def add_model_access(self):
        """
        Adds model access environment variables to the container.

        Returns:
            CogContainer: Container instance with added environment variables.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        env_vars = [
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "MINIO_BUCKET_NAME",
            "API_BASEPATH",
            "MLFLOW_TRACKING_URI",
            "KF_PIPELINES_SA_TOKEN_PATH",
            "MINIO_ENDPOINT_URL",
            "MLFLOW_S3_ENDPOINT_URL",
        ]

        # Adding only environment variables present in the image
        for key in env_vars:
            value = os.environ.get(key)
            if value:
                self.add_env_variable(V1EnvVar(name=key, value=value))

        return self


class KubeflowPlugin:
    """
    Class for defining reusable components.
    """

    def __init__(
        self,
        image=None,
        command=None,
        args=None,
        api_url: str = None,
        skip_tls_verify: bool = True,
    ):
        """
        Initializes the KubeflowPlugin class.
        """
        self.kfp = kfp
        self.kfp.dsl._container_op.Container.AddModelAccess = (
            CogContainer.add_model_access
        )
        self.kfp.dsl._container_op.ContainerOp.AddModelAccess = (
            CogContainer.add_model_access
        )
        self.config_file_path = os.getenv(plugin_config.COGFLOW_CONFIG_FILE_PATH)
        self.v2 = kfp.v2
        self.section = "kubeflow_plugin"
        self._api_url = api_url
        self._skip_tls_verify = skip_tls_verify

    @staticmethod
    def pipeline(name=None, description=None):
        """
        Decorator function to define Kubeflow Pipelines.

        Args:
            name (str, optional): Name of the pipeline. Defaults to None.
            description (str, optional): Description of the pipeline. Defaults to None.

        Returns:
            Callable: Decorator for defining Kubeflow Pipelines.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        return dsl.pipeline(name=name, description=description)

    @staticmethod
    def create_component_from_func(
        func,
        output_component_file=None,
        base_image=None,
        packages_to_install=None,
        annotations: Optional[Mapping[str, str]] = None,
    ):
        """
        Create a component from a Python function.

        Args:
            func (Callable): Python function to convert into a component.
            output_component_file (str, optional): Path to save the component YAML file. Defaults
            to None.
            base_image (str, optional): Base Docker image for the component. Defaults to None.
            packages_to_install (List[str], optional): List of additional Python packages
            to install in the component.
            Defaults to None.
            annotations: Optional. Allows adding arbitrary key-value data to the component specification.
        Returns:
            kfp.components.ComponentSpec: Component specification.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        training_var = kfp.components.create_component_from_func(
            func=func,
            output_component_file=output_component_file,
            base_image=base_image,
            packages_to_install=packages_to_install,
            annotations=annotations,
        )

        def wrapped_component(*args, **kwargs):
            component_op = training_var(*args, **kwargs)
            component_op = CogContainer.add_model_access(component_op)
            return component_op

        wrapped_component.__signature__ = inspect.signature(training_var)
        wrapped_component.component_spec = training_var.component_spec
        return wrapped_component

    def _create_kfp_client(
        self, session_cookies: str = None, namespace: str = None
    ) -> kfp.Client:
        """
        Create a KFP client, optionally using api_url and session cookies.
        Works inside or outside the cluster.
        """
        # Case 1: Inside cluster / default
        if not self._api_url and not session_cookies:
            return kfp.Client()

        # Case 2: Outside cluster with cookie string
        if session_cookies:
            # Monkey patch for TLS verification (needed in KFP v1.8.22)
            original_load_config = kfp.Client._load_config

            def patched_load_config(client_self, *args, **kwargs):
                config = original_load_config(client_self, *args, **kwargs)
                config.verify_ssl = not self._skip_tls_verify
                return config

            patched_kfp_client = kfp.Client
            patched_kfp_client._load_config = patched_load_config

            return patched_kfp_client(
                host=self._api_url,
                cookies=session_cookies,  # expecting full "authservice_session=..." string
                namespace=namespace,
            )

        # Case 3: api_url but no cookie
        return kfp.Client(host=self._api_url, namespace=namespace)

    @staticmethod
    def client(
        api_url: str = None,
        skip_tls_verify: bool = True,
        session_cookies: str = None,
        namespace: str = None,
    ) -> kfp.Client:
        """
        Get the Kubeflow Pipelines client.

        Args:
            api_url (str, optional): KFP API endpoint for external access.
            skip_tls_verify (bool): Whether to skip TLS verification.
            session_cookies (str, optional): Dex/IAP session cookie string.
            namespace (str, optional): Kubernetes namespace to use. If None, uses default.

        Returns:
            kfp.Client: Configured Kubeflow Pipelines client instance.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        kfp_plugin = KubeflowPlugin(api_url=api_url, skip_tls_verify=skip_tls_verify)
        return kfp_plugin._create_kfp_client(
            session_cookies=session_cookies, namespace=namespace
        )

    @staticmethod
    def load_component_from_url(url):
        """
        Load a component from a URL.

        Args:
            url (str): URL to load the component from.

        Returns:
            kfp.components.ComponentSpec: Loaded component specification.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        return kfp.components.load_component_from_url(url)

    @staticmethod
    def serve_model_v2(
        model_uri: str,
        isvc_name: str = None,
        model_id: str = None,
        model_name: str = None,
        model_version: str = None,
        dataset_id: str = None,
        transformer_image: str = None,
        transformer_parameters: dict = None,
    ):
        """
        Create a KServe InferenceService with optional transformer.

        Args:
            model_uri (str): URI of the model.
            isvc_name (str, optional): Name of the kserve instance.
            model_id (str, optional): Unique identifier for the model.
            model_name (str, optional): Name of the registered model.
            model_version (str, optional): Version of the registered model.
            dataset_id (str, optional): Linked dataset identifier.
            transformer_image (str): Image of the transformer.
            transformer_parameters (dict, optional): Dict containing:
            - "PROMETHEUS_URL": URL for Prometheus
            - "PROMETHEUS_METRICS": Comma-separated metrics
            Required if transformer_image is provided.
        """
        PluginManager().verify_activation(KubeflowPlugin().section)

        namespace = utils.get_default_target_namespace()
        if isvc_name is None:
            now = datetime.now()
            date = now.strftime("%d%M")
            isvc_name = f"predictormodel{date}"

        # Predictor spec
        predictor = V1beta1PredictorSpec(
            service_account_name="kserve-controller-s3",
            min_replicas=1,
            model=V1beta1ModelSpec(
                model_format=V1beta1ModelFormat(name=plugin_config.MODEL_TYPE),
                storage_uri=model_uri,
                protocol_version="v2",
            ),
        )

        # Metadata annotations
        annotations = {
            "sidecar.istio.io/inject": "false",
            "model_name": model_name,
            "model_version": model_version,
            "model_id": model_id,
        }
        if dataset_id:
            annotations["dataset_id"] = dataset_id

        # Transformer (optional)
        transformer = None
        if transformer_parameters:
            if not transformer_image:
                raise ValueError(
                    "transformer_image must be provided when transformer_parameters is set"
                )

            prometheus_url = transformer_parameters.get("PROMETHEUS_URL")
            prometheus_metrics = transformer_parameters.get("PROMETHEUS_METRICS")

            if not prometheus_url or not prometheus_metrics:
                raise ValueError(
                    "transformer_parameters must include both 'PROMETHEUS_URL' and 'PROMETHEUS_METRICS'"
                )

            container_name = f"{isvc_name}-transformer".lower()

            transformer = client.V1Container(
                name=container_name,
                image=transformer_image,
                env=[
                    client.V1EnvVar(name="PROMETHEUS_URL", value=prometheus_url),
                    client.V1EnvVar(
                        name="PROMETHEUS_METRICS", value=prometheus_metrics
                    ),
                ],
            )

        # Build InferenceService
        isvc_spec = V1beta1InferenceServiceSpec(predictor=predictor)
        if transformer:
            isvc_spec.transformer = client.V1PodSpec(containers=[transformer])

        isvc = V1beta1InferenceService(
            api_version=constants.KSERVE_V1BETA1,
            kind=constants.KSERVE_KIND,
            metadata=client.V1ObjectMeta(
                name=isvc_name,
                namespace=namespace,
                annotations=annotations,
            ),
            spec=isvc_spec,
        )

        # Create the service with error handling
        kserve = KServeClient()
        try:
            kserve.create(isvc)
            time.sleep(plugin_config.TIMER_IN_SEC)
            print(
                f"InferenceService '{isvc_name}' creation requested in namespace '{namespace}'."
            )
        except ApiException as e:
            if e.status == 409:  # Already exists
                print(
                    f"InferenceService '{isvc_name}' already exists in namespace '{namespace}'."
                )
            else:
                print(f"Failed to create InferenceService '{isvc_name}': {e.reason}")
                raise

    @staticmethod
    def serve_model_v1(model_uri: str, isvc_name: str = None):
        """
        Create a kserve instance version1.

        Args:
            model_uri (str): URI of the model.
            isvc_name (str, optional): Name of the kserve instance. If not provided,
            a default name will be generated.

        Returns:
            None
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        try:
            namespace = utils.get_default_target_namespace()
            isvc = V1beta1InferenceService(
                api_version=constants.KSERVE_V1BETA1,
                kind=constants.KSERVE_KIND,
                metadata=V1ObjectMeta(
                    name=isvc_name,
                    namespace=namespace,
                    annotations={"sidecar.istio.io/inject": "false"},
                ),
                spec=V1beta1InferenceServiceSpec(
                    predictor=V1beta1PredictorSpec(
                        service_account_name="kserve-controller-s3",
                        sklearn=V1beta1SKLearnSpec(storage_uri=model_uri),
                    )
                ),
            )

            kclient = KServeClient()
            kclient.create(isvc)
            time.sleep(plugin_config.TIMER_IN_SEC)
        except ApiException as e:
            raise e

    @staticmethod
    def get_served_models(
        namespace: Optional[str] = None, isvc_name: Optional[str] = None
    ):
        """
        Get served model(s) information from the default namespace.

        Args:
            namespace(str): Namespace where the inference services are deployed.
            isvc_name (str, optional): Name of model inference service.
            If None, returns all inference services of models.

        Returns:
            list: List of model information dictionaries. If isvc_name provided,
                 returns list with a single model. If isvc_name is None, returns
                 a list of all models. Each dict contains: model_name, model_id,
                 model_version, creation_timestamp, served_model_url, status, traffic_percentage.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        kclient = KServeClient()

        def _get_isvc_info(isvc_response):
            if not isvc_response:
                return None
            model_info = KubeflowPlugin._process_isvc(isvc_response)
            return [model_info] if model_info else None

        def _get_all_isvc_info(isvc_response):
            if isinstance(isvc_response, dict) and "items" in isvc_response:
                isvc_list = isvc_response["items"]
            elif hasattr(isvc_response, "items"):
                isvc_list = (
                    isvc_response.items
                    if not callable(isvc_response.items)
                    else isvc_response.items()
                )
            else:
                isvc_list = [isvc_response] if isvc_response else []
            served_models = [
                KubeflowPlugin._process_isvc(isvc)
                for isvc in isvc_list
                if isinstance(isvc, dict)
            ]
            served_models = [m for m in served_models if m]
            served_models.sort(
                key=lambda x: x.get("creation_timestamp") or "", reverse=True
            )
            return served_models

        def is_404_error(exc: Exception) -> bool:
            cause = getattr(exc, "__cause__", None) or getattr(exc, "__context__", None)
            if cause and cause is not exc and is_404_error(cause):
                return True
            if isinstance(exc, ApiException):
                if (
                    getattr(exc, "code", None) == 404
                    or getattr(exc, "status", None) == 404
                ):
                    return True
                reason_text = str(getattr(exc, "reason", "")).lower()
                if "not found" in reason_text or "404" in reason_text:
                    return True
                try:
                    body = getattr(exc, "body", None)
                    if body:
                        if '"code":404' in body or '"reason":"NotFound"' in body:
                            return True
                        data = json.loads(body)
                        if data.get("code") == 404:
                            return True
                except Exception:
                    pass
            if "not found" in str(exc).lower():
                return True
            return False

        try:
            if isvc_name:
                try:
                    isvc_response = kclient.get(namespace=namespace, name=isvc_name)
                except Exception as e:
                    if is_404_error(e):
                        return None
                    raise
                return _get_isvc_info(isvc_response)
            isvc_response = kclient.get(namespace=namespace)
            return _get_all_isvc_info(isvc_response)
        except ApiException as exp:
            if is_404_error(exp):
                return None
            print(f"API Exception: {exp}")
            raise
        except ConfigException as exp:
            print(f"Config Exception: {exp}")
            raise
        except Exception as exp:
            if is_404_error(exp):
                return None
            print(f"Unexpected Exception: {exp}")
            raise

    @staticmethod
    def _process_isvc(isvc: dict) -> dict:
        """
        Process a KServe InferenceService object and extract detailed
        model rollout and canary traffic information.

        Args:
            isvc (dict): Raw InferenceService object from KServe API.

        Returns:
            dict: Processed information with rollout awareness.
        """
        metadata = isvc.get("metadata", {}) or {}
        annotations = metadata.get("annotations", {}) or {}
        status_dict = isvc.get("status", {}) or {}
        spec_dict = isvc.get("spec", {}) or {}

        # --- Identifiers ---
        isvc_name = metadata.get("name", "Unknown")
        model_name = annotations.get("model_name")
        model_id = annotations.get("model_id")
        model_version = annotations.get("model_version")
        dataset_id = annotations.get("dataset_id")
        creation_timestamp = metadata.get("creationTimestamp")

        # --- Base URLs ---
        served_model_url = (
            status_dict.get("url")
            or status_dict.get("address", {}).get("url")
            or status_dict.get("components", {}).get("predictor", {}).get("url")
            or status_dict.get("components", {}).get("transformer", {}).get("url")
        )

        # --- Status ---
        status = "not_ready"
        for cond in status_dict.get("conditions", []):
            if cond.get("type") == "Ready":
                if cond.get("status") == "True":
                    status = "ready"
                break

        # --- Components (predictor + transformer) ---
        components = status_dict.get("components", {})
        predictor = components.get("predictor", {})
        transformer = components.get("transformer", {})

        # Extract predictor/transformer traffic
        predictor_traffic = predictor.get("traffic", [])

        # --- Canary detection ---
        canary_spec = spec_dict.get("predictor", {}).get("canary")
        canary_traffic_percent = spec_dict.get("predictor", {}).get(
            "canaryTrafficPercent"
        )
        has_canary = canary_spec is not None or canary_traffic_percent is not None

        # --- Traffic computation ---
        total_traffic = 0
        traffic_entries = []

        def _extract_traffic_entries(source_traffic, component_name):
            entries = []
            for item in source_traffic or []:
                entries.append(
                    {
                        "revision": item.get("revisionName"),
                        "percent": item.get("percent", 0),
                        "tag": item.get("tag"),
                        "component": component_name,
                    }
                )
            return entries

        traffic_entries.extend(_extract_traffic_entries(predictor_traffic, "predictor"))
        total_traffic = sum(t["percent"] for t in traffic_entries if t["percent"])

        # --- Determine stable vs canary ---
        stable_revision = None
        canary_revision = None
        stable_traffic = None
        canary_traffic = None

        if has_canary:
            for t in traffic_entries:
                if t["percent"] and t["percent"] < 100:
                    if not stable_revision:
                        stable_revision = t["revision"]
                        stable_traffic = t["percent"]
                if t["percent"] and t["percent"] < 100 and t["tag"] == "canary":
                    canary_revision = t["revision"]
                    canary_traffic = t["percent"]

            # fallback if only predictor used
            if not canary_revision and len(traffic_entries) == 2:
                canary_revision = traffic_entries[1]["revision"]
                canary_traffic = traffic_entries[1]["percent"]
                stable_revision = traffic_entries[0]["revision"]
                stable_traffic = traffic_entries[0]["percent"]
        else:
            # single model
            if traffic_entries:
                stable_revision = traffic_entries[0].get("revision")
                stable_traffic = traffic_entries[0].get("percent", 100)

        # --- Age calculation ---
        if creation_timestamp:
            try:
                creation_time = datetime.strptime(
                    creation_timestamp, "%Y-%m-%dT%H:%M:%SZ"
                )
                age = str(datetime.utcnow() - creation_time).split(".", 1)[0]
            except Exception:
                age = "Unknown"
        else:
            age = "Unknown"

        # --- Compose final object ---
        model_info = {
            "isvc_name": isvc_name,
            "served_model_url": served_model_url,
            "status": status,
            "model_id": model_id or None,
            "model_name": model_name or None,
            "model_version": model_version or None,
            "dataset_id": dataset_id or None,
            "creation_timestamp": creation_timestamp,
            "age": age,
            "latest_ready_revision": predictor.get("latestReadyRevision")
            or transformer.get("latestReadyRevision"),
            "traffic_percentage": total_traffic or stable_traffic or 100,
            "has_canary": bool(has_canary),
            "stable_revision": stable_revision,
            "canary_revision": canary_revision,
            "stable_traffic_percent": stable_traffic,
            "canary_traffic_percent": canary_traffic,
        }

        return model_info

    @staticmethod
    def delete_served_model(isvc_name: str, namespace: str = None):
        """
        Delete a deployed model by its ISVC name.

        Args:
            isvc_name (str): Name of the deployed model.
            namespace (str, optional): Namespace where the model is deployed.

        Returns:
            None
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)

        try:
            if namespace is None:
                namespace = utils.get_default_target_namespace()
            KServeClient().delete(isvc_name, namespace)
            print("Inference Service has been deleted successfully.")
        except Exception as exp:
            raise Exception(f"Failed to delete Inference Service: {exp}")

    @staticmethod
    def load_component_from_file(file_path):
        """
        Load a component from a File.

        Args:
            file_path (str): file_path to load the component from file.

        Returns:
            kfp.components.ComponentSpec: Loaded component specification.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)
        return kfp.components.load_component_from_file(file_path)

    @staticmethod
    def load_component_from_text(text):
        """
        Load a component from the text.

        Args:
            text (str):  load the component from text.

        Returns:
            kfp.components.ComponentSpec: Loaded component specification.
        """
        # Verify plugin activation
        PluginManager().verify_activation(KubeflowPlugin().section)
        return kfp.components.load_component_from_text(text)

    def create_run_from_pipeline_func(
        self,
        pipeline_func,
        arguments: Optional[Dict[str, Any]] = None,
        run_name: Optional[str] = None,
        experiment_name: Optional[str] = None,
        namespace: Optional[str] = None,
        pipeline_root: Optional[str] = None,
        enable_caching: Optional[bool] = None,
        service_account: Optional[str] = None,
    ):
        """
            method to create a run from pipeline function
        :param pipeline_func:
        :param arguments:
        :param run_name:
        :param experiment_name:
        :param namespace:
        :param pipeline_root:
        :param enable_caching:
        :param service_account:
        :return:
        """
        run_details = self.client().create_run_from_pipeline_func(
            pipeline_func,
            arguments,
            run_name,
            experiment_name,
            namespace,
            pipeline_root,
            enable_caching,
            service_account,
        )
        return run_details

    def is_run_finished(
        self,
        run_id,
    ):
        """
            method to check if the run is finished
        :param run_id: run_id of the run
        :return: boolean
        """
        status = self.client().get_run(run_id).run.status
        return status in ["Succeeded", "Failed", "Skipped", "Error"]

    def get_run_status(
        self,
        run_id,
    ):
        """
        method return the status of run
        :param run_id: run_id of the run
        :return: status of the run
        """
        return self.client().get_run(run_id).run.status

    @staticmethod
    def delete_pipeline(
        pipeline_id,
        api_url: str = None,
        skip_tls_verify: bool = True,
        session_cookies: str = None,
        namespace: str = None,
    ):
        """
        method deletes the pipeline
        :param pipeline_id: pipeline id
        :param api_url: KFP API endpoint for external access
        :param skip_tls_verify: whether to skip TLS verification
        :param session_cookies: session cookies for authentication
        :param namespace: user namespace to use. If None, uses default.
        :return:
        """
        KubeflowPlugin.client(
            api_url=api_url,
            skip_tls_verify=skip_tls_verify,
            session_cookies=session_cookies,
            namespace=namespace,
        ).delete_pipeline(pipeline_id=pipeline_id)

    @staticmethod
    def list_pipeline_versions(
        pipeline_id,
        api_url: str = None,
        skip_tls_verify: bool = True,
        session_cookies: str = None,
        namespace: str = None,
    ):
        """
         method to list the pipeline based on pipeline_id
        :param pipeline_id: pipeline id
        :param api_url: KFP API endpoint for external access
        :param skip_tls_verify: whether to skip TLS verification
        :param session_cookies: session cookies for authentication
        :param namespace: user namespace to use. If None, uses default.
        :return:
        """
        response = KubeflowPlugin.client(
            api_url=api_url,
            skip_tls_verify=skip_tls_verify,
            session_cookies=session_cookies,
            namespace=namespace,
        ).list_pipeline_versions(pipeline_id=pipeline_id)
        return response

    @staticmethod
    def delete_pipeline_version(
        version_id,
        api_url: str = None,
        skip_tls_verify: bool = True,
        session_cookies: str = None,
        namespace: str = None,
    ):
        """
        method to list the pipeline based on version_id
        :param version_id: pipeline id
        :param api_url: KFP API endpoint for external access
        :param skip_tls_verify: whether to skip TLS verification
        :param session_cookies: session cookies for authentication
        :param namespace: user namespace to use. If None, uses default.
        :return:
        """
        KubeflowPlugin.client(
            api_url=api_url,
            skip_tls_verify=skip_tls_verify,
            session_cookies=session_cookies,
            namespace=namespace,
        ).delete_pipeline_version(version_id=version_id)

    @staticmethod
    def delete_runs(
        run_ids,
        api_url: str = None,
        skip_tls_verify: bool = True,
        session_cookies: str = None,
        namespace: str = None,
    ):
        """
        delete the pipeline runs
        :param run_ids: list of runs
        :param api_url: KFP API endpoint for external access
        :param skip_tls_verify: whether to skip TLS verification
        :param session_cookies: session cookies for authentication
        :param namespace: user namespace to use. If None, uses default.
        :return: successful deletion runs or 404 error
        """
        for run in run_ids:
            KubeflowPlugin.client(
                api_url=api_url,
                skip_tls_verify=skip_tls_verify,
                session_cookies=session_cookies,
                namespace=namespace,
            ).runs.delete_run(id=run)

    @staticmethod
    def get_default_namespace() -> str:
        """
        Retrieve the default namespace from the current Kubernetes configuration.
        Returns:
            str: The default namespace.
        """
        try:
            config.load_incluster_config()
            with open(
                "/var/run/secrets/kubernetes.io/serviceaccount/namespace",
                "r",
                encoding="utf-8",
            ) as f:
                return f.read().strip()
        except (FileNotFoundError, ConfigException):
            try:
                config.load_kube_config()
                current_context = config.list_kube_config_contexts()[1]
                return current_context["context"].get("namespace", "default")
            except ConfigException:
                return "default"

    @staticmethod
    def create_service(name: str) -> str:
        """
        Create a Kubernetes service for the component in the default namespace.
        Args:
            name (str): Name of the service to be created.
        Returns:
            str: Name of the created service.
        """
        namespace = KubeflowPlugin().get_default_namespace()
        srvname = name

        print(f"Creating service in namespace '{namespace}'...")

        # Define the service
        service_spec = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=srvname,
                annotations={
                    "service.alpha.kubernetes.io/app-protocols": '{"grpc":"HTTP2"}'
                },
            ),
            spec=client.V1ServiceSpec(
                selector={"app": name},
                ports=[
                    client.V1ServicePort(
                        protocol="TCP", port=8080, name="grpc", target_port=8080
                    )
                ],
                type="ClusterIP",
            ),
        )

        # Create the Kubernetes API client
        api_instance = client.CoreV1Api()

        try:
            # Create the service
            api_instance.create_namespaced_service(
                namespace=namespace, body=service_spec
            )
            print(
                f"Service '{srvname}' created successfully in namespace '{namespace}'."
            )
        except client.exceptions.ApiException as e:
            raise RuntimeError(f"Exception when creating service: {e}")

        return srvname

    @staticmethod
    def delete_service(name: str):
        """
        Delete a Kubernetes service by name in the default namespace.
        Args:
            name (str): Name of the service to be deleted.
        """
        namespace = KubeflowPlugin().get_default_namespace()
        srvname = name
        print(f"Deleting service '{srvname}' from namespace '{namespace}'...")

        api_instance = client.CoreV1Api()

        try:
            api_instance.delete_namespaced_service(name=srvname, namespace=namespace)
            print(
                f"Service '{srvname}' deleted successfully from namespace '{namespace}'."
            )
        except client.exceptions.ApiException as e:
            print(f"Exception when deleting service: {e}")

    @staticmethod
    def create_fl_pipeline(
        fl_client, fl_server, connectors: list, node_enforce: bool = True
    ):
        """
        Returns a KFP pipeline function that wires up:
        setup_links → fl_server → many fl_client → release_links

        fl_client must accept at minimum:
        - server_address: str
        - local_data_connector

        fl_server must accept at minimum:
        - number_of_iterations: int

        Any other parameters that fl_client/ fl_server declare will automatically
        become pipeline inputs and be forwarded along.
        """

        def setup_links_func(name: str) -> str:
            """
            Set up a service in the default namespace with the given name.
            Args:
                name (str): Name of the service to be created.
            Returns:
                str: Name of the created service.
            """
            from cogflow import KubeflowPlugin

            KubeflowPlugin().create_service(name=name)
            return name

        def release_links_func(name: str):
            """
            Release a service created by `setup_links_func`.
            Deletes a previously created service by name in the default namespace.
            Args:
                name (str): Name of the service to be deleted.
            Returns:
                str: Result message of service deletion.
            """
            from cogflow import KubeflowPlugin

            KubeflowPlugin().delete_service(name=name)

        # Introspect client/server signatures
        client_sig = inspect.signature(fl_client)
        server_sig = inspect.signature(fl_server)

        # Mandatory params
        client_req = {"server_address", "local_data_connector"}
        server_req = {"number_of_iterations"}

        # ← CHANGE: only consider real kw/positional params, skip VAR_POSITIONAL and VAR_KEYWORD
        def _valid_param_names(sig):
            return [
                name
                for name, p in sig.parameters.items()
                if p.kind
                in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                )
            ]

        client_params = _valid_param_names(client_sig)  # ← CHANGE
        server_params = _valid_param_names(server_sig)  # ← CHANGE

        # Find any extra parameters
        client_extra = [p for p in client_params if p not in client_req]
        server_extra = [p for p in server_params if p not in server_req]
        extra_params = list(dict.fromkeys(client_extra + server_extra))

        # Build a list of inspect.Parameter for the pipeline signature
        sig_params = []
        # 1) local_data_connectors --removed
        # 2) number_of_iterations
        sig_params.append(
            Parameter(
                name="number_of_iterations",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=int,
            )
        )
        # 3) extras, preserving defaults & annotations
        for name in extra_params:
            # pick whichever component declares it
            param = client_sig.parameters.get(name, server_sig.parameters.get(name))
            default = (
                param.default if param.default is not inspect._empty else inspect._empty
            )
            ann = param.annotation if param.annotation is not inspect._empty else None
            sig_params.append(
                Parameter(
                    name=name,
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=ann,
                    default=default,
                )
            )
        pipeline_sig = Signature(parameters=sig_params)

        # create component from func
        setup_links = KubeflowPlugin.create_component_from_func(
            setup_links_func, base_image="hiroregistry/cogflow_lite:latest"
        )
        release_links = KubeflowPlugin.create_component_from_func(
            release_links_func, base_image="hiroregistry/cogflow_lite:latest"
        )

        def fl_pipeline_func(*args, _node_enforce=node_enforce, **kwargs):
            # 2) bind positional → named arguments per our explicit signature
            bound = fl_pipeline_func.__signature__.bind_partial(
                *args, **kwargs
            )  # ← CHANGE
            bound.apply_defaults()  # ← CHANGE
            args_map = bound.arguments  # ← CHANGE
            # extract required inputs
            # local_data_connectors = args_map["local_data_connectors"]
            number_of_iterations = args_map["number_of_iterations"]

            # split extras for client & server
            server_kwargs = {k: args_map[k] for k in server_extra}
            client_kwargs = {k: args_map[k] for k in client_extra}

            # generate service name with run id later at runtime it will replaced by run id
            srv_name = "flserver-" + "{{workflow.uid}}"
            # 1. create the k8s Service
            setup_task = setup_links(name=srv_name)
            # 1.1. tear down once the server is done
            cleanup_task = release_links(name=srv_name)
            # 2. start the FL server
            with dsl.ExitHandler(cleanup_task):
                server_task = fl_server(
                    number_of_iterations=number_of_iterations, **server_kwargs
                ).after(setup_task)
                server_task.add_pod_label(name="app", value=srv_name)

                # 3. fan-out clients in parallel -- We will revert back to this after v2
                # supported grouping added later on kfp v2
                # with dsl.ParallelFor(local_data_connectors) as connector:
                for connector in connectors:
                    client_op = fl_client(
                        server_address=setup_task.output,
                        local_data_connector=connector.link,
                        **client_kwargs,
                    ).after(setup_task)

                    region = getattr(connector, "region", "")
                    # ← CHANGE: only add node selector if enforcement is enabled
                    if _node_enforce:
                        client_op.add_node_selector_constraint("region", region)

                    client_op.set_display_name(  # ← CHANGE: moved inside loop
                        f"client:{region}"  # ← CHANGE: display region
                    )

            # Attach the explicit signature so KFP can see all inputs

        fl_pipeline_func.__signature__ = pipeline_sig

        # Decorate as a pipeline
        flpipeline = dsl.pipeline(
            name="Federated Learning Pipeline", description="Auto-generated FL pipeline"
        )(fl_pipeline_func)
        return flpipeline

    @staticmethod
    def create_fl_component_from_func(
        func,
        output_component_file=None,
        base_image=None,
        packages_to_install=None,
        annotations: Optional[Mapping[str, str]] = None,
        container_port=8080,
        pod_label_name="app",
    ):
        """
        Create a component from a Python function with additional configurations
        for ports and pod labels using Pod UID to ensure unique run_id.
        """

        # Create the initial KFP component
        training_var = kfp.components.create_component_from_func(
            func=func,
            output_component_file=output_component_file,
            base_image=base_image,
            packages_to_install=packages_to_install,
            annotations=annotations,
        )

        def wrapped_fl_component(*args, **kwargs):
            run_id = "fl-server-" + "{{workflow.uid}}"

            component_op = training_var(*args, **kwargs)

            # Add container port and pod labels
            component_op.container.add_port(
                V1ContainerPort(container_port=container_port)
            )

            # Add model access configurations
            component_op = CogContainer.add_model_access(component_op)

            # Add run_id and pod label
            component_op.add_pod_label(name=pod_label_name, value=run_id)

            return component_op

        wrapped_fl_component.__signature__ = inspect.signature(training_var)
        wrapped_fl_component.component_spec = training_var.component_spec
        return wrapped_fl_component

    @staticmethod
    def create_fl_client_component(
        func,
        annotations: Optional[Mapping[str, str]] = None,
        output_component_file=None,
        base_image=None,
        packages_to_install=None,
    ) -> Callable:
        """
        Decorator to mark and execute an FL client function.

        Args:
            annotations (dict, optional): Arbitrary metadata to tag the component.
            func : Wraps a function
            output_component_file (str, optional): The output file for the component.
            base_image (str, optional): The base image to use. Defaults to
            "hiroregistry/cogflow:latest".
            packages_to_install (list, optional): List of packages to install.

        Returns:
            Callable: The original function, executed when called.
        """
        # 3) Create the initial KFP component
        training_var = kfp.components.create_component_from_func(
            func=func,
            output_component_file=output_component_file,
            base_image=base_image,
            packages_to_install=packages_to_install,
            annotations=annotations,
        )

        def wrapped_fl_client_component(*args, **kwargs):
            component_op = training_var(*args, **kwargs)

            # Add model access configurations
            component_op = CogContainer.add_model_access(component_op)
            return component_op

        wrapped_fl_client_component.__signature__ = inspect.signature(training_var)
        wrapped_fl_client_component.component_spec = training_var.component_spec
        return wrapped_fl_client_component

    @staticmethod
    def create_fl_base_component(
        func,
        annotations: Optional[Mapping[str, str]] = None,
        output_component_file=None,
        base_image=None,
        packages_to_install=None,
    ) -> Callable:
        """
        Decorator to mark and execute an FL client function.

        Args:
            annotations (dict, optional): Arbitrary metadata to tag the component.
            func : Wraps a function
            output_component_file (str, optional): The output file for the component.
            base_image (str, optional): The base image to use. Defaults to
            "hiroregistry/cogflow:latest".
            packages_to_install (list, optional): List of packages to install.

        Returns:
            Callable: The original function, executed when called.
        """

        # 3) Create the initial KFP component
        training_var = kfp.components.create_component_from_func(
            func=func,
            output_component_file=output_component_file,
            base_image=base_image,
            packages_to_install=packages_to_install,
            annotations=annotations,
        )

        def wrapped_fl_client_component(*args, **kwargs):
            component_op = training_var(*args, **kwargs)

            # Add model access configurations
            component_op = CogContainer.add_model_access(component_op)
            return component_op

        wrapped_fl_client_component.__signature__ = inspect.signature(training_var)
        wrapped_fl_client_component.component_spec = training_var.component_spec
        return wrapped_fl_client_component

    @staticmethod
    def load_k8s_config() -> None:
        """
        Loads the Kubernetes configuration.

        This method tries to load the in-cluster configuration if the code is running inside a pod.
        If it fails (e.g., if the code is running outside the cluster), it loads the kubeconfig file
        from the default location.

        Raises:
            config.config_exception.ConfigException: If the configuration could not be loaded.
        """
        try:
            # Load in-cluster config if running in a pod
            config.load_incluster_config()
        except config.config_exception.ConfigException:
            # If not running in a pod, load the kubeconfig file
            config.load_kube_config()

    @staticmethod
    def _raise_isvc_not_found(
        isvc_name: str, namespace: str, model_name: str, model_version: str
    ):
        raise RuntimeError(
            f"InferenceService '{isvc_name}' not found in namespace '{namespace}'. "
            "First serve the model using serve_model(model_id=None, artifact_path=None, "
            f"model_name='{model_name}', model_version='{model_version}', isvc_name='{isvc_name}')."
        )

    @staticmethod
    def _parse_group_version(api_version: str) -> Tuple[str, str]:
        """
        Parse the group and version from an apiVersion string.
        """
        if not api_version or "/" not in api_version:
            raise ValueError(f"Unexpected apiVersion: {api_version!r}")
        grp, ver = api_version.split("/", 1)
        return grp, ver

    @staticmethod
    def update_served_model(
        isvc_name: str,
        model_id: Optional[str] = None,
        model_uri: Optional[str] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        dataset_id: Optional[str] = None,
        transformer_image: Optional[str] = None,
        transformer_parameters: Optional[Dict] = None,
        protocol_version: Optional[str] = None,
        namespace: Optional[str] = None,
        model_format: Optional[str] = None,
        canary_traffic_percent: Optional[int] = None,
        enable_tag_routing: Optional[bool] = False,
    ) -> str:
        """
        Update or roll out a model on an existing KServe InferenceService.

        Supports:
            - Normal update (no canary)
            - Initial canary rollout (split traffic)
            - Canary promotion (increase or full switch)
            - Disable canary

        Args:
            isvc_name (str): Name of the KServe InferenceService to update.
            model_id (str, optional): Unique identifier for the model/run.
            model_name (str, optional): Registered model name.
            model_version (str, optional): Registered model version.
            model_uri (str, optional): Model URI in artifact store.
            dataset_id (str, optional): Linked dataset ID.
            transformer_image (str, optional): Transformer image.
            transformer_parameters (dict, optional): Transformer parameters.
            protocol_version (str, optional): Protocol version (e.g., v1, v2).
            namespace (str, optional): Namespace of ISVC.
            model_format (str, optional): Model format (mlflow, sklearn, etc.)
            canary_traffic_percent (int, optional): % of traffic routed to canary.
            enable_tag_routing (bool, optional): Tag routing flag.

        Returns:
            str: Success message.
        """
        try:
            if not isvc_name:
                raise ValueError("isvc_name is required")

            # Default namespace
            if not namespace:
                namespace = KubeflowPlugin.get_default_namespace()

            KubeflowPlugin().load_k8s_config()
            co_api = client.CustomObjectsApi()

            # Retrieve ISVC object
            try:
                isvc_obj = KServeClient().get(namespace=namespace, name=isvc_name)
                KubeflowPlugin._process_isvc(isvc_obj)
            except RuntimeError as e:
                msg = str(e)
                if "(404)" in msg or "Not Found" in msg:
                    KubeflowPlugin()._raise_isvc_not_found(
                        isvc_name, namespace, model_name, model_version
                    )
                if "(403)" in msg or "Forbidden" in msg:
                    raise PermissionError(
                        f"Forbidden to access InferenceService '{isvc_name}' in namespace '{namespace}'."
                    ) from e
                raise

            # Parse group/version
            api_version = isvc_obj.get("apiVersion") or isvc_obj.get(
                "metadata", {}
            ).get("apiVersion", "serving.kserve.io/v1beta1")
            group, version = KubeflowPlugin()._parse_group_version(api_version)
            plural = constants.KSERVE_PLURAL

            # ------------------------------------------------------------------
            # Detect existing canary & identify flow type
            # ------------------------------------------------------------------
            existing_canary = (
                isvc_obj.get("spec", {})
                .get("predictor", {})
                .get("canaryTrafficPercent")
                is not None
            )

            is_promotion = canary_traffic_percent is not None and existing_canary

            # ------------------------------------------------------------------
            # Promotion-only flow → patch ONLY traffic percent
            # ------------------------------------------------------------------
            if is_promotion:
                KubeflowPlugin().validate_canary_traffic_percent(
                    isvc_name, canary_traffic_percent
                )

                patch_body = {
                    "spec": {
                        "predictor": {"canaryTrafficPercent": canary_traffic_percent}
                    }
                }

                co_api.patch_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    name=isvc_name,
                    body=patch_body,
                )

                return f"InferenceService '{isvc_name}' canary traffic updated to {canary_traffic_percent}%."

            # ------------------------------------------------------------------
            # Initial rollout or normal update flow
            # ------------------------------------------------------------------
            if not model_id and not (model_name and model_version):
                raise ValueError(
                    "Initial rollout/update requires either model_id or (model_name + model_version)."
                )

            # Validate canary range if provided
            if canary_traffic_percent is not None:
                KubeflowPlugin().validate_canary_traffic_percent(
                    isvc_name, canary_traffic_percent
                )

            # --- Annotations patch ---
            annotations_patch = {
                "model_id": model_id,
                "model_name": model_name,
                "model_version": model_version,
                "dataset_id": str(dataset_id) if dataset_id else None,
                "enable_tag_routing": str(enable_tag_routing).lower(),
            }

            # --- Transformer patch ---
            transformer_patch = {}
            if transformer_parameters:
                env_list = [
                    {"name": k, "value": str(v)}
                    for k, v in transformer_parameters.items()
                ]
                transformer_patch = {
                    "transformer": {
                        "containers": [
                            {
                                "name": f"{isvc_name}-transformer".lower(),
                                "image": transformer_image,
                                "env": env_list,
                            }
                        ]
                    }
                }

            # --- Model patch ---
            model_patch = {}
            if model_uri:
                model_patch["storageUri"] = model_uri
            if protocol_version:
                model_patch["protocolVersion"] = protocol_version
            if model_format:
                model_patch["modelFormat"] = {"name": model_format}

            predictor_patch = {"model": model_patch}

            # --- Canary rollout logic ---
            if canary_traffic_percent is not None:
                predictor_patch.update(
                    {
                        "canary": {"model": model_patch},
                        "canaryTrafficPercent": canary_traffic_percent,
                    }
                )

            # --- Final patch body ---
            patch_body = {
                "metadata": {"annotations": annotations_patch},
                "spec": {
                    "predictor": predictor_patch,
                    **transformer_patch,
                },
            }

            # Apply patch
            co_api.patch_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=isvc_name,
                body=patch_body,
            )

            msg = f"InferenceService '{isvc_name}' updated successfully "
            return msg

        except Exception as exp:
            raise exp

    @staticmethod
    def validate_canary_traffic_percent(
        isvc_name: str, canary_traffic_percent: int
    ) -> bool:
        """
        Validate the provided canary_traffic_percent value based on whether a canary
        spec already exists in the given InferenceService object.

        Rules:
          - If no canary exists yet → canary_traffic_percent must be between 1 and 99.
          - If canary already exists → canary_traffic_percent must be between 0 and 100.

        Args:
            isvc_name (str): Name of the KServe InferenceService.
            canary_traffic_percent (int, optional): Desired canary traffic percentage.

        Returns:
            bool: True if valid, otherwise raises ValueError.

        Raises:
            ValueError: If canary_traffic_percent violates the above rules.
        """

        isvc_obj = KServeClient().get(
            namespace=KubeflowPlugin().get_default_namespace(), name=isvc_name
        )
        # Check if canary already exists in the current ISVC
        canary_spec_exists = (
            isvc_obj.get("spec", {}).get("predictor", {}).get("canaryTrafficPercent")
            is not None
        )

        # Validation rules
        if canary_spec_exists:
            # Existing canary → allow 0–100 range (promotion, disable, update)
            if not 0 <= canary_traffic_percent <= 100:
                raise ValueError(
                    f"Invalid canary_traffic_percent={canary_traffic_percent}. "
                    "While promotion/disable/update, must be between 0 and 100."
                )
        else:
            # First-time rollout → must be partial (1–99)
            if not 1 <= canary_traffic_percent <= 99:
                raise ValueError(
                    f"Invalid canary_traffic_percent={canary_traffic_percent}. "
                    "For initial rollout, must be between 1 and 99."
                )

        # If all checks pass
        return True

    @staticmethod
    def serve_model(
        model_uri: str,
        isvc_name: str = None,
        model_id: str = None,
        model_name: str = None,
        model_version: str = None,
        dataset_id: str = None,
        transformer_image: str = None,
        transformer_parameters: dict = None,
        protocol_version: str = None,
        model_format: str = None,
        namespace: str = None,
    ):
        """
        Create a KServe InferenceService with optional transformer.

        Args:
            model_uri (str): URI of the model.
            isvc_name (str, optional): Name of the kserve instance.
            model_id (str, optional): Unique identifier for the model.
            model_name (str, optional): Name of the registered model.
            model_version (str, optional): Version of the registered model.
            dataset_id (str, optional): Linked dataset identifier.
            transformer_image (str): Image of the transformer.
            transformer_parameters (dict, optional): Dict containing:
            - "PROMETHEUS_URL": URL for Prometheus
            - "PROMETHEUS_METRICS": Comma-separated metrics
            Required if transformer_image is provided.
            protocol_version (str, optional): Protocol version for the model server (e.g., "v1", "v2").
            model_format (str, optional): Model format, e.g., "tensorflow", "pytorch", "sklearn", etc.
            namespace (str, optional): Namespace to deploy the InferenceService.
        """
        PluginManager().verify_activation(KubeflowPlugin().section)

        if namespace is None:
            namespace = utils.get_default_target_namespace()
        if isvc_name is None:
            now = datetime.now()
            date = now.strftime("%d%M")
            isvc_name = f"predictormodel{date}"

        # Predictor spec
        model_spec_kwargs = {
            "model_format": V1beta1ModelFormat(name=model_format),
            "storage_uri": model_uri,
        }
        if protocol_version:
            model_spec_kwargs["protocol_version"] = protocol_version

        predictor = V1beta1PredictorSpec(
            service_account_name="kserve-controller-s3",
            min_replicas=1,
            model=V1beta1ModelSpec(**model_spec_kwargs),
        )

        # Metadata annotations
        annotations = {
            "sidecar.istio.io/inject": "false",
            "model_name": model_name,
            "model_version": model_version,
            "model_id": model_id,
        }
        if dataset_id:
            annotations["dataset_id"] = str(dataset_id)

        # Transformer (optional)
        transformer = None
        if transformer_parameters:
            if not transformer_image:
                raise ValueError(
                    "transformer_image must be provided when transformer_parameters is set"
                )

            prometheus_url = transformer_parameters.get("PROMETHEUS_URL")
            prometheus_metrics = transformer_parameters.get("PROMETHEUS_METRICS")

            if not prometheus_url or not prometheus_metrics:
                raise ValueError(
                    "transformer_parameters must include both 'PROMETHEUS_URL' and 'PROMETHEUS_METRICS'"
                )

            container_name = f"{isvc_name}-transformer".lower()

            transformer = client.V1Container(
                name=container_name,
                image=transformer_image,
                env=[
                    client.V1EnvVar(name="PROMETHEUS_URL", value=prometheus_url),
                    client.V1EnvVar(
                        name="PROMETHEUS_METRICS", value=prometheus_metrics
                    ),
                ],
            )

        # Build InferenceService
        isvc_spec = V1beta1InferenceServiceSpec(predictor=predictor)
        if transformer:
            isvc_spec.transformer = client.V1PodSpec(containers=[transformer])

        isvc = V1beta1InferenceService(
            api_version=constants.KSERVE_V1BETA1,
            kind=constants.KSERVE_KIND,
            metadata=client.V1ObjectMeta(
                name=isvc_name,
                namespace=namespace,
                annotations=annotations,
            ),
            spec=isvc_spec,
        )

        # Create the service with error handling
        kserve = KServeClient()
        try:
            kserve.create(isvc)
            time.sleep(plugin_config.TIMER_IN_SEC)
            print(
                f"InferenceService '{isvc_name}' creation requested in namespace '{namespace}'."
            )
        except ApiException as e:
            if e.status == 409:  # Already exists
                print(
                    f"InferenceService '{isvc_name}' already exists in namespace '{namespace}'."
                )
            else:
                print(f"Failed to create InferenceService '{isvc_name}': {e.reason}")
                raise

    @staticmethod
    def _enabledex():
        """
        Enable Dex gRPC configuration by appending config to the pod and restarting the process.

        This function:
        1. Connects to Kubernetes cluster
        2. Appends gRPC configuration to /etc/dex/config.docker.yaml in the dex-auth-0 pod
        3. Restarts the Dex process by killing the current process

        Raises:
            Exception: If any Kubernetes operation fails
        """
        # Configuration
        pod_name = plugin_config.POD_NAME
        namespace = plugin_config.NAMESPACE
        container = plugin_config.CONTAINER

        try:
            # Load in-cluster Kubernetes config
            KubeflowPlugin().load_k8s_config()

            # Create Kubernetes API client
            v1 = client.CoreV1Api()

            logging.info(
                "Checking gRPC config in %s in namespace %s", pod_name, namespace
            )

            # Command to check if gRPC section already exists
            check_config_cmd = [
                "sh",
                "-c",
                f"grep -Eq '^[[:space:]]*grpc:[[:space:]]*$' {plugin_config.CONFIG_PATH}",
            ]

            # Check if gRPC section exists
            try:
                stream(
                    v1.connect_get_namespaced_pod_exec,
                    pod_name,
                    namespace,
                    command=check_config_cmd,
                    container=container,
                    stderr=True,
                    stdin=False,
                    stdout=True,
                    tty=False,
                )
                logging.info(
                    "gRPC section already exists in config file, skipping append"
                )
                grpc_exists = True
            except Exception:
                # grep returns non-zero exit code when pattern not found
                grpc_exists = False

            # Only append gRPC config if it doesn't exist
            if not grpc_exists:
                logging.info("gRPC section not found, appending configuration")

                # Command to append gRPC config to the Dex configuration file
                append_block = textwrap.dedent(
                    f"""\
                    cat <<'EOF' >> {plugin_config.CONFIG_PATH}
                    grpc:
                      addr: 0.0.0.0:{plugin_config.GRPC_PORT}
                      reflection: true
                    EOF
                    """
                )

                append_cmd = ["sh", "-c", append_block]

                # Execute command to append config
                stream(
                    v1.connect_get_namespaced_pod_exec,
                    pod_name,
                    namespace,
                    command=append_cmd,
                    container=container,
                    stderr=True,
                    stdin=False,
                    stdout=True,
                    tty=False,
                )

                logging.info("Successfully appended gRPC configuration")
                # Restart only if we changed the file.
                restart_cmd = ["sh", "-c", "kill $(pidof dex)"]
                logging.info("Restarting Dex process to apply gRPC config.")
                stream(
                    v1.connect_get_namespaced_pod_exec,
                    pod_name,
                    namespace,
                    command=restart_cmd,
                    container=container,
                    stderr=True,
                    stdin=False,
                    stdout=True,
                    tty=False,
                )
                logging.info("Dex process restart requested.")
            return True

        except Exception as e:
            logging.error("Failed to enable Dex gRPC: %s", e)
            raise Exception(f"Failed to enable Dex: {e}")

    @staticmethod
    def get_current_user_from_namespace() -> str:
        """
        Fetch the current Kubeflow user ID by reading the owner annotation
        from the user's namespace.

        Returns:
            str: The user ID of the notebook owner.

        Raises:
            RuntimeError: If the owner annotation is not found.
        """
        # 1️⃣ Get the notebook's namespace
        namespace_name = KubeflowPlugin().get_default_namespace()

        # 2️⃣ Load cluster Kubernetes configuration
        KubeflowPlugin().load_k8s_config()
        v1 = client.CoreV1Api()

        # 3️⃣ Fetch the namespace object
        ns_obj = v1.read_namespace(name=namespace_name)

        # 4️⃣ Get annotations
        annotations = ns_obj.metadata.annotations or {}

        # 5️⃣ Extract owner
        owner = annotations.get("owner")
        if not owner:
            raise RuntimeError(
                f"No owner annotation found in namespace: {namespace_name}"
            )

        return owner
