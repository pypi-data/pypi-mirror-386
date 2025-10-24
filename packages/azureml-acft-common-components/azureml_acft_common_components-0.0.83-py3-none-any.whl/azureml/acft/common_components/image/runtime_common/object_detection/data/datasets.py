# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Classes and functions to ingest data for object detection."""
import copy
import json
import os
import numpy as np
import time
import torch

from collections import defaultdict
from PIL.Image import BILINEAR
from sklearn.model_selection import train_test_split
from torchvision.transforms import transforms
from typing import Any, Dict, DefaultDict, Optional, List, Tuple, TypeVar

from azureml.automl.core.shared import logging_utilities

from azureml.acft.common_components import get_logger_app
from azureml.acft.common_components.image.runtime_common.common.aml_dataset_base_wrapper import \
    AmlDatasetBaseWrapper
from azureml.acft.common_components.image.runtime_common.common.constants import SettingsLiterals, \
    TrainingCommonSettings
from azureml.acft.common_components.image.runtime_common.common.exceptions import AutoMLVisionDataException
from azureml.acft.common_components.image.runtime_common.common.dataset_helper import AmlDatasetHelper
from azureml.acft.common_components.image.runtime_common.common.tiling_utils import validate_tiling_settings
from azureml.acft.common_components.image.runtime_common.common.utils import _validate_image_exists
from azureml.acft.common_components.image.runtime_common.object_detection.common.augmentations \
    import transform as augmentations_transform
from azureml.acft.common_components.image.runtime_common.object_detection.common.constants \
    import DatasetFieldLabels, PredefinedLiterals
from azureml.acft.common_components.image.runtime_common.object_detection.common.masktools import \
    decode_rle_masks_as_binary_mask
from azureml.acft.common_components.image.runtime_common.object_detection.common.tiling_helper import \
    generate_tiles_annotations
from azureml.acft.common_components.image.runtime_common.object_detection.data.object_annotation import \
    ObjectAnnotation
from azureml.acft.common_components.image.runtime_common.common.tiling_dataset_element import TilingDatasetElement
from azureml.acft.common_components.image.runtime_common.common.system_meter import SystemMeter

logger = get_logger_app(__name__)


# Upper limit for sum of mask dimensions for instance segmentation. The original image and the object masks are
# downsampled together so that the limit is not exceeded.
MAX_MASK_PIXELS_PER_IMAGE = 500_000_000


T_co = TypeVar('T_co', covariant=True)

system_meter = SystemMeter(log_static_sys_info=True)


def log_memory_usage(is_train: bool, before_dataset_creation: bool = True):
    """ Log the memory usage
    :param is_train: Whether it is a train dataset or not
    :type is_train: boolean
    :param before_dataset_creation: Whether it is called before dataset creation method or after. The log message
    is changed accordingly.
    :type is_train: boolean
    :return: None
    """
    log_message = 'reading training dataset' if is_train else 'reading validation dataset'
    if not before_dataset_creation:
        log_message = f'Finished {log_message}'

    logger.info(log_message)
    system_meter.log_system_stats()


class CommonObjectDetectionDataset:
    """Common object detection dataset"""

    def __init__(self, is_train: bool = False, prob: float = 0.5, ignore_data_errors: bool = True,
                 transform: transforms = None, use_bg_label: bool = True, label_compute_func: Any = None,
                 settings: Optional[Dict[str, Any]] = None, masks_required: bool = False,
                 tile_grid_size: Optional[Tuple[int, int]] = None, tile_overlap_ratio: Optional[float] = None,
                 use_cv2: bool = False) -> None:
        """
        :param is_train: which mode (training, inference) is the network in?
        :type is_train: bool
        :param prob: target probability of randomness for each augmentation method
        :type prob: float
        :param ignore_data_errors: boolean flag on whether to ignore input data errors
        :type ignore_data_errors: bool
        :param transform: function to apply for data transformation
        :type transform: function that gets 2 parameters: image tensor and targets tensor
        :param use_bg_label: flag to indicate if we use incluse the --bg-- label
        :type use_bg_label: bool
        :param label_compute_func: function to use when computing labels
        :type label_compute_func: func
        :param settings: additional settings to be used in the dataset
        :type settings: dict
        :param masks_required: If masks information is required
        :type masks_required: bool
        :param tile_grid_size: The grid size to split the image into, if tiling is enabled. None, otherwise
        :type tile_grid_size: Tuple[int, int]
        :param tile_overlap_ratio: Overlap ratio between adjacent tiles in each dimension.
                                   None, if tile_grid_size is None
        :type tile_overlap_ratio: float
        :param use_cv2: Use cv2 for reading image dimensions
        :type use_cv2: bool
        """
        self._is_train = is_train
        self._prob = prob
        self._ignore_data_errors = ignore_data_errors
        self._transform = transform
        self._use_bg_label = use_bg_label
        self._label_compute_func = label_compute_func
        self._settings = settings
        validate_tiling_settings(tile_grid_size, tile_overlap_ratio)
        self._tile_grid_size = tile_grid_size
        self._tile_overlap_ratio = tile_overlap_ratio
        self._use_cv2 = use_cv2

        self._image_elements: List[TilingDatasetElement] = []
        self._annotations: DefaultDict[TilingDatasetElement, Any] = defaultdict(list)
        self._image_tiles: DefaultDict[TilingDatasetElement, Any] = defaultdict(list)
        # List of all dataset elements (with both images and tiles)
        self._dataset_elements: List[TilingDatasetElement] = []

        self._object_classes: List[str] = []
        self._class_to_index_map: Dict[str, Any] = {}
        self._labels = None
        # when self is a subset of a dataset, self._indices is not None
        self._indices = None
        self._masks_required = masks_required
        self.apply_mosaic = True if settings is None else settings.get(
            SettingsLiterals.APPLY_MOSAIC_FOR_YOLO, True)
        self.apply_automl_train_augmentations = True if settings is None else settings.get(
            SettingsLiterals.APPLY_AUTOML_TRAIN_AUGMENTATIONS, True)

    def __len__(self):
        """Get number of records in dataset

        :return: Number of records
        :rtype: int
        """
        if self._indices is not None:
            return len(self._indices)
        else:
            return len(self._image_elements)

    def get_image_label_info(self, dataset_element: TilingDatasetElement):
        """Get the image and supervision data.

        :param dataset_element: Dataset element to fetch
        :type dataset_element: TilingDatasetElement
        :return: Image, bounding box information, and image information, with form:
                 -Image: Torch tensor
                 -Labels: Dictionary with keys "boxes" and "labels", where boxes is a list of lists of
                          pixel coordinates, and "labels" is a list of integers with the class of each bounding box,
                          and optionally masks if there are masks in the image annotations
                 -Image Information: is a dictionary with the image url, image width and height,
                                     and a list of areas of the different bounding boxes
        :rtype: Tuple of form (Torch Tensor, Dictionary, Dictionary)
        """
        from azureml.acft.common_components.image.runtime_common.common.utils import _read_image
        image = _read_image(self._ignore_data_errors, dataset_element.image_url, tile=dataset_element.tile)
        if image is None:
            return None, {}, {}

        annotations = self._annotations[dataset_element]

        # If the number of objects x the image resolution exceeds threshold, then downsample the image to prevent OOMs.
        image = self._downsample_for_instance_segmentation(image, annotations)

        height = image.height
        width = image.width

        bounding_boxes = []
        classes = []
        iscrowd = []
        raw_masks = []

        for annotation in annotations:
            self._fill_missing_fields_annotation(annotation, height=height, width=width)
            bounding_boxes.append(annotation.bounding_box)
            annotation_index = self._class_to_index_map[annotation.label]
            classes.append(annotation_index)
            iscrowd.append(annotation.iscrowd)

            # Convert masks to tensors if they are present
            if annotation.rle_masks is not None:
                mask = decode_rle_masks_as_binary_mask(annotation.rle_masks)
                raw_masks.append(torch.as_tensor(mask, dtype=torch.uint8))

        # Get the boxes, classes and masks as tensors. If not an instance segmentation task, then set masks to `None`.
        boxes = torch.as_tensor(bounding_boxes, dtype=torch.float32)
        labels = torch.as_tensor(classes, dtype=torch.int64)
        if self._masks_required:
            masks = torch.stack(raw_masks) if len(raw_masks) > 0 \
                else torch.zeros((0,), dtype=boxes.dtype, device=boxes.device)
        else:
            masks = None

        # If the image does not have any objects, ensure that the dimensions of the boxes, classes and masks are valid,
        # eg (0, 4) for boxes.
        if (len(boxes) == 0) and (len(labels) == 0) and ((masks is None) or (len(masks) == 0)):
            boxes = torch.zeros((0, 4), dtype=boxes.dtype, device=boxes.device)
            labels = torch.zeros((0,), dtype=labels.dtype, device=labels.device)
            if masks is not None:
                masks = torch.zeros((0, height, width), dtype=masks.dtype, device=masks.device)
                # Warn about lack of masks.
                logger.warning(f"(train: {self._is_train}) No valid masks for image.")

        original_width = width
        original_height = height

        # data augmentations
        image, boxes, areas, height, width, masks = augmentations_transform(
            image, boxes, self._is_train, self.apply_automl_train_augmentations, self._prob, self._transform, masks)

        # Only keep valid bounding boxes after transform. Warn if no valid bounding boxes are left.
        boxes, labels, iscrowd, areas, masks = \
            self._filter_invalid_bounding_boxes(boxes, labels, iscrowd, areas, width, height, masks)
        if not boxes.shape[0]:
            logger.warning(f"(train: {self._is_train}) No valid bbox for image after transform.")

        training_labels = {"boxes": boxes,
                           "labels": labels}

        # Only include masks if they have been computed
        if masks is not None:
            training_labels["masks"] = masks

        image_info = {"areas": areas, "iscrowd": iscrowd, "filename": dataset_element.image_url,
                      "height": height, "width": width, "original_height": original_height,
                      "original_width": original_width}

        if dataset_element.tile is not None:
            # the default_collate function used in PredictionDataset has issues with None values in item
            # returned by dataset. See __getitem__() function in PredictionDataset for more info.
            # Even though the collate function for this dataset has no issues,
            # adding tile only when it is not None to keep it consistent with PredictionDataset.
            image_info.update({"tile": dataset_element.tile})

        return (image, training_labels, image_info)

    def get_image_label_info_for_image_url(self, image_url: str):
        """Get the image and supervision data for an image url.

        Syntactic sugar for `get_image_label_info()` that allows the caller to not know about tiling. Makes a tiling
        element for the entire image.

        :param image_url: The url of the image to be returned together with supervision data.
        :type image_url: str
        :return: Image, bounding box information, and image information, with form:
                 -Image: Torch tensor
                 -Labels: Dictionary with keys "boxes" and "labels", where boxes is a list of lists of
                          pixel coordinates, and "labels" is a list of integers with the class of each bounding box,
                          and optionally masks if there are masks in the image annotations
                 -Image Information: is a dictionary with the image url, image width and height,
                                     and a list of areas of the different bounding boxes
        :rtype: Tuple of form (Torch Tensor, Dictionary, Dictionary)
        """

        return self.get_image_label_info(TilingDatasetElement(image_url, None))

    @staticmethod
    def _downsample_for_instance_segmentation(image, annotations):
        """For instance segmentation tasks only, downsample the image so its object masks do not lead to OOM.

        :param image: Image data.
        :type image: PIL.Image
        :param annotations: Annotations for the image
        :type annotations: List[ObjectAnnotation]
        :return: Image whose object masks do not cause OOM.
        :rtype: PIL.Image
        """

        # Get the number of objects for instance segmentation. This is 0 if the task is not instance segmentation.
        num_objects_with_masks = sum(map(lambda a: a.has_valid_mask, annotations))  # type: ignore[no-any-return]

        # Calculate the downsampling factor s that makes N x (W/s) x (H/s) equal to threshold.
        downsampling_factor = np.sqrt(
            float(num_objects_with_masks * image.width * image.height) / MAX_MASK_PIXELS_PER_IMAGE
        )

        # Downsample the image if N x W x H is greater than threshold.
        if downsampling_factor > 1.0:
            downsampled_width = int(image.width / downsampling_factor)
            downsampled_height = int(image.height / downsampling_factor)
            logger.warning(
                f"Downsampling {image.width}x{image.height} image with "
                f"{num_objects_with_masks} objects by {downsampling_factor:.2f} to "
                f"{downsampled_width}x{downsampled_height}."
            )
            image = image.resize((downsampled_width, downsampled_height), BILINEAR)

        return image

    @staticmethod
    def _fill_missing_fields_annotation(annotation, height=None, width=None):
        """Fills object annotation in place

        :param annotation: annotation object
        :type annotation: azureml.automl.dnn.vision.object_detection.data.datasets.ObjectAnnotation
        :param height: image height in pixels
        :type height: int
        :param width: image width in pixels
        :type width: int
        """
        if height is None or width is None:
            raise AutoMLVisionDataException("width or height cannot be None", has_pii=False)

        if annotation.missing_properties:
            annotation.fill_box_properties(width=width, height=height)

    @staticmethod
    def _filter_invalid_bounding_boxes(boxes, labels, iscrowd, areas, image_width, image_height, masks=None):
        """validate bbox w/ condition of (x_min < x_max and y_min < y_max)
        and return the valid boxes and corresponding labels, iscrowd and areas.

        :param boxes: Tensor containing bounding box co-ordinates in (x_min, y_min, x_max, y_max) format.
        :type boxes: torch.Tensor of shape (N, 4)
        :param labels: Bounding box labels.
        :type labels: torch.Tensor of shape (N)
        :param iscrowd: iscrowd values for the bounding boxes.
        :type iscrowd: List
        :param areas: Bounding box areas.
        :type areas: List
        :param image_width: image width in pixels
        :type image_width: int
        :param image_height: image height in pixels
        :type image_height: int
        :param masks (optional): Tensor containing mask data
        :type masks (optional): Tensor
        :return: Valid bounding boxes and corresponding labels, iscrowd and areas.
        :rtype: tensor, tensor, List, List
        """
        if len(boxes) == 0:
            return boxes, labels, iscrowd, areas, masks

        coordinates_ordered = (boxes[:, 0] < boxes[:, 2]) * (boxes[:, 1] < boxes[:, 3])
        within_bounds = (boxes[:, 0] >= 0) * (boxes[:, 2] <= image_width) * \
                        (boxes[:, 1] >= 0) * (boxes[:, 3] <= image_height)
        is_valid = coordinates_ordered * within_bounds
        valid_boxes = boxes[is_valid, :]
        valid_labels = labels[is_valid]
        iscrowd = torch.as_tensor(iscrowd, dtype=torch.int8)
        valid_iscrowd = iscrowd[is_valid].tolist()
        valid_areas = torch.as_tensor(areas, dtype=torch.float32)
        valid_areas_list = valid_areas[is_valid].tolist()

        valid_masks = None
        if masks is not None:
            valid_masks = masks[is_valid]

        return valid_boxes, valid_labels, valid_iscrowd, valid_areas_list, valid_masks

    @property
    def num_classes(self):
        """Get number of classes in dataset

        :return: Number of classes in dataset
        :rtype: int
        """
        return len(self._object_classes)

    @property
    def classes(self):
        """Get list of classes in dataset

        :return: List of classses
        :rtype: List of strings
        """
        return self._object_classes

    @property
    def transform(self):
        """The post augmentation transform.

        :return: the transform function
        :rtype: function that gets 2 parameters: image tensor and targets tensor
        """
        return self._transform

    @transform.setter
    def transform(self, value):
        """The post augmentation transform.

        :return: the transform function
        :rtype: function that gets 2 parameters: image tensor and targets tensor
        """
        self._transform = value

    def label_to_index_map(self, label):
        """Get mapping from class name to numeric
        class index.

        :param label: Class name
        :type label: str
        :return: Numeric class index
        :rtype: int
        """
        return self._class_to_index_map[label]

    def index_to_label(self, index):
        """Get the class name associated with numeric index

        :param index: Numeric class index
        :type index: int
        :return: Class name
        :rtype: str
        """
        return self._object_classes[index]

    def train_val_split(self, valid_portion=TrainingCommonSettings.DEFAULT_VALIDATION_SIZE):
        """Splits a dataset into two datasets, one for training and and for validation.

        :param valid_portion: (optional) Portion of dataset to use for validation.
        :type valid_portion: Float between 0.0 and 1.0
        :return: Training dataset and validation dataset
        :rtype: Tuple of (Trainining, Validation) datasets of the same type as current object
        """
        number_of_samples = len(self._image_elements)
        indices = np.arange(number_of_samples)
        if number_of_samples == 1:
            logger.warning("Only one data point provided, will use this for both training and validation.")
            training_indices = indices
            validation_indices = indices
        else:
            training_indices, validation_indices = train_test_split(indices, test_size=valid_portion)

        train_dataset = copy.deepcopy(self)
        train_dataset._indices = training_indices
        train_dataset._reset_dataset_elements()

        validation_dataset = copy.deepcopy(self)
        validation_dataset._indices = validation_indices
        validation_dataset._is_train = False
        validation_dataset._reset_dataset_elements()

        return train_dataset, validation_dataset

    def reset_classes(self, classes):
        """Update dataset wrapper with a list of new classes

        :param classes: classes
        :type classes: string list
        """
        self._object_classes = sorted(classes, reverse=False)
        self._class_to_index_map = {object_class: i for
                                    i, object_class in
                                    enumerate(self._object_classes)}

    def collate_function(self, batch):
        """Collate function for the dataset"""
        return tuple(zip(*batch))

    @staticmethod
    def _prepare_images_and_labels(image_elements, annotations, object_classes, use_bg_label, label_compute_func):
        object_classes = list(object_classes)
        if use_bg_label:
            object_classes = [PredefinedLiterals.BG_LABEL] + object_classes
        # "-" is smaller than capital letter
        object_classes = sorted(object_classes, reverse=False)  # make sure --bg-- is mapped to zero index
        # Use sorted to make sure all workers get the same order of data in distributed training/validation
        image_elements = sorted(image_elements)
        class_to_index_map = {object_class: i for
                              i, object_class in
                              enumerate(object_classes)}
        labels = None
        if label_compute_func is not None:
            labels = label_compute_func(image_elements, annotations, class_to_index_map)

        return object_classes, image_elements, class_to_index_map, labels

    def _get_real_index(self, index):
        if self._indices is not None:
            if index >= len(self._indices):
                raise IndexError
            return self._indices[index]
        else:
            if index >= len(self._image_elements):
                raise IndexError
        return index

    def prepare_image_data_for_eval(self, image_targets, image_info):
        """ Convert image data (part of output of __getitem__) to a format suitable for calculating
        eval metrics. The output should be a tuple of image_info and box_info. box_info should be a dictionary
        containing boxes in unnormalized xyxy format and labels as a 1d torch.tensor of dtype torch.long.

        :param image_targets: Targets for an image (part of output of __getitem__)
        :type image_targets: torch.tensor
        :param image_info: Image info (part of output of __getitem__)
        :type image_info: dict
        :return: Tuple of image_info and box_info (Dictionary containing boxes, labels and optionally masks)
        :rtype: Tuple[Dict, Dict]
        """
        return image_info, image_targets

    def get_image_element_at_index(self, index):
        """Get the image_element at an index.

        :param index: Index
        :type index: Int
        :return: Image element
        :rtype: TilingDatasetElement
        """
        index = self._get_real_index(index)
        return self._image_elements[index]

    def get_image_tiles(self, image_element):
        """Get tiles for an image.

        :param image_element: Image element
        :type image_element: TilingDatasetElement
        :return: List of image tiles
        :rtype: List[TilingDatasetElement]
        """
        return self._image_tiles[image_element]

    def _generate_tile_elements(self):
        """ Generate tiles and corresponding annotations.
        """
        if self._tile_grid_size is None or self._tile_overlap_ratio is None:
            return

        from azureml.acft.common_components.image.runtime_common.common.utils import _read_image_dimensions

        tiling_start = time.time()
        logger.info(f"Generating tiles for all images using grid size: {self._tile_grid_size} "
                    f"and overlap ratio: {self._tile_overlap_ratio}")

        for index in range(len(self)):
            image_element = self.get_image_element_at_index(index)
            image_annotations = self._annotations[image_element]
            image_tiles = []

            image_size = _read_image_dimensions(self._ignore_data_errors, image_element.image_url, self._use_cv2)
            if image_size is not None:
                tile_annotations = generate_tiles_annotations(image_annotations,
                                                              self._tile_grid_size, self._tile_overlap_ratio,
                                                              image_size)
                for tile, per_tile_annotations in tile_annotations.items():
                    if per_tile_annotations:  # not empty
                        image_tile = TilingDatasetElement(image_element.image_url, tile)
                        image_tiles.append(image_tile)
                        self._annotations[image_tile] = []
                        for item in per_tile_annotations:
                            oa = ObjectAnnotation()
                            oa.init(item)
                            self._annotations[image_tile].append(oa)

            if self._label_compute_func is not None and self._labels is not None:
                image_tile_labels = self._label_compute_func(image_tiles, self._annotations, self._class_to_index_map)
                self._labels.update(image_tile_labels)

            self._image_tiles[image_element] = image_tiles

        logger.info(f"Generated tiles in {time.time() - tiling_start} sec")

    def supports_tiling(self):
        """Check if the dataset supports tiling.

        :return: Supports tiling or not
        :rtype: bool
        """
        return self._tile_grid_size is not None

    def get_dataset_elements(self):
        """Get all dataset elements.

        :return: List of dataset elements
        :rtype: List[TilingDatasetElement]
        """
        return self._dataset_elements

    def _reset_dataset_elements(self):
        """Reset the list of dataset elements."""
        dataset_elements = []
        for index in range(len(self)):
            image_element = self.get_image_element_at_index(index)
            dataset_elements.append(image_element)
            image_tiles = self._image_tiles[image_element]
            dataset_elements.extend(image_tiles)
        self._dataset_elements = dataset_elements


class FileObjectDetectionDataset(CommonObjectDetectionDataset):
    """Wrapper for object detection dataset"""

    def __init__(self, annotations_file: Optional[str] = None, image_folder: str = ".", is_train: bool = False,
                 prob: float = 0.5, ignore_data_errors: bool = True, use_bg_label: bool = True,
                 label_compute_func: Any = None,
                 settings: Optional[Dict[str, Any]] = None, masks_required: bool = False,
                 tile_grid_size: Optional[Tuple[int, int]] = None,
                 tile_overlap_ratio: Optional[float] = None, use_cv2: bool = False) -> None:
        """
        :param annotations_file: Annotations file
        :type annotations_file: str
        :param image_folder: target image path
        :type image_folder: str
        :param is_train: which mode (training, inferencing) is the network in?
        :type is_train: bool
        :param prob: target probability of random horizontal flipping
        :type prob: float
        :param ignore_data_errors: flag to indicate if image data errors should be ignored
        :type ignore_data_errors: bool
        :param use_bg_label: flag to indicate if we use incluse the --bg-- label
        :type use_bg_label: bool
        :param label_compute_func: function to use when computing labels
        :type label_compute_func: func
        :param settings: additional settings to be used in the dataset
        :type settings: dict
        :param masks_required: If masks information is required
        :type masks_required: bool
        :param tile_grid_size: The grid size to split the image into, if tiling is enabled. None, otherwise
        :type tile_grid_size: Tuple[int, int]
        :param tile_overlap_ratio: Overlap ratio between adjacent tiles in each dimension.
                                   None, if tile_grid_size is None
        :type tile_overlap_ratio: float
        :param use_cv2: Use cv2 for reading image dimensions
        :type use_cv2: bool
        """
        super().__init__(is_train=is_train, prob=prob, ignore_data_errors=ignore_data_errors,
                         use_bg_label=use_bg_label, label_compute_func=label_compute_func,
                         settings=settings, masks_required=masks_required,
                         tile_grid_size=tile_grid_size, tile_overlap_ratio=tile_overlap_ratio, use_cv2=use_cv2)
        log_memory_usage(is_train, before_dataset_creation=True)

        if annotations_file is not None:
            annotations = self._read_annotations_file(annotations_file, ignore_data_errors=ignore_data_errors)

            self._init_dataset(annotations, image_folder,
                               ignore_data_errors=ignore_data_errors)
            log_memory_usage(is_train, before_dataset_creation=False)

    def _init_dataset(self, annotations, image_folder, ignore_data_errors):

        image_elements = set()
        object_classes = set()

        if not annotations:
            raise AutoMLVisionDataException("No annotations to initialize datasets.", has_pii=False)
        for annotation in annotations:
            if (DatasetFieldLabels.IMAGE_URL not in annotation or DatasetFieldLabels.IMAGE_LABEL not in annotation):
                missing_required_fields_message = "Missing required fields in annotation"
                if ignore_data_errors:
                    logger.warning(missing_required_fields_message)
                    continue
                else:
                    raise AutoMLVisionDataException(missing_required_fields_message, has_pii=False)

            try:
                object_info = ObjectAnnotation(_masks_required=self._masks_required)
                object_info.init(annotation[DatasetFieldLabels.IMAGE_LABEL])
            except AutoMLVisionDataException as ex:
                if ignore_data_errors:
                    logging_utilities.log_traceback(ex, logger)
                    continue
                else:
                    raise

            if not object_info.valid:
                logger.warning("Invalid annotation. Skipping it.")
                continue

            image_url = os.path.join(image_folder, annotation[DatasetFieldLabels.IMAGE_URL])

            if not _validate_image_exists(image_url, ignore_data_errors):
                continue

            image_element = TilingDatasetElement(image_url, None)
            image_elements.add(image_element)
            self._annotations[image_element].append(object_info)
            object_classes.add(annotation[DatasetFieldLabels.IMAGE_LABEL][DatasetFieldLabels.CLASS_LABEL])

        if not image_elements:
            raise AutoMLVisionDataException("All annotations provided are ill-formed.", has_pii=False)

        self._object_classes, self._image_elements, self._class_to_index_map, self._labels = \
            self._prepare_images_and_labels(image_elements, self._annotations, object_classes,
                                            self._use_bg_label, self._label_compute_func)
        self._generate_tile_elements()
        self._reset_dataset_elements()

    @staticmethod
    def _read_annotations_file(annotations_file, ignore_data_errors=True):
        annotations = []
        line_no = 0
        with open(annotations_file, "r") as json_file:
            for line in json_file:
                try:
                    try:
                        line_no += 1
                        annotations.append(json.loads(line))
                    except json.JSONDecodeError:
                        raise AutoMLVisionDataException(f"Json decoding error in line no: {line_no}",
                                                        has_pii=False)
                except AutoMLVisionDataException as ex:
                    if ignore_data_errors:
                        logging_utilities.log_traceback(ex, logger)
                    else:
                        raise

        return annotations


class AmlDatasetObjectDetection(CommonObjectDetectionDataset, AmlDatasetBaseWrapper):
    """Wrapper for Aml labeled dataset for object detection dataset"""

    def __init__(self, dataset, is_train=False, prob=0.5,
                 ignore_data_errors=False,
                 use_bg_label=True, label_compute_func=None, label_column_name=None,
                 settings=None, masks_required=False, tile_grid_size=None, tile_overlap_ratio=None, use_cv2=False):
        """
        :param dataset: dataset
        :type dataset: AbstractDataset
        :param is_train: which mode (training, inferencing) is the network in?
        :type is_train: bool
        :param prob: target probability of random horizontal flipping
        :type prob: float
        :param ignore_data_errors: Setting this ignores and files in the labeled dataset that fail to download.
        :type ignore_data_errors: bool
        :param use_bg_label: flag to indicate if we use incluse the --bg-- label
        :type use_bg_label: bool
        :param label_compute_func: function to use when computing labels
        :type label_compute_func: func
        :param label_column_name: Label column name
        :type label_column_name: str
        :param settings: additional settings to be used in the dataset
        :type settings: dict
        :param masks_required: If masks information is required
        :type masks_required: bool
        :param tile_grid_size: The grid size to split the image into, if tiling is enabled. None, otherwise
        :type tile_grid_size: Tuple[int, int]
        :param tile_overlap_ratio: Overlap ratio between adjacent tiles in each dimension.
                                   None, if tile_grid_size is None
        :type tile_overlap_ratio: float
        :param use_cv2: Use cv2 for reading image dimensions
        :type use_cv2: bool
        """
        super().__init__(is_train=is_train, prob=prob, ignore_data_errors=ignore_data_errors,
                         use_bg_label=use_bg_label, label_compute_func=label_compute_func,
                         settings=settings, masks_required=masks_required, tile_grid_size=tile_grid_size,
                         tile_overlap_ratio=tile_overlap_ratio, use_cv2=use_cv2)

        stream_image_files = False if settings is None else settings.get(SettingsLiterals.STREAM_IMAGE_FILES, False)

        log_memory_usage(is_train, before_dataset_creation=True)
        self._dataset_helper = AmlDatasetHelper(dataset, ignore_data_errors,
                                                image_column_name=self.DATASET_IMAGE_COLUMN_NAME,
                                                download_files=False)
        if label_column_name is None:
            self._label_column_name = self._dataset_helper.label_column_name
        else:
            self._label_column_name = label_column_name
        images_df = self._dataset_helper.images_df

        self._init_dataset(images_df, stream_image_files, ignore_data_errors=ignore_data_errors)
        log_memory_usage(is_train, before_dataset_creation=False)

    def _init_dataset(self, images_df, stream_image_files, ignore_data_errors=True):

        image_elements = set()
        object_classes = set()
        num_background_images = 0

        if self._label_column_name not in images_df:
            raise AutoMLVisionDataException("No labels found to initialize dataset.",
                                            has_pii=False)

        for index, label in enumerate(images_df[self._label_column_name]):
            if index % 10000 == 0:
                logger.info(f"Processing Image # {index}")
                system_meter.log_system_stats()

            image_url = self._dataset_helper.get_image_full_path(index)

            # Validate that image files exist.
            # (Only validate this if all files have been downloaded to disk. Ohterwise, existence checks
            # are too slow / can take hours.)
            if not stream_image_files and not _validate_image_exists(image_url, ignore_data_errors):
                continue

            cur_img_object_infos = []
            cur_object_classes = set()

            try:
                if not isinstance(label, list):
                    msg = "The provided annotations are not in valid format." \
                        "Please check the annotations format for each specific image task here. " \
                        "https://docs.microsoft.com/en-us/azure/machine-learning/reference-automl-images-schema"
                    raise AutoMLVisionDataException(msg, has_pii=False)

                for annotation in label:
                    object_info = ObjectAnnotation(_masks_required=self._masks_required)
                    object_info.init(annotation)
                    if object_info.valid:
                        cur_img_object_infos.append(object_info)
                        cur_object_classes.add(annotation[DatasetFieldLabels.CLASS_LABEL])
            except AutoMLVisionDataException as ex:
                if ignore_data_errors:
                    logging_utilities.log_traceback(ex, logger)
                    continue
                else:
                    raise

            # If there is at least one object annotation but all of them are invalid, skip the image. Note that
            # images without any object annotations are kept.
            if (len(label) > 0) and (len(cur_img_object_infos) == 0):
                logger.warning("No valid annotations. Skipping image.")
                continue

            # Increment counter for background images if the current image does not have any object annotations.
            num_background_images += len(cur_img_object_infos) == 0

            image_element = TilingDatasetElement(image_url, None)
            image_elements.add(image_element)
            self._annotations[image_element].extend(cur_img_object_infos)
            object_classes.update(cur_object_classes)

        if not image_elements:
            raise AutoMLVisionDataException("All annotations provided are ill-formed.", has_pii=False)

        # Check that at least an image in the dataset has at least an object.
        if num_background_images == len(image_elements):
            raise AutoMLVisionDataException(
                "No objects in dataset. Please ensure that at least one image has one or more objects.", has_pii=False
            )

        # Log number of background images.
        logger.info(f"{num_background_images} background images.")

        self._object_classes, self._image_elements, self._class_to_index_map, self._labels = \
            self._prepare_images_and_labels(image_elements, self._annotations, object_classes,
                                            self._use_bg_label, self._label_compute_func)
        self._generate_tile_elements()
        self._reset_dataset_elements()

    def get_images_df(self):
        """Return images dataframe"""
        return self._dataset_helper.images_df

    def delete_images_df(self):
        """Delete the images dataframe"""
        del self._dataset_helper.images_df
