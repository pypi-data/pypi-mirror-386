# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Helper Utils for model deployment."""
import json
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional, Union

import azureml.automl.core.shared.constants as shared_constants
import captum
import pkg_resources
import saliency
import torch
from azureml.automl.core.inference import inference
from azureml.automl.core.shared import logging_utilities
from azureml.acft.common_components.image.runtime_common.classification.models.base_model_wrapper import \
    BaseModelWrapper

from azureml.acft.common_components import get_logger_app
from azureml.acft.common_components.image.runtime_common.common import utils
from azureml.acft.common_components.image.runtime_common.common.constants import \
    (MLFlowSchemaLiterals, ScoringLiterals)
from azureml.acft.common_components.image.runtime_common.common.exceptions import \
    AutoMLVisionDataException
from azureml.acft.common_components.image.runtime_common.explainability.constants import (
    ExplainabilityDefaults, ExplainabilityLiterals, XAIPredictionLiterals)
from azureml.acft.common_components.image.runtime_common.explainability.methods import load_xai_method
from azureml.acft.common_components.image.runtime_common.explainability.utils import (
    base64_to_img, validate_xai_parameters)
from azureml.acft.common_components.image.runtime_common.object_detection.models.base_model_wrapper import \
    BaseObjectDetectionModelWrapper
from azureml.acft.common_components.image.runtime_common.object_detection_yolo.models.yolo_wrapper import \
    YoloV5Wrapper
from azureml.core.run import Run, _OfflineRun

from mlflow.models.signature import ModelSignature
from mlflow.types.schema import ColSpec, Schema

logger = get_logger_app(__name__)


def _get_scoring_method(task_type: str, is_yolo: Optional[bool] = False) -> Callable[..., None]:
    """
    Return scoring method to be used at the inference time for the input task type.

    :param task_type: Task type used in training.
    :type task_type: str
    :param is_yolo: True if experiment is object detection yolo.
    :type is_yolo: bool
    :return: Scoring function corresponding to the task type.
    :rtype: Python method
    """
    from azureml.acft.common_components.image.runtime_common.classification.inference.score import \
        _score_with_model as _score_with_model_classifier
    from azureml.acft.common_components.image.runtime_common.object_detection.writers.score import \
        _score_with_model as _score_with_model_od
    from azureml.acft.common_components.image.runtime_common.object_detection_yolo.writers.score import \
        _score_with_model as _score_with_model_od_yolo

    if task_type in shared_constants.Tasks.ALL_IMAGE_CLASSIFICATION:
        return _score_with_model_classifier
    if task_type in shared_constants.Tasks.ALL_IMAGE_OBJECT_DETECTION and is_yolo:
        return _score_with_model_od_yolo
    # for object detection other than YOLO and Instance Segmentation _score_with_model_od will be used
    return _score_with_model_od


def _get_mlflow_signature(task_type: str) -> ModelSignature:
    """
    Return mlflow model signature with input and output schema given the input task type.

    :param task_type: Task type used in training.
    :type task_type: str
    :return: mlflow model signature.
    :rtype: mlflow.models.signature.ModelSignature
    """

    input_schema = Schema([ColSpec(MLFlowSchemaLiterals.INPUT_COLUMN_IMAGE_DATA_TYPE,
                                   MLFlowSchemaLiterals.INPUT_COLUMN_IMAGE)])
    if task_type in shared_constants.Tasks.ALL_IMAGE_CLASSIFICATION:

        output_schema = Schema([ColSpec(MLFlowSchemaLiterals.OUTPUT_COLUMN_DATA_TYPE,
                                        MLFlowSchemaLiterals.OUTPUT_COLUMN_FILENAME),
                                ColSpec(MLFlowSchemaLiterals.OUTPUT_COLUMN_DATA_TYPE,
                                        MLFlowSchemaLiterals.OUTPUT_COLUMN_PROBS),
                                ColSpec(MLFlowSchemaLiterals.OUTPUT_COLUMN_DATA_TYPE,
                                        MLFlowSchemaLiterals.OUTPUT_COLUMN_LABELS),
                                ColSpec(MLFlowSchemaLiterals.OUTPUT_COLUMN_XAI_VISUALIZATIONS_DATA_TYPE,
                                        XAIPredictionLiterals.VISUALIZATIONS_KEY_NAME),
                                ColSpec(MLFlowSchemaLiterals.OUTPUT_COLUMN_XAI_ATTRIBUTIONS_DATA_TYPE,
                                        XAIPredictionLiterals.ATTRIBUTIONS_KEY_NAME)])

    # for object detection and instance segmentation mlflow signature remains same
    else:
        output_schema = Schema([ColSpec(MLFlowSchemaLiterals.OUTPUT_COLUMN_DATA_TYPE,
                                        MLFlowSchemaLiterals.OUTPUT_COLUMN_FILENAME),
                                ColSpec(MLFlowSchemaLiterals.OUTPUT_COLUMN_DATA_TYPE,
                                        MLFlowSchemaLiterals.OUTPUT_COLUMN_BOXES)])

    return ModelSignature(inputs=input_schema, outputs=output_schema)


def prepare_model_export(run: Run, output_dir: str, task_type: str,
                         model_settings: Optional[Dict[str, Any]] = {},
                         save_as_mlflow: bool = False, is_yolo: bool = False) -> None:
    """Save model and weights to artifacts, generate score script and
        conda environment yml, and save run properties needed for model export

    :param run: The current azureml run object
    :type run: azureml.core.Run
    :param output_dir: Name of dir to save model files.
    :type output_dir: str
    :param task_type: Task type used in training.
    :type task_type: str
    :param model_settings: Settings for the model
    :type model_settings: dict
    :param save_as_mlflow: Flag to save as mlflow model
    :type save_as_mlflow: bool
    :param is_yolo: True if experiment is object detection yolo
    :type is_yolo: bool
    """
    from azureml.train.automl.runtime._azureautomlruncontext import AzureAutoMLRunContext
    automl_run_context = AzureAutoMLRunContext(run)

    # Initialize the artifact data dictionary for the current run
    strs_to_save = {shared_constants.RUN_ID_OUTPUT_PATH: run.id}
    mlflow_model_wrapper = None

    if save_as_mlflow:
        logger.info("save_as_mlflow flag is True, saving the model in MLFlow format.")
        from azureml.acft.common_components.image.runtime_common.common.mlflow.mlflow_model_wrapper import \
            MLFlowImagesModelWrapper
        mlflow_model_wrapper = MLFlowImagesModelWrapper(model_settings=model_settings,  # type:ignore
                                                        task_type=task_type,
                                                        scoring_method=_get_scoring_method(task_type, is_yolo))

    torch_model = torch.load(os.path.join(output_dir, shared_constants.PT_MODEL_FILENAME),
                             map_location='cpu')

    models_to_upload = {
        # load the checkpoint of the best model to be saved in outputs
        shared_constants.PT_MODEL_PATH: torch_model
    }

    # Save conda environment file into artifacts
    try:
        strs_to_save[shared_constants.CONDA_ENV_FILE_PATH] = _create_conda_env_file_content(run)
    except Exception as e:
        logger.warning("Failed to create conda environment file.")
        logging_utilities.log_traceback(e, logger)

    # Save scoring file into artifacts
    try:
        scoring_file_str = _get_scoring_file(run=run,
                                             task_type=task_type,
                                             model_settings=model_settings,
                                             is_yolo=is_yolo)
        strs_to_save[shared_constants.SCORING_FILE_PATH] = scoring_file_str
    except Exception as e:
        logger.warning("Failed to create score inference file.")
        logging_utilities.log_traceback(e, logger)

    # Upload files to artifact store
    mlflow_options = {shared_constants.MLFlowLiterals.WRAPPER: mlflow_model_wrapper,
                      shared_constants.MLFlowLiterals.SCHEMA_SIGNATURE: _get_mlflow_signature(task_type)}
    automl_run_context.batch_save_artifacts(working_directory=os.getcwd(),
                                            input_strs=strs_to_save,
                                            model_outputs=models_to_upload,
                                            save_as_mlflow=save_as_mlflow,
                                            mlflow_options=mlflow_options)

    # Get model artifacts file paths
    scoring_data_loc = automl_run_context._get_artifact_id(shared_constants.SCORING_FILE_PATH)
    conda_env_data_loc = automl_run_context._get_artifact_id(shared_constants.CONDA_ENV_FILE_PATH)
    model_artifacts_file = automl_run_context._get_artifact_id(shared_constants.PT_MODEL_PATH)

    # Add paths to run properties for model deployment
    properties_to_add = {
        inference.AutoMLInferenceArtifactIDs.ScoringDataLocation: scoring_data_loc,
        inference.AutoMLInferenceArtifactIDs.CondaEnvDataLocation: conda_env_data_loc,
        inference.AutoMLInferenceArtifactIDs.ModelDataLocation: model_artifacts_file
    }
    run.add_properties(properties_to_add)


def _create_conda_env_file_content(run: Run) -> Any:
    """
    Return conda/pip dependencies for the current run.

    If there are any changes to the conda environment file, the version of the conda environment
    file should be updated in the vendor.

    :param run: The current azureml run object
    :type run: azureml.core.run
    :return: Conda dependencies as string
    :rtype: str
    """
    env = run.get_environment()
    conda_deps = env.python.conda_dependencies

    # Add necessary extra package dependencies
    for conda_package in inference.get_local_conda_versions(inference.AutoMLVisionCondaPackagesList):
        conda_deps.add_conda_package(conda_package)

    # Add pytorch channel to download pytorch and torchvision
    conda_deps.add_channel('pytorch')

    # Renames environment to 'project environment' instead
    # using the default generated name
    conda_deps._conda_dependencies['name'] = 'project_environment'
    return conda_deps.serialize_to_string()


def _get_scoring_file(run: Run, task_type: str, model_settings: Optional[Dict[str, Any]] = {},
                      is_yolo: Optional[bool] = False) -> str:
    """
    Return scoring file to be used at the inference time.

    If there are any changes to the scoring file, the version of the scoring file should
    be updated in the vendor.
    :param run: The current azureml run object
    :type run: azureml.core.Run
    :param task_type: Task type used in training
    :type task_type: str
    :param model_settings: Settings for the model
    :type model_settings: dict
    :param is_yolo: True if experiment is object detection yolo
    :type is_yolo: bool
    :return: Scoring python file as a string
    :rtype: str
    """
    scoring_file_path = pkg_resources.resource_filename(
        inference.PACKAGE_NAME, os.path.join('inference', 'score_images.txt'))

    # Ensure correct path is used to import _score_with_model in the script
    score_path = 'object_detection_yolo.writers' if is_yolo else 'object_detection.writers'
    if task_type in shared_constants.Tasks.ALL_IMAGE_CLASSIFICATION:
        score_path = 'classification.inference'

    model_name = inference._get_model_name(run.id)

    if model_settings is None:
        model_settings = {}

    with open(scoring_file_path, 'r') as scoring_file_ptr:
        content = scoring_file_ptr.read()
        content = content.replace('<<model_filename>>', shared_constants.PT_MODEL_FILENAME)
        content = content.replace('<<task_type>>', task_type)
        content = content.replace('<<score_path>>', score_path)
        content = content.replace('<<model_name>>', model_name)
        content = content.replace('<<model_settings>>', json.dumps(model_settings).replace('null', 'None'))

    return content


def load_model(task_type: str,
               model_path: str,
               **model_settings: Dict[str, Any]) -> Union[BaseObjectDetectionModelWrapper,
                                                          YoloV5Wrapper,
                                                          BaseModelWrapper]:
    """Load model for model deployment

    :param task_type: Task type used in training.
    :type task_type: str
    :param model_path: Path to the model file
    :type model_path: str
    :param model_settings: Settings for the model
    :type model_settings: dict
    :return: Loaded model wrapper
    :rtype: typing.Union[object_detection.models.CommonObjectDetectionModelWrapper,
                         object_detection_yolo.models.Model,
                         classification.models.BaseModelWrapper]
    """
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    if task_type in shared_constants.Tasks.ALL_IMAGE_CLASSIFICATION:
        from azureml.acft.common_components.image.runtime_common.classification.common.classification_utils \
            import _load_model_wrapper as classification_load_model_wrapper
        return classification_load_model_wrapper(torch_model_file=model_path, distributed=False, local_rank=0,
                                                 device=device, model_settings=model_settings)
    else:
        from azureml.acft.common_components.image.runtime_common.object_detection.common.object_detection_utils \
            import _load_model_wrapper as od_load_model_wrapper
        return od_load_model_wrapper(torch_model_file=model_path, device=device, model_settings=model_settings)


def create_temp_file(request_body: bytes, dir: str) -> str:
    """ Create temporory file, save image and return path to the file

    :param request_body: Image
    :type request_body: bytes
    :param dir: directory name
    :type dir: str
    :return: Path to the file
    :rtype: str
    """
    with tempfile.NamedTemporaryFile(dir=dir, mode="wb", delete=False) as image_file_fp:
        image_file_fp.write(request_body)
        return image_file_fp.name


def get_xai_method(model: Union[BaseObjectDetectionModelWrapper, YoloV5Wrapper, BaseModelWrapper],
                   model_explainability: Optional[bool],
                   **kwargs  # type: Any
                   ) -> Union[saliency.core.xrai.XRAI,
                              captum.attr._core.noise_tunnel.NoiseTunnel,
                              captum.attr._core.guided_grad_cam.GuidedGradCam]:
    """ Get explainability algorithm object

    :param model: Model to use for inferencing
    :type model: typing.Union[object_detection.models.CommonObjectDetectionModelWrapper,
                              object_detection_yolo.models.Model,
                              classification.models.BaseModelWrapper]
    :param model_explainability: flag on whether to generate Explanations
    :type model_explainability: bool
    :return: XAI model object
    :rtype: typing.Union[saliency.core.xrai.XRAI,
                         captum.attr._core.noise_tunnel.NoiseTunnel,
                         captum.attr._core.guided_grad_cam.GuidedGradCam]
    """
    xai_method = None
    if model_explainability:
        validate_xai_parameters(**kwargs)
        xai_method = load_xai_method(model, kwargs.get(ExplainabilityLiterals.XAI_ALGORITHM,
                                                       ExplainabilityDefaults.XAI_ALGORITHM))
    return xai_method


def run_inference(model: Union[BaseObjectDetectionModelWrapper, YoloV5Wrapper, BaseModelWrapper],
                  request_body: bytes, score_with_model: Callable[..., None],
                  model_explainability: Optional[bool] = False,
                  **kwargs  # type: Any
                  ) -> bytes:
    """ Run inferencing for deployed models

    :param model: Model to use for inferencing
    :type model: typing.Union[object_detection.models.CommonObjectDetectionModelWrapper,
                              object_detection_yolo.models.Model,
                              classification.models.BaseModelWrapper]
    :param request_body: Data of image to score
    :type request_body: str
    :param score_with_model: method to be called for scoring
    :type score_with_model: Callable
    :param model_explainability: flag on whether to generate Explanations
    :type model_explainability: bool
    :return: Output of inferencing
    :rtype: bytes
    """
    with tempfile.TemporaryDirectory() as tmp_output_dir:
        with tempfile.NamedTemporaryFile(dir=tmp_output_dir, delete=False) as output_filename_fp, \
                tempfile.NamedTemporaryFile(dir=tmp_output_dir, mode="w", delete=False) as image_list_file_fp, \
                tempfile.NamedTemporaryFile(dir=tmp_output_dir, delete=False) as image_file_fp:

            image_file_fp.write(request_body)
            image_file_fp.flush()

            image_list_file_fp.write(image_file_fp.name)
            image_list_file_fp.flush()

            labeled_dataset_file_path = os.path.join(tmp_output_dir,
                                                     ScoringLiterals.LABELED_DATASET_FILE_NAME)

            root_dir = ""
            device = utils._get_default_device()

            xai_method = get_xai_method(model, model_explainability, **kwargs)

            score_with_model(model,
                             run=_OfflineRun(),
                             target_path=None,
                             output_file=output_filename_fp.name,
                             root_dir=root_dir,
                             image_list_file=image_list_file_fp.name,
                             labeled_dataset_file=labeled_dataset_file_path,
                             device=device,
                             num_workers=0,
                             model_explainability=model_explainability,
                             xai_method=xai_method,
                             **kwargs)
            output_filename_fp.flush()

            return output_filename_fp.read()


def run_inference_batch(model: Union[BaseObjectDetectionModelWrapper, YoloV5Wrapper, BaseModelWrapper],
                        mini_batch: List[str], score_with_model: Callable[..., None],
                        batch_size: Optional[int] = None,
                        model_explainability: Optional[bool] = False,
                        **kwargs  # type: Any
                        ) -> List[str]:
    """ Run inferencing for deployed models

    :param model: Model to use for inferencing
    :type model: typing.Union[object_detection.models.CommonObjectDetectionModelWrapper,
                              object_detection_yolo.models.Model,
                              classification.models.BaseModelWrapper]
    :param mini_batch: list of filepaths to images to score
    :type mini_batch: list[str]
    :param score_with_model: method to be called for scoring
    :type score_with_model: Callable
    :param batch_size: batch size for inferencing
    :type batch_size: int
    :param model_explainability: flag on whether to generate Explanations
    :type model_explainability: bool
    :return: Output of inferencing
    :rtype: list[str]
    """

    # TODO: refactor the run_inference_batch() to take list of images

    with tempfile.TemporaryDirectory() as tmp_output_dir:
        with tempfile.NamedTemporaryFile(dir=tmp_output_dir,
                                         mode="w", delete=False) as image_list_file_fp:

            image_list_file_fp.write('\n'.join(mini_batch))
            image_list_file_fp.flush()

            device = utils._get_default_device()
            output_file_path = os.path.join(tmp_output_dir,
                                            ScoringLiterals.PREDICTION_FILE_NAME)
            xai_method = get_xai_method(model, model_explainability, **kwargs)
            labeled_dataset_file_path = os.path.join(tmp_output_dir,
                                                     ScoringLiterals.LABELED_DATASET_FILE_NAME)

            if batch_size:
                logger.info(f"Scoring with batch size: {batch_size}.")
                score_with_model(model,
                                 run=_OfflineRun(),
                                 target_path=None,
                                 output_file=output_file_path,
                                 root_dir="",
                                 image_list_file=image_list_file_fp.name,
                                 labeled_dataset_file=labeled_dataset_file_path,
                                 device=device,
                                 batch_size=batch_size,
                                 num_workers=0,
                                 model_explainability=model_explainability,
                                 xai_method=xai_method,
                                 **kwargs)
            else:
                logger.info("Scoring with default value for batch size.")
                score_with_model(model,
                                 run=_OfflineRun(),
                                 target_path=None,
                                 output_file=output_file_path,
                                 root_dir="",
                                 image_list_file=image_list_file_fp.name,
                                 labeled_dataset_file=labeled_dataset_file_path,
                                 device=device,
                                 num_workers=0,
                                 model_explainability=model_explainability,
                                 xai_method=xai_method,
                                 **kwargs)

            logger.info("Finished batch inferencing")

            results = []
            with open(output_file_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip('\n')
                    results.append(line)

            return results


def run_inference_helper(model: Union[BaseObjectDetectionModelWrapper, YoloV5Wrapper, BaseModelWrapper],
                         request_body: bytes, score_with_model: Callable[..., None],
                         task_type: str) -> bytes:
    """ Run inferencing for deployed models

    :param model: Model to use for inferencing
    :type model: typing.Union[object_detection.models.CommonObjectDetectionModelWrapper,
                              object_detection_yolo.models.Model,
                              classification.models.BaseModelWrapper]
    :param request_body: Data of image to score
    :type request_body: str
    :param score_with_model: method to be called for scoring
    :type score_with_model: Callable
    :param task_type: task type
    :type task_type: str
    :return: Output of inferencing
    :rtype: bytes
    """
    try:
        logger.info("Attempting to parse request as JSON string.")
        request_body = json.loads(request_body)
    except ValueError:
        logger.info("Input is not a valid json string.")

    if isinstance(request_body, dict):
        logger.info("Running inference with json input.")

        if (
            request_body.get(
                ExplainabilityLiterals.MODEL_EXPLAINABILITY,
                ExplainabilityDefaults.MODEL_EXPLAINABILITY,
            )
            and task_type in shared_constants.Tasks.ALL_IMAGE_CLASSIFICATION
        ):
            model_explainability = True
            xai_extra_params = request_body.get(ExplainabilityLiterals.XAI_PARAMETERS, {})

        else:  # for cases where XAI is False and detection/segmentation
            model_explainability = False
            xai_extra_params = {}

        # online inference on an image
        return run_inference(model,
                             base64_to_img(request_body["image"]),
                             score_with_model,
                             model_explainability=model_explainability,
                             **xai_extra_params
                             )
    elif isinstance(request_body, bytes):  # if it is bytes
        # backward compatibility
        logger.info("Running inference with image in bytes.")
        return run_inference(model, request_body, score_with_model)
    else:
        logger.info("Input data format is incompatible.")
        raise AutoMLVisionDataException(
            "Incompatible input format",
            has_pii=False,
        )
