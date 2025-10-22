import json
import logging
import os
import shutil
from typing import Any

from picsellia import DatasetVersion, Label
from picsellia.exceptions import NoDataError
from picsellia.sdk.asset import MultiAsset
from picsellia.types.enums import AnnotationFileType
from tqdm import tqdm

from picsellia_cv_engine.core.data.dataset.utils import remove_empty_directories

from .base_dataset import BaseDataset

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


class CocoDataset(BaseDataset):
    """
    A specialized dataset for managing COCO annotations, enabling downloading, batching,
    and merging of annotation files.

    This class provides methods for downloading annotations in batches, merging them into a single
    COCO file, and loading the data for further processing.
    """

    def __init__(
        self,
        name: str,
        dataset_version: DatasetVersion,
        assets: MultiAsset | None = None,
        labelmap: dict[str, Label] | None = None,
    ):
        """
        Initialize the COCO dataset.

        Args:
            name (str): The name of the dataset.
            dataset_version (DatasetVersion): The version of the dataset to work with.
            assets (Optional[MultiAsset]): Preloaded assets, if available.
            labelmap (Optional[Dict[str, Label]]): Mapping of labels for the dataset.
        """
        super().__init__(
            name=name,
            dataset_version=dataset_version,
            assets=assets,
            labelmap=labelmap,
        )
        self.coco_file_path: str | None = None
        """The path to the merged COCO annotation file."""

        self.coco_data: dict[str, Any] | None = None
        """The loaded COCO annotation data."""

    def download_annotations(
        self, destination_dir: str, use_id: bool | None = True
    ) -> None:
        """
        Download COCO annotations in batches, optionally merging them into a single file.

        Args:
            destination_dir (str): Directory to save the COCO annotation files.
            use_id (Optional[bool]): Whether to use asset IDs in file paths (default: True).
        """
        self.annotations_dir = destination_dir
        os.makedirs(self.annotations_dir, exist_ok=True)
        assets_to_download = self._determine_assets_source()

        with tqdm(desc="Downloading COCO annotation batches", unit="assets") as pbar:
            batch_files = self._process_batches(
                destination_dir=self.annotations_dir,
                assets_to_download=assets_to_download,
                pbar=pbar,
                use_id=use_id,
            )

        if not batch_files:
            logger.warning("No batches were successfully downloaded.")
            return None

        self.coco_file_path = os.path.join(
            self.annotations_dir, "coco_annotations.json"
        )
        if len(batch_files) == 1:
            moved_file_path = shutil.move(src=batch_files[0], dst=self.annotations_dir)
            os.rename(src=moved_file_path, dst=self.coco_file_path)
            logger.info(f"Single batch file saved to {self.coco_file_path}")
        else:
            self._merge_batches(
                batch_files=batch_files, final_coco_file_path=self.coco_file_path
            )
            logger.info(f"Merged COCO annotations saved to {self.coco_file_path}")

        remove_empty_directories(directory=self.annotations_dir)

        self.coco_data = self.load_coco_file_data()
        logger.info("COCO annotations downloaded and loaded into memory.")

    def _determine_assets_source(self) -> MultiAsset | None:
        """
        Determine the source of assets for downloading annotations.

        Returns:
            Optional[MultiAsset]: Preloaded assets if available, otherwise None for dynamic fetching.
        """
        if self.assets:
            logger.info("Using preloaded assets for batch download.")
            return self.assets
        else:
            logger.info(
                "Preloaded assets not available. Fetching assets incrementally."
            )
            return None

    def _process_batches(
        self,
        destination_dir: str,
        assets_to_download: MultiAsset | None,
        pbar: tqdm,
        use_id: bool | None = True,
    ) -> list[str]:
        """
        Process assets in batches and export their COCO annotations.

        Args:
            destination_dir (str): Directory to save batch files.
            assets_to_download (Optional[MultiAsset]): Preloaded assets or None for dynamic fetching.
            pbar (tqdm): Progress bar to display batch processing progress.
            use_id (Optional[bool]): Whether to use asset IDs in file paths (default: True).

        Returns:
            List[str]: List of file paths to the exported batch files.
        """
        batch_files = []
        offset = 0
        batch_index = 0

        while True:
            try:
                batch_assets = self._get_next_batch(
                    assets_to_download=assets_to_download, offset=offset
                )
                if not batch_assets:
                    logger.info("All assets have been processed.")
                    break

                batch_file_path = os.path.join(
                    destination_dir, f"coco_batch_{batch_index}.json"
                )
                coco_annotation_path = self._export_batch(
                    batch_assets=batch_assets,
                    destination_path=batch_file_path,
                    use_id=use_id,
                )
                batch_files.append(coco_annotation_path)

                pbar.update(len(batch_assets))
                offset += len(batch_assets)
                batch_index += 1
            except NoDataError:
                logger.info("No more assets available to process. Exiting.")
                break
            except Exception as e:
                logger.error(
                    f"An error occurred during batch {batch_index} processing: {e}"
                )
                break

        return batch_files

    def _get_next_batch(
        self, assets_to_download: MultiAsset | None, offset: int
    ) -> MultiAsset:
        """
        Retrieve the next batch of assets.

        Args:
            assets_to_download (Optional[MultiAsset]): Preloaded assets or None for dynamic fetching.
            offset (int): Current offset for fetching the batch.

        Returns:
            MultiAsset: The next batch of assets.
        """
        if assets_to_download:
            return assets_to_download[offset : offset + BATCH_SIZE]
        else:
            return self.get_assets_batch(limit=BATCH_SIZE, offset=offset)

    def _export_batch(
        self,
        batch_assets: MultiAsset,
        destination_path: str,
        use_id: bool | None = True,
    ) -> str:
        """
        Export COCO annotations for a batch of assets.

        Args:
            batch_assets (MultiAsset): The batch of assets to export.
            destination_path (str): File path to save the exported JSON file.
            use_id (Optional[bool]): Whether to use asset IDs in file paths (default: True).

        Returns:
            str: Path to the exported annotation file.
        """
        return self.dataset_version.export_annotation_file(
            annotation_file_type=AnnotationFileType.COCO,
            target_path=destination_path,
            use_id=use_id,
            assets=batch_assets,
        )

    def _merge_batches(self, batch_files: list[str], final_coco_file_path: str) -> None:
        """
        Merge multiple COCO annotation batches into a single file.

        Args:
            batch_files (List[str]): Paths to the batch files.
            final_coco_file_path (str): Path to save the merged COCO file.
        """
        merged_coco_data: dict[str, list] = {
            "images": [],
            "annotations": [],
            "categories": [],
        }
        max_image_id = 0
        max_annotation_id = 0

        with tqdm(batch_files, desc="Merging annotation batches", unit="batch") as pbar:
            for batch_file in pbar:
                with open(batch_file) as f:
                    batch_data = json.load(f)

                for image in batch_data.get("images", []):
                    image["id"] += max_image_id
                    merged_coco_data["images"].append(image)

                for annotation in batch_data.get("annotations", []):
                    annotation["id"] += max_annotation_id
                    annotation["image_id"] += max_image_id
                    merged_coco_data["annotations"].append(annotation)

                if merged_coco_data["images"]:
                    max_image_id = (
                        max(img["id"] for img in merged_coco_data["images"]) + 1
                    )
                else:
                    max_image_id = 0

                if merged_coco_data["annotations"]:
                    max_annotation_id = (
                        max(ann["id"] for ann in merged_coco_data["annotations"]) + 1
                    )
                else:
                    max_annotation_id = 0

                if not merged_coco_data["categories"]:
                    merged_coco_data["categories"] = batch_data.get("categories", [])

                os.remove(batch_file)

        with open(final_coco_file_path, "w") as f:
            json.dump(merged_coco_data, f, indent=4)
        logger.info(f"Merged annotations saved to {final_coco_file_path}")

    def load_coco_file_data(self) -> dict[str, Any]:
        """
        Load COCO annotation data from the merged annotation file.

        Returns:
            Dict[str, Any]: The COCO data loaded as a dictionary.

        Raises:
            FileNotFoundError: If the COCO file path is not set.
            Exception: If an error occurs while reading the file.
        """
        if self.coco_file_path is None:
            raise FileNotFoundError(
                "COCO file path is not set. Please download the COCO file first."
            )
        try:
            with open(self.coco_file_path) as f:
                coco_data = json.load(f)
            logger.info(f"Successfully loaded COCO data from {self.coco_file_path}")
            return coco_data
        except Exception as e:
            logger.error(f"Error loading COCO data from {self.coco_file_path}: {e}")
            raise
