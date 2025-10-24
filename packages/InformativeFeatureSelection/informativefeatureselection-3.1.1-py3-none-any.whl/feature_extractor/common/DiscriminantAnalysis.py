from abc import ABC, abstractmethod
from typing import Tuple, Union, List, Any

import numpy as np
from scipy import linalg
from sklearn.covariance import empirical_covariance


def _cov(X):
    """Estimate covariance matrix (using optional covariance_estimator).
    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Input data.

    Returns
    -------
    s : ndarray of shape (n_features, n_features)
        Estimated covariance matrix.
    """
    return empirical_covariance(X)


def _class_cov(X, y, priors):
    """Compute weighted within-class covariance matrix.

    The per-class covariance are weighted by the class priors.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Input data.

    y : array-like of shape (n_samples,) or (n_samples, n_targets)
        Target values.

    priors : array-like of shape (n_classes,)
        Class priors.

    Returns
    -------
    cov : array-like of shape (n_features, n_features)
        Weighted within-class covariance matrix
    """
    classes = np.unique(y)
    cov = np.zeros(shape=(X.shape[1], X.shape[1]))
    for idx, group in enumerate(classes):
        Xg = X[y == group, :]
        cov += priors[idx] * np.atleast_2d(_cov(Xg))
    return cov


def single_feature_statistic(data: Union[np.ndarray, List[np.ndarray]]) -> Tuple[np.ndarray, np.ndarray, Any]:
    """
    Method optimized for calculation individual criteria for single feature.
    Work twice faster that "numba_calculate_matrices"
    :return: scatter_between value, scatter_within value and individual criteria value
    """
    n_classes = len(data)
    separated_into_classes = data
    aig = np.array([np.mean(obj) for obj in separated_into_classes])

    n_k = np.array([class_samples.shape[0] for class_samples in separated_into_classes])
    n = np.sum(n_k)

    wa = np.sum(aig * n_k / n)

    b = np.sum(n_k * (aig - wa) ** 2)
    w = np.sum(np.array([np.sum((separated_into_classes[i] - aig[i]) ** 2) for i in range(0, n_classes)]))

    _lambda = b / (w + b)
    return b, w, _lambda


class BaseDiscriminantAnalysis(ABC):
    def calculate_group_criteria(self, Sb: np.ndarray, Sw: np.ndarray) -> float:
        evals, _ = linalg.eigh(Sb, Sw)
        return np.sum(evals)
    
    def calculate_individual_criteria(self, Sb: np.ndarray, Sw: np.ndarray) -> np.array:
        return np.diag(Sb) / (np.diag(Sw) + np.diag(Sb))

    @abstractmethod
    def calculate_matrices(self, data: Union[np.ndarray, List[np.ndarray]], data_t=None) \
            -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, Any]]:
        pass


class DiscriminantAnalysis(BaseDiscriminantAnalysis):
    """
    The first version of DA
    """

    def calculate_matrices(self, data: Union[np.ndarray, List[np.ndarray]], data_t=None) \
            -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, Any]]:
        """
        Calculates scatter between and scatter within matrices
        :see Linear discriminant analysis

        :note if data with single feature is provided also returns individual criteria value. It also may be usefully
        with extremely large data

        :param data: numpy array of shape (n_classes, n_samples, n_features) or list of numpy arrays (n_classes, ?,
        n_features)
        :return: tuple of two numpy arrays which represents scatter between and scatter within matrices
        """
        if data[0].shape[1] == 1:
            return single_feature_statistic(data)
        
        if data_t is None:
            data_t = [x.T.copy() for x in data]
            
        n_features = data[0].shape[1]

        n_samples_total = 0.0
        for class_samples in data:
            n_samples_total += class_samples.shape[0]

        Sb = np.zeros((n_features, n_features))
        Sw = np.zeros((n_features, n_features))
        mean_vectors = np.zeros((len(data), n_features,))
        mean = np.zeros((n_features, 1))

        for class_idx, class_samples in enumerate(data_t):
            for feature_idx in range(n_features):
                mean_vectors[class_idx, feature_idx] = np.mean(class_samples[feature_idx])
        for feature_idx in range(n_features):
            mean[feature_idx] = np.mean(mean_vectors[::, feature_idx])

        for cl in range(len(data)):
            priors = data[cl].shape[0] / n_samples_total
            Sw += priors * empirical_covariance(data[cl])

        for cl, mean_v in enumerate(mean_vectors):
            priors = data[cl].shape[0] / n_samples_total
            Sb += (mean_v - mean).dot(np.transpose(mean_v - mean))

        return Sb, Sw


class DiscriminantAnalysisV2(BaseDiscriminantAnalysis):
    """
    The latest implementation of the DA Sb and Sw matrices are computed
    in the same way as scikit does 
    """
    
    def calculate_matrices(self, data: Union[np.ndarray, List[np.ndarray]], data_t=None) -> Tuple[np.ndarray, np.ndarray]:
        if data[0].shape[1] == 1:
            return single_feature_statistic(data)
        
        X = np.vstack(data)
        Y = []
        priors = []
        for i, entry in enumerate(data):
            Y.extend([i] * len(entry))
            priors.append(
                len(entry) / len(X)
            )
        
        covs = _class_cov(X, Y, priors)
        
        Sw = covs
        St = _cov(X)
        Sb = St - Sw
        return Sb, Sw
