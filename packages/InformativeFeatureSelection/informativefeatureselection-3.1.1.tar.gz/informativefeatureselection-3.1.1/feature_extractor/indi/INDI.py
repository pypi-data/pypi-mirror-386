from typing import List, Tuple, Optional

import numpy as np
from numba import njit

from feature_extractor.common import DiscriminantAnalysis
from feature_extractor.tools import wrap_verbose_loop
from feature_extractor.indi.IndiBase import BaseINDI


@njit(fastmath=True)
def ndi(l1: np.ndarray, l2: np.ndarray) -> np.ndarray:
    a = np.subtract(l1, l2)
    b = np.add(l1, l2) + 1e-4
    c = np.divide(a, b)
    return c


class INDI(BaseINDI):
    """
    INDI implementation for the binary case
    """

    def __init__(self, lda=DiscriminantAnalysis(), verbose=False) -> None:
        super().__init__()
        self.lda = lda
        self.verbose = verbose

    def process(
        self, data: List[np.ndarray], labels: Optional[List[int]] = None
    ) -> Tuple[int, int]:
        n_classes = len(data)
        assert n_classes == 2, "This is implementation of binary INDI"
        n_features = data[0].shape[1]
        max_lambda = np.NINF
        best_layers = (1, 2)

        data_t = [x.T.copy() for x in data]
        indices = np.triu_indices(n_features, k=1)

        for i, j in wrap_verbose_loop(
            zip(*indices), "Searching for best INDI pair", self.verbose
        ):
            ndi_cl1 = ndi(data_t[0][i], data_t[0][j])
            ndi_cl2 = ndi(data_t[1][i], data_t[1][j])

            _, _, _lambda = self.lda.calculate_matrices(
                [ndi_cl1.reshape(-1, 1), ndi_cl2.reshape(-1, 1)]
            )
            # _lambda = b / (b + w)

            if _lambda > max_lambda:
                best_layers = (i, j)
                max_lambda = _lambda

        return best_layers, max_lambda
