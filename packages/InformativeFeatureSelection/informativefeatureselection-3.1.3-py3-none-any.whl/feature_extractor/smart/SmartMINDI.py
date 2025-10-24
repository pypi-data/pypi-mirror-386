from itertools import combinations
from typing import List, Tuple

import numpy as np
from feature_extractor.common import (
    BaseDiscriminantAnalysis,
    DiscriminantAnalysis,
    DiscriminantAnalysisV2,
    MindiResult
)
from feature_extractor.indi import MulticlassINDI, BaseINDI


class SmartMINDI:
    def __init__(self, mindi: BaseINDI, lda: BaseDiscriminantAnalysis):
        self.mindi = mindi
        self.lda = lda

    @staticmethod
    def default():
        """SmartMINDI factory with default parameters

        Returns
        -------
        SmartMINDI
            the SmartMINDI itself
        """
        lda = DiscriminantAnalysisV2()
        return SmartMINDI(mindi=MulticlassINDI(lda=lda), lda=lda)

    def process(
        self, data: List[np.ndarray], masks: List[np.ndarray]
    ) -> Tuple[List[MindiResult], List[np.ndarray]]:
        """Performs MINDI
        1. Checks whether data is normalized
        2. For given masks and data performs merging of sibling masks
           by the means of Discriminant Analysis
        3. Performs searching INDI for each class

        Parameters
        ----------
        data : List[np.ndarray]
            list of (n_samples, n_features) for each class
        masks : List[np.ndarray]
            list of binary masks with the shape of the initial hyperpsectral image

        Returns
        -------
        Tuple[List[MindiResult], List[np.ndarray]]
            `MindiResult` list and corresponding masks
        """
        data = self.data_to_norm(data)

        r_data, r_label = self.perform_merge_sublings(data, masks)
        last_data, last_mask = r_data[-1], r_label[-1]

        found_mindi = self.mindi.process(last_data, np.arange(len(last_data)))
        return found_mindi, last_mask

    def data_to_norm(data: List[np.ndarray]):
        """Checks wether the data is normalized or not
        The check is naive, just take a look on the max value
        it should be lesser than one, otherwise data is not normalized

        Parameters
        ----------
        data : List[np.ndarray]
            initial data comprised of features values for each class
        """
        if np.max(data[0]) > 1.0:
            for i, entry in enumerate(data):
                data[i] = entry.astype(np.float64) / 255
        return data

    def perform_merge_sublings(
        self, initial_data, initial_mask, threshold="auto", iters=5
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Performs merging of sibling masks by means of the Discriminant analysis using group criteria

        Parameters
        ----------
        initial_data : List[np.ndarray]
            list of (n_samples, n_features) for each class
        initial_mask : List[np.ndarray]
            list of binary masks with the shape of the initial hyperpsectral image
        threshold : str, optional
            threshold value for cutting of classes need to be merged
            default value 'auto' manages the threshold automatically
            by merging 30th percentile of classes, by default 'auto'
        iters : int, optional
            number of iterations to merge masks, by default 5

        Returns
        -------
        Tuple[List[np.ndarray], List[np.ndarray]]
            returns lists of data and masks for each iteration
        """
        labels = np.arange(len(initial_data))
        pairs = list(combinations(labels, 2))

        data = initial_data
        mask = initial_mask

        result_data = []
        result_mask = []

        for _ in range(iters):
            data, mask, _ = self.merge_siblings(data, mask, pairs, threshold)
            # data, mask, _ = merge_siblings(data, mask, pairs, 0.3)
            labels = np.arange(len(data))
            pairs = list(combinations(labels, 2))

            result_data.append(data)
            result_mask.append(mask)

        return result_data, result_mask

    def calc_ind_criteria_for_pairs(
        self, data: List[np.ndarray], pairs: List[Tuple[int, int]]
    ) -> np.array:
        """Calculates group criteria for given data array and pairs 
        using Discriminant analysis.

        Parameters
        ----------
        data : List[np.ndarray]
            Input data
        pairs : List[Tuple[int, int]]
            List of tuples of layer indices (l1, l2) to consider when merging sibling masks.

        Returns
        -------
        np.array
            list of criteria values
        """
        criterias = []
        LDA = DiscriminantAnalysisV2()
        for l1, l2 in pairs:
            _data = (data[l1], data[l2])
            Sb, Sw = LDA.calculate_matrices(_data)
            try:
                individ_criteria = LDA.calculate_group_criteria(Sb, Sw)
            except:
                continue
            criterias.append(np.max(individ_criteria))
        return np.array(criterias)

    def merge_siblings(
        self,
        data: List[np.ndarray],
        masks: List[np.ndarray],
        pairs: Tuple[int, int],
        threshold=0.8,
    ) -> Tuple[List[np.ndarray], List[np.ndarray], List[Tuple[int, int]]]:
        """The logic of merging siblings itself

        Parameters
        ----------
        data : List[np.ndarray]
            Input data
        masks : List[np.ndarray]
            Input masks
        pairs : Tuple[int, int]
            Input pairs to consider
        threshold : float, optional
            Threshold for criteria value, may be 'auto' 
            to be determined automatically, by default 0.8

        Returns
        -------
        Tuple[List[np.ndarray], List[np.ndarray], List[Tuple[int, int]]]
            New data, new masks and list of pairs of class indexes were merged
        """

        criterias = self.calc_ind_criteria_for_pairs(data, pairs)

        sorted_criterias_indices = np.argsort(criterias)
        sorted_criterias = criterias[sorted_criterias_indices]
        if threshold == "auto":
            threshold = np.percentile(criterias, 0.5)
        split_index = np.searchsorted(sorted_criterias, threshold)

        to_merge = []
        unused_indices = set(np.arange(len(data)))
        used_indices = set()

        for pair_index in sorted_criterias_indices[:split_index]:
            p1, p2 = pairs[pair_index]
            if p1 in used_indices or p2 in used_indices:
                continue
            else:
                to_merge.append((p1, p2))
                used_indices.add(p1)
                used_indices.add(p2)
        unused_indices = unused_indices - used_indices

        new_data = []
        new_masks = []
        for p1, p2 in to_merge:
            new_data.append(np.vstack((data[p1], data[p2])))
            mask = np.zeros(masks.shape[1:])
            mask[masks[p1] == True] = True
            mask[masks[p2] == True] = True
            new_masks.append(mask)
        for unused_idx in unused_indices:
            new_data.append(data[unused_idx])
            new_masks.append(masks[unused_idx])

        return new_data, np.array(new_masks), to_merge
