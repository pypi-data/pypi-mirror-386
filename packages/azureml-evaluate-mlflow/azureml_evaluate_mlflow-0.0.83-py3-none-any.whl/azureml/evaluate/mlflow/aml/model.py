# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from abc import ABC, abstractmethod, ABCMeta
from logging import getLogger
from typing import Union, List, Any, Dict
import posixpath

import azureml.evaluate.mlflow as azureml_mlflow
from azureml.evaluate.mlflow.exceptions import AzureMLMLFlowUserException
import pandas as pd
import numpy as np
from mlflow.pyfunc import PythonModelContext
import os
import shutil
import yaml
import cloudpickle
from scipy.sparse import csc_matrix, csr_matrix
from mlflow.models import Model
from mlflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE
from mlflow.models.model import MLMODEL_FILE_NAME
from mlflow.utils.file_utils import TempDir, _copy_file_or_tree
from mlflow.utils.requirements_utils import _get_pinned_requirement
from mlflow.utils.file_utils import write_to
from mlflow.utils.model_utils import _get_flavor_configuration
from mlflow.tracking.artifact_utils import _download_artifact_from_uri
from mlflow.utils.environment import (
    _mlflow_conda_env,
    _process_pip_requirements,
    _process_conda_env,
    _CONDA_ENV_FILE_NAME,
    _REQUIREMENTS_FILE_NAME,
    _CONSTRAINTS_FILE_NAME,
    _PYTHON_ENV_FILE_NAME,
    _PythonEnv,
)

logger = getLogger(__name__)

AzureMLInput = Union[pd.DataFrame, np.ndarray, csc_matrix, csr_matrix, List[Any], Dict[str, Any]]
AzureMLOutput = Union[pd.DataFrame, pd.Series, np.ndarray, list]

CONFIG_KEY_ARTIFACTS = "artifacts"
CONFIG_KEY_ARTIFACT_RELATIVE_PATH = "path"
CONFIG_KEY_ARTIFACT_URI = "uri"
CONFIG_KEY_aml_model = "aml_model"
CONFIG_KEY_CLOUDPICKLE_VERSION = "cloudpickle_version"


def get_default_pip_requirements():
    """
    :return: A list of default pip requirements for MLflow Models produced by this flavor.
             Calls to :func:`save_model()` and :func:`log_model()` produce a pip environment
             that, at minimum, contains these requirements.
    """
    return [_get_pinned_requirement("cloudpickle")]


def get_default_conda_env():
    """
    :return: The default Conda environment for MLflow Models produced by calls to
             :func:`save_model() <mlflow.aml.save_model>`
             and :func:`log_model() <mlflow.aml.log_model>` when a user-defined subclass of
             :class:`PythonModel` is provided.
    """
    return _mlflow_conda_env(additional_pip_deps=get_default_pip_requirements())


def _load_model_env(path):
    """
    Get ENV file string from a model configuration stored in Python Function format.
    Returned value is a model-relative path to a Conda Environment file,
    or None if none was specified at model save time
    """
    return _get_flavor_configuration(model_path=path, flavor_name=azureml_mlflow.aml.FLAVOR_NAME) \
        .get(azureml_mlflow.aml.ENV, None)


def _save_model_with_class_artifacts_params(
        path,
        aml_model,
        artifacts=None,
        conda_env=None,
        code_paths=None,
        mlflow_model=None,
        pip_requirements=None,
        extra_pip_requirements=None,
):
    """
    :param path: The path to which to save the AzureML model.
    :param aml_model: An instance of a subclass of :class:`~AzureMLModel`. ``aml_model``
                        defines how the model loads artifacts and how it performs inference.
    :param artifacts: A dictionary containing ``<name, artifact_uri>`` entries.
                      Remote artifact URIs
                      are resolved to absolute filesystem paths, producing a dictionary of
                      ``<name, absolute_path>`` entries. ``aml_model`` can reference these
                      resolved entries as the ``artifacts`` property of the ``context``
                      attribute. If ``None``, no artifacts are added to the model.
    :param conda_env: Either a dictionary representation of a Conda environment or the
                      path to a Conda environment yaml file. If provided, this decsribes the
                      environment this model should be run in. At minimum, it should specify
                      the dependencies
                      contained in :func:`get_default_conda_env()`. If ``None``, the default
                      :func:`get_default_conda_env()` environment is added to the model.
    :param code_paths: A list of local filesystem paths to Python file dependencies (or directories
                       containing file dependencies). These files are *prepended* to the system
                       path before the model is loaded.
    :param mlflow_model: The model configuration to which to add the ``mlflow.aml`` flavor.
    """
    if mlflow_model is None:
        mlflow_model = Model()

    custom_model_config_kwargs = {
        CONFIG_KEY_CLOUDPICKLE_VERSION: cloudpickle.__version__,
    }
    if isinstance(aml_model, AzureMLModel):
        saved_aml_model_subpath = "aml_model.pkl"
        with open(os.path.join(path, saved_aml_model_subpath), "wb") as out:
            cloudpickle.dump(aml_model, out)
        custom_model_config_kwargs[CONFIG_KEY_aml_model] = saved_aml_model_subpath
    else:
        raise AzureMLMLFlowUserException(
            message=(
                "`aml_model` must be a subclass of `AzureMLModel`. Instead, found an"
                " object of type: {aml_model_type}".format(aml_model_type=type(aml_model))
            ),
            error_code=INVALID_PARAMETER_VALUE,
        )

    if artifacts:
        saved_artifacts_config = {}
        with TempDir() as tmp_artifacts_dir:
            tmp_artifacts_config = {}
            saved_artifacts_dir_subpath = "artifacts"
            for artifact_name, artifact_uri in artifacts.items():
                tmp_artifact_path = _download_artifact_from_uri(
                    artifact_uri=artifact_uri, output_path=tmp_artifacts_dir.path()
                )
                tmp_artifacts_config[artifact_name] = tmp_artifact_path
                saved_artifact_subpath = posixpath.join(
                    saved_artifacts_dir_subpath,
                    os.path.relpath(path=tmp_artifact_path, start=tmp_artifacts_dir.path()),
                )
                saved_artifacts_config[artifact_name] = {
                    CONFIG_KEY_ARTIFACT_RELATIVE_PATH: saved_artifact_subpath,
                    CONFIG_KEY_ARTIFACT_URI: artifact_uri,
                }

            shutil.move(tmp_artifacts_dir.path(), os.path.join(path, saved_artifacts_dir_subpath))
        custom_model_config_kwargs[CONFIG_KEY_ARTIFACTS] = saved_artifacts_config

    saved_code_subpath = None
    if code_paths is not None:
        saved_code_subpath = "code"
        for code_path in code_paths:
            _copy_file_or_tree(src=code_path, dst=path, dst_dir=saved_code_subpath)

    azureml_mlflow.aml.add_to_model(
        model=mlflow_model,
        loader_module=__name__,
        code=saved_code_subpath,
        env=_CONDA_ENV_FILE_NAME,
        **custom_model_config_kwargs,
    )
    mlflow_model.save(os.path.join(path, MLMODEL_FILE_NAME))

    if conda_env is None:
        if pip_requirements is None:
            default_reqs = get_default_pip_requirements()
            # To ensure `_load_azureml` can successfully load the model during the dependency
            # inference, `mlflow_model.save` must be called beforehand to save an MLmodel file.
            inferred_reqs = azureml_mlflow.models.infer_pip_requirements(
                path,
                azureml_mlflow.aml.FLAVOR_NAME,
                fallback=default_reqs,
            )
            default_reqs = sorted(set(inferred_reqs).union(default_reqs))
        else:
            default_reqs = None
        conda_env, pip_requirements, pip_constraints = _process_pip_requirements(
            default_reqs,
            pip_requirements,
            extra_pip_requirements,
        )
    else:
        conda_env, pip_requirements, pip_constraints = _process_conda_env(conda_env)

    with open(os.path.join(path, _CONDA_ENV_FILE_NAME), "w") as f:
        yaml.safe_dump(conda_env, stream=f, default_flow_style=False)

    # Save `constraints.txt` if necessary
    if pip_constraints:
        write_to(os.path.join(path, _CONSTRAINTS_FILE_NAME), "\n".join(pip_constraints))

    # Save `requirements.txt`
    write_to(os.path.join(path, _REQUIREMENTS_FILE_NAME), "\n".join(pip_requirements))

    _PythonEnv.current().to_yaml(os.path.join(path, _PYTHON_ENV_FILE_NAME))


class AzureMLModel:
    """
    Represents a generic Python model that evaluates inputs and produces API-compatible outputs.
    By subclassing :class:`~PythonModel`, users can create customized MLflow models with the
    "python_function" ("pyfunc") flavor, leveraging custom inference logic and artifact
    dependencies.
    """

    __metaclass__ = ABCMeta

    def load_context(self, context):
        """
        Loads artifacts from the specified :class:`~PythonModelContext` that can be used by
        :func:`~AzureMLModel.predict` when evaluating inputs. When loading an MLflow model with
        :func:`~load_model`, this method is called as soon as the :class:`~AzureMLModel` is
        constructed.

        The same :class:`~PythonModelContext` will also be available during calls to
        :func:`~PythonModel.predict`, but it may be more efficient to override this method
        and load artifacts from the context at model load time.

        :param context: A :class:`~PythonModelContext` instance containing artifacts that the model
                        can use to perform inference.
        """


class AzureMLClassifierModel(AzureMLModel, ABC):
    @abstractmethod
    def predict(self, context, model_input):
        """
        Evaluates an azureml-compatible input and produces an azureml-compatible output.
        For more information about the azureml input/output API, see the :ref:`pyfunc-inference-api`.

        :param context: A :class:`~PythonModelContext` instance containing artifacts that the model
                        can use to perform inference.
        :param model_input: An azureml-compatible input for the model to evaluate.
        """

    @abstractmethod
    def predict_proba(self, context, model_input):
        """
        Evaluates an azureml-compatible input and produces an azureml-compatible output.
        For more information about the azureml input/output API, see the :ref:`pyfunc-inference-api`.

        :param context: A :class:`~PythonModelContext` instance containing artifacts that the model
                        can use to perform inference.
        :param model_input: An azureml-compatible input for the model to evaluate.
        """


class AzureMLGenericModel(AzureMLModel, ABC):
    @abstractmethod
    def predict(self, context, model_input):
        """
        Evaluates an azureml-compatible input and produces an azureml-compatible output.
        For more information about the azureml input/output API, see the :ref:`pyfunc-inference-api`.

        :param context: A :class:`~PythonModelContext` instance containing artifacts that the model
                        can use to perform inference.
        :param model_input: An azureml-compatible input for the model to evaluate.
        """


class AzureMLForecastModel(AzureMLModel, ABC):
    @abstractmethod
    def forecast(self, context, model_input, input_context):
        """
        API to be implemented by forecasting models. Evaluates an azureml-compatible input and produces an
        azureml-compatible output.
        For more information about the azureml input/output API, see the :ref:`pyfunc-inference-api`.

        :param context: A :class:`~PythonModelContext` instance containing artifacts that the model
                        can use to perform inference.
        :param model_input: An azureml-compatible input for the model to forecast.
        :param input_context: Input context"""


def _load_azureml(model_path):
    aml_config = _get_flavor_configuration(
        model_path=model_path, flavor_name=azureml_mlflow.aml.FLAVOR_NAME
    )

    aml_model_cloudpickle_version = aml_config.get(CONFIG_KEY_CLOUDPICKLE_VERSION, None)
    if aml_model_cloudpickle_version is None:
        azureml_mlflow.aml._logger.warning(
            "The version of CloudPickle used to save the model could not be found in the MLmodel"
            " configuration"
        )
    elif aml_model_cloudpickle_version != cloudpickle.__version__:
        # CloudPickle does not have a well-defined cross-version compatibility policy. Micro version
        # releases have been known to cause incompatibilities. Therefore, we match on the full
        # library version
        azureml_mlflow.aml._logger.warning(
            "The version of CloudPickle that was used to save the model, `CloudPickle %s`, differs"
            " from the version of CloudPickle that is currently running, `CloudPickle %s`, and may"
            " be incompatible",
            aml_model_cloudpickle_version,
            cloudpickle.__version__,
        )

    aml_model_subpath = aml_config.get(CONFIG_KEY_aml_model, None)
    if aml_model_subpath is None:
        raise AzureMLMLFlowUserException("Python model path was not specified in the model configuration.")
    with open(os.path.join(model_path, aml_model_subpath), "rb") as f:
        aml_model = cloudpickle.load(f)

    artifacts = {}
    for saved_artifact_name, saved_artifact_info in aml_config.get(
            CONFIG_KEY_ARTIFACTS, {}
    ).items():
        artifacts[saved_artifact_name] = os.path.join(
            model_path, saved_artifact_info[CONFIG_KEY_ARTIFACT_RELATIVE_PATH]
        )

    context = PythonModelContext(artifacts=artifacts, model_config=None)
    aml_model.load_context(context=context)
    return _AzureMLModelWrapper(aml_model=aml_model, context=context)


class _AzureMLModelWrapper:
    def __init__(self, aml_model, context):
        """
        :param aml_model: An instance of a subclass of :class:`~PythonModel`.
        :param context: A :class:`~PythonModelContext` instance containing artifacts that
                        ``aml_model`` may use when performing inference.
        """
        self.aml_model = aml_model
        self.context = context

    def predict(self, model_input):
        return self.aml_model.predict(self.context, model_input)

    def predict_proba(self, model_input):
        return self.aml_model.predict_proba(self.context, model_input)

    def generate(self, model_input):
        return self.aml_model.generate(self.context, model_input)

    def forecast(self, model_input):
        return self.aml_model.forecast(self.context, model_input)
