import os
from typing import List, Tuple

import numpy as np
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator


class SegmentAnythingModel:
    def __init__(
            self,
            points_per_side=32,
            pred_iou_thresh=0.86,
            stability_score_thresh=0.92,
            crop_n_layers=3,
            crop_n_points_downscale_factor=2,
            min_mask_region_area=200,
            device='cpu'
        ):
        """Performs setup of the SAM model using default parameters
        
        Parameters
        ----------
        points_per_side : (int or None) - The number of points to be sampled
            along one side of the image. The total number of points is
            points_per_side**2. If None, 'point_grids' must provide explicit
            point sampling.
            
        pred_iou_thresh : (float) - A filtering threshold in [0,1], using the
            model's predicted mask quality.
            
        stability_score_thresh : (float) - A filtering threshold in [0,1], using
            the stability of the mask under changes to the cutoff used to binarize
            the model's mask predictions.
            
        crops_n_layers : (int) - If >0, mask prediction will be run again on
            crops of the image. Sets the number of layers to run, where each
            layer has 2**i_layer number of image crops.
            
        crop_n_points_downscale_factor : (int) - The number of points-per-side
            sampled in layer n is scaled down by crop_n_points_downscale_factor**n.
            
        min_mask_region_area : (int) - If >0, postprocessing will be applied
            to remove disconnected regions and holes in masks with area smaller
            than min_mask_region_area. Requires opencv.
        """
        curdir = os.path.dirname(os.path.abspath(__file__))
        sam_checkpoint = f"{curdir}/weights/sam_vit_h_4b8939.pth"
        model_type = "vit_h"

        self.sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
        self.sam.to(device=device)
        self.mask_generator = SamAutomaticMaskGenerator(
            model=self.sam,
            points_per_side=points_per_side,
            pred_iou_thresh=pred_iou_thresh,
            stability_score_thresh=stability_score_thresh,
            crop_n_layers=crop_n_layers,
            crop_n_points_downscale_factor=crop_n_points_downscale_factor,
            min_mask_region_area=min_mask_region_area,
        )

    def generate_mask(self, rgb: np.ndarray, min=0.01, max=0.90) -> List[dict]:
        """Generates masks for given 3-channel image
        This method generates masks using segment_anything model.
        The masks go throught filtering using the followng rule:
        `min` < area(mask) < `max`

        TODO: interception detection and filtration

        Parameters
        ----------
        rgb : any image with three channels (even PCA's result may be used)

        min : float number used for area filtering. Masks with area lower
              than `min` will be discarded

        max : float number used in the same way as `min`

        Returns
        -------
        masks : list of filtered segment-anything's outputs
        """
        masks = self.mask_generator.generate(rgb)

        # Performs filtration by area
        to_delete = []
        for i, layer in enumerate(masks):
            s = np.sum(layer["segmentation"] > 0)
            percent = s / np.prod(rgb.shape[:2])
            if min < percent < max:
                continue

            to_delete.append(i)
        masks = [item for i, item in enumerate(masks) if i not in to_delete]
        return masks

    def generate_dataset_for_mindi(
        self, hsi: np.ndarray, rgb: np.ndarray, min=0.01, max=0.90
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Creates a dataset which may be used to generate MINDI indices

        Parameters
        ----------
        hsi : initial hyperspectral data

        rgb : any image with three channels (even PCA's result may be used)

        min : float number used for area filtering. Masks with area lower
              than `min` will be discarded

        max : float number used in the same way as `min`

        Returns
        -------
        data : list of numpy arrays contains the exact hyperspectral 
               values of corresponding masks (n_samples, n_features)

        masks : list of numpy arrays represents binary masks 
        """
        masks = self.generate_mask(rgb, min, max)

        data2save = []
        mask2save = []
        for i, mask in enumerate(
            map(
                lambda item: item["segmentation"],
                sorted(masks, key=lambda x: x["area"], reverse=True),
            )
        ):
            mask2save.append(mask)
            data2save.append(hsi[mask == True, ::])

        return data2save, mask2save
