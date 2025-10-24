from copy import copy
from typing import List, Tuple, Dict
from feature_extractor.common.models import MindiResult
from feature_extractor.tools.utils import wrap_verbose_loop

import numpy as np

from feature_extractor.common import DiscriminantAnalysis
from feature_extractor.indi.INDI import INDI


class MulticlassINDI(INDI):
    """
    INDI implementation for the multiclass case
    This implementation also considers faraway class searching optimization in order to improve accuracy
    """

    def __init__(self, lda=DiscriminantAnalysis(), verbose=False):
        super().__init__()
        self.LDA = lda
        self.ignored_classes = []
        self.classes = []
        self.verbose = verbose

    def process(
        self, data: List[np.ndarray], labels: List[int], **kwargs
    ) -> Dict[int, Tuple[int, int]]:
        """
        Be careful, this implementation returns dictionary instead of list of layer's indices (like INDI class do)
        :return: dictionary like {'class_label': [layer_index, layer_index]}
        """
        self.ignored_classes = []
        self.classes = np.arange(len(labels))
        n_classes = len(labels)

        result = []

        for _ in wrap_verbose_loop(
            range(n_classes - 1), name="Loop over classes", verbose=self.verbose, leave=False
        ):
            faraway_class_idx, class_criteria = self.find_faraway_class(data)
            divided_data = self.divide_data(data, faraway_class_idx)
            # Just use the method from the binary INDI implementation since now we consider One-Vs-Rest case
            indices, ndi_criteria = super().process(divided_data)
            result.append(
                MindiResult(
                    class_idx=labels[faraway_class_idx],
                    indices=indices,
                    ndi_criteria=ndi_criteria,
                    class_criteria=class_criteria,
                )
            )
            self.ignored_classes.append(faraway_class_idx)

        result.append(MindiResult(
            class_idx=labels[self.get_classes_exclude_ignored()[0]],
            indices=indices,
            ndi_criteria=ndi_criteria,
            class_criteria=class_criteria,
        ))

        return result

    def find_faraway_class(self, initial_data: List[np.ndarray]) -> int:
        """
        Finds faraway class in the given data using individual criteria of discriminant analysis
        :return: faraway class label
        """
        classes = self.get_classes_exclude_ignored()
        criteria_val, informative_feature_val, faraway_class = 0, 0, classes[-1]

        for _class in wrap_verbose_loop(
            classes, name="Searching for faraway class", verbose=self.verbose,
            position=1, leave=False
        ):
            data = self.divide_data(initial_data, _class)

            Sb, Sw = self.LDA.calculate_matrices(data)
            individ_criteria = self.LDA.calculate_group_criteria(Sb, Sw)
            tmp_criteria_val = np.max(individ_criteria)

            if tmp_criteria_val > criteria_val:
                criteria_val = tmp_criteria_val
                faraway_class = _class

        return faraway_class, criteria_val

    def divide_data(self, data: List[np.ndarray], target: int):
        """
        Separates data in order to solve One-Vs-Rest task

        :param data: initial data
        :param target: class label which will be separated
        :return: list with two numpy arrays, the first one is "One", the second one is "Rest"
        """
        classes = self.get_classes_exclude_ignored()
        other_classes = copy(classes)
        other_classes.remove(target)
        data = [data[target], np.vstack([data[i] for i in other_classes])]
        return data

    def get_classes_exclude_ignored(self):
        return list(set(self.classes) - set(self.ignored_classes))
