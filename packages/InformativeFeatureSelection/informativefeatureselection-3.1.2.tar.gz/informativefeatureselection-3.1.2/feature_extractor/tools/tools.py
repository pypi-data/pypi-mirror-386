from typing import List, Tuple

import numpy as np

from feature_extractor.common.models import MindiResult


def find_indi_thresholds_by_percentile(
    hsi: np.ndarray, mask: List[np.ndarray], indices: List[MindiResult], p1=20, p2=80
) -> List[Tuple[float, float]]:
    """
    Searches for thresholds to clip values using percentile analysis of the initial values distribution.

    Parameters
    ----------
    hsi : np.ndarray
        A numpy array containing the initial values distribution.
        It should be a three-dimensional array of shape `(height, width, num_bands)`.
    mask : List[np.ndarray]
        A list of boolean numpy arrays used as masks.
        It should have the same length as `indices`,
        and each element is a two-dimensional numpy array of shape `(height, width)`.
    indices : List[MindiResult]
        A list of `MindiResult` objects.
        It should be a list of `MindiResult` objects representing each class in the dataset.
    p1 : int, optional
        The percentile at which to set the lower threshold, by default 20.
    p2 : int, optional
        The percentile at which to set the upper threshold, by default 80.

    Returns
    -------
    List[Tuple[float, float]]
        A list of tuples containing the lower and upper thresholds
        for each `MindiResult` object in `indices`.
    """
    ndis = [None] * len(indices)
    thresholds = [None] * len(indices)
    for index in indices:
        key = index.class_idx
        (p1, p2) = index.indices
        l1 = hsi[..., p1]
        l2 = hsi[..., p2]
        ndis[key] = np.divide(
            l1 - l2, l1 + l2, out=np.zeros_like(l1), where=l2 != 0, dtype=np.float32
        )

        target_values = ndis[key][mask[key] == True]
        a, b = np.percentile(target_values, p1), np.percentile(target_values, p2)
        thresholds[key] = (a, b)

    return thresholds
