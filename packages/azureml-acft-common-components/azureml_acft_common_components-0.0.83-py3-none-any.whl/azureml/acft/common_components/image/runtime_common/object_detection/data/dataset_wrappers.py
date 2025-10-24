# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Classes and functions to ingest data for object detection."""
from typing import Dict, List

from abc import ABC, abstractmethod
from enum import Enum
from torch.utils.data import Dataset

from azureml.acft.common_components.image.runtime_common.common.exceptions import AutoMLVisionSystemException
from azureml.acft.common_components.image.runtime_common.object_detection.data.datasets import \
    CommonObjectDetectionDataset
from typing import TypeVar

T_co = TypeVar('T_co', covariant=True)


class ObjectDetectionDatasetBaseWrapper(ABC, Dataset[T_co]):
    """Class the establishes interface for object detection datasets"""

    @abstractmethod
    def __getitem__(self, index: int):
        """Get item by index

        :param index: Index of object
        :type index: int
        :return: Item at Index
        :rtype: Object Detection Record
        """
        pass

    @abstractmethod
    def __len__(self):
        """Get the number of items in dataset

        :return: Number of items in dataset
        :rtype: int
        """
        pass


class DatasetProcessingType(Enum):
    """Type indicating how to process dataset."""
    IMAGES = 0
    IMAGES_AND_TILES = 1


class CommonObjectDetectionDatasetWrapper(ObjectDetectionDatasetBaseWrapper):
    """Wrapper for object detection dataset"""

    def __init__(self, dataset: CommonObjectDetectionDataset, dataset_processing_type: DatasetProcessingType) -> None:
        """
        :param dataset: Object detection dataset
        :type dataset: CommonObjectDetectionDataset
        :param dataset_processing_type: Dataset processing type
        :type dataset_processing_type: DatasetProcessingType
        """
        self._dataset = dataset
        self._dataset_processing_type = dataset_processing_type

        if self._dataset_processing_type == DatasetProcessingType.IMAGES_AND_TILES and \
                not self._dataset.supports_tiling():
            raise AutoMLVisionSystemException("Dataset doesn't support tiling. Cannot use tiles", has_pii=False)

        self._dataset_elements = []
        self._image_url_to_indices_mapping: Dict[str, List[int]] = {}

        dataset_elements = set()
        for index in range(len(self._dataset)):
            image_element = self._dataset.get_image_element_at_index(index)
            dataset_elements.add(image_element)

            if self._dataset_processing_type == DatasetProcessingType.IMAGES_AND_TILES:
                image_tiles = self._dataset.get_image_tiles(image_element)
                dataset_elements.update(image_tiles)

        self._dataset_elements = sorted(dataset_elements)

        # Image Url to dataset element indices mapping
        for index, dataset_element in enumerate(self._dataset_elements):
            if dataset_element.image_url not in self._image_url_to_indices_mapping:
                self._image_url_to_indices_mapping[dataset_element.image_url] = []
            self._image_url_to_indices_mapping[dataset_element.image_url].append(index)

    def __len__(self) -> int:
        """Get the number of items in dataset

        :return: Number of items in dataset
        :rtype: int
        """
        return len(self._dataset_elements)

    def __getitem__(self, index: int):
        """Get item by index

        :param index: Index of object
        :type index: int
        :return: Item at Index
        :rtype: Object Detection Record
        """
        dataset_element = self._dataset_elements[index]
        return self._dataset.get_image_label_info(dataset_element)

    @property
    def dataset(self) -> CommonObjectDetectionDataset:
        """Get dataset.

        :return: Dataset
        :rtype: CommonObjectDetectionDataset
        """
        return self._dataset

    @property
    def dataset_processing_type(self) -> DatasetProcessingType:
        """Get dataset processing type.

        :return: Dataset processing type.
        :rtype: DatasetProcessingType
        """
        return self._dataset_processing_type

    def get_indices_for_image(self, image_url: str) -> List[int]:
        """Get the indices in dataset_elements corresponding to an image.

        :param image_url: Image url.
        :type image_url: str
        :return: List of indices
        :rtype: List[int]
        """
        return self._image_url_to_indices_mapping[image_url]
