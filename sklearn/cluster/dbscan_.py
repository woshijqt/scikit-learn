# -*- coding: utf-8 -*-
"""
DBSCAN: Density-Based Spatial Clustering of Applications with Noise
"""

# Author: Robert Layton <robertlayton@gmail.com>
#         Joel Nothman <joel.nothman@gmail.com>
#         Lars Buitinck
#
# License: BSD 3 clause

import warnings

import numpy as np
from scipy import sparse

from ..base import BaseEstimator, ClusterMixin
from ..metrics import pairwise_distances
from ..utils import check_array, check_consistent_length
from ..neighbors import NearestNeighbors

from ._dbscan_inner import dbscan_inner


def dbscan(X, eps=0.5, min_samples=5, metric='minkowski',
           algorithm='auto', leaf_size=30, p=2, sample_weight=None,
           random_state=None):
    """Perform DBSCAN clustering from vector array or distance matrix.

    Read more in the :ref:`User Guide <dbscan>`.

    Parameters
    ----------
    X : array or sparse (CSR) matrix of shape (n_samples, n_features), or \
            array of shape (n_samples, n_samples)
        A feature array, or array of distances between samples if
        ``metric='precomputed'``.

    eps : float, optional
        The maximum distance between two samples for them to be considered
        as in the same neighborhood.

    min_samples : int, optional
        The number of samples (or total weight) in a neighborhood for a point
        to be considered as a core point. This includes the point itself.

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string or callable, it must be one of
        the options allowed by metrics.pairwise.pairwise_distances for its
        metric parameter.
        If metric is "precomputed", X is assumed to be a distance matrix and
        must be square. X may be a sparse matrix (CSR preferred) in which case
        only "nonzero" elements may be considered neighbors for DBSCAN.

    algorithm : {'auto', 'ball_tree', 'kd_tree', 'brute'}, optional
        The algorithm to be used by the NearestNeighbors module
        to compute pointwise distances and find nearest neighbors.
        See NearestNeighbors module documentation for details.

    leaf_size : int, optional (default = 30)
        Leaf size passed to BallTree or cKDTree. This can affect the speed
        of the construction and query, as well as the memory required
        to store the tree. The optimal value depends
        on the nature of the problem.

    p : float, optional
        The power of the Minkowski metric to be used to calculate distance
        between points.

    sample_weight : array, shape (n_samples,), optional
        Weight of each sample, such that a sample with a weight of at least
        ``min_samples`` is by itself a core sample; a sample with negative
        weight may inhibit its eps-neighbor from being core.
        Note that weights are absolute, and default to 1.

    random_state: numpy.RandomState, optional
        Deprecated and ignored as of version 0.16, will be removed in version
        0.18. DBSCAN does not use random initialization.

    Returns
    -------
    core_samples : array [n_core_samples]
        Indices of core samples.

    labels : array [n_samples]
        Cluster labels for each point.  Noisy samples are given the label -1.

    Notes
    -----
    See examples/cluster/plot_dbscan.py for an example.

    This implementation bulk-computes all neighborhood queries, which increases
    the memory complexity to O(n.d) where d is the average number of neighbors,
    while original DBSCAN had memory complexity O(n).

    References
    ----------
    Ester, M., H. P. Kriegel, J. Sander, and X. Xu, "A Density-Based
    Algorithm for Discovering Clusters in Large Spatial Databases with Noise".
    In: Proceedings of the 2nd International Conference on Knowledge Discovery
    and Data Mining, Portland, OR, AAAI Press, pp. 226-231. 1996
    """
    if not eps > 0.0:
        raise ValueError("eps must be positive.")
    if random_state is not None:
        warnings.warn("The parameter random_state is deprecated in 0.16 "
                      "and will be removed in version 0.18. "
                      "DBSCAN is deterministic except for rare border cases.",
                      category=DeprecationWarning)

    X = check_array(X, accept_sparse='csr')
    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)
        check_consistent_length(X, sample_weight)

    # Calculate neighborhood for all samples. This excludes the query sample,
    # but its weight is incorporated into n_neighbors below.
    if metric == 'precomputed':
        D = pairwise_distances(X, metric=metric)
        neighborhoods = np.empty(X.shape[0], dtype=object)
        if sparse.issparse(D):
            D_mask = D.data <= eps
            masked_indices = D.indices.astype(np.intp)[D_mask]
            masked_indptr = np.cumsum(D_mask)[D.indptr[1:-1] - 1]
            neighborhoods[:] = np.split(masked_indices, masked_indptr)
        else:
            neighborhoods[:] = [np.setdiff1d(np.where(x <= eps)[0], [i],
                                             assume_unique=True)
                                for i, x in enumerate(D)]
    else:
        neighbors_model = NearestNeighbors(radius=eps, algorithm=algorithm,
                                           leaf_size=leaf_size,
                                           metric=metric, p=p)
        neighbors_model.fit(X)
        # This has worst case O(n^2) memory complexity
        neighborhoods = neighbors_model.radius_neighbors(return_distance=False)

    # n_neighbors includes the weight of a sample and its eps-neighbors
    if sample_weight is None:
        n_neighbors = np.array([len(neighbors) + 1
                                for neighbors in neighborhoods])
    else:
        n_neighbors = (sample_weight +
                       np.array([np.sum(sample_weight[neighbors])
                                 for neighbors in neighborhoods]))

    # Initially, all samples are noise.
    labels = -np.ones(X.shape[0], dtype=np.intp)

    # A list of all core samples found.
    core_samples = np.asarray(n_neighbors >= min_samples, dtype=np.uint8)
    dbscan_inner(core_samples, neighborhoods, labels)
    return np.where(core_samples)[0], labels


class DBSCAN(BaseEstimator, ClusterMixin):
    """Perform DBSCAN clustering from vector array or distance matrix.

    DBSCAN - Density-Based Spatial Clustering of Applications with Noise.
    Finds core samples of high density and expands clusters from them.
    Good for data which contains clusters of similar density.

    Read more in the :ref:`User Guide <dbscan>`.

    Parameters
    ----------
    eps : float, optional
        The maximum distance between two samples for them to be considered
        as in the same neighborhood.
    min_samples : int, optional
        The number of samples (or total weight) in a neighborhood for a point
        to be considered as a core point. This includes the point itself.
    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string or callable, it must be one of
        the options allowed by metrics.pairwise.calculate_distance for its
        metric parameter.
        If metric is "precomputed", X is assumed to be a distance matrix and
        must be square. X may be a sparse matrix (CSR preferred) in which case
        only "nonzero" elements may be considered neighbors for DBSCAN.
    algorithm : {'auto', 'ball_tree', 'kd_tree', 'brute'}, optional
        The algorithm to be used by the NearestNeighbors module
        to compute pointwise distances and find nearest neighbors.
        See NearestNeighbors module documentation for details.
    leaf_size : int, optional (default = 30)
        Leaf size passed to BallTree or cKDTree. This can affect the speed
        of the construction and query, as well as the memory required
        to store the tree. The optimal value depends
        on the nature of the problem.
    random_state: numpy.RandomState, optional
        Deprecated and ignored as of version 0.16, will be removed in version
        0.18. DBSCAN does not use random initialization.

    Attributes
    ----------
    core_sample_indices_ : array, shape = [n_core_samples]
        Indices of core samples.

    components_ : array, shape = [n_core_samples, n_features]
        Copy of each core sample found by training.

    labels_ : array, shape = [n_samples]
        Cluster labels for each point in the dataset given to fit().
        Noisy samples are given the label -1.

    Notes
    -----
    See examples/cluster/plot_dbscan.py for an example.

    This implementation bulk-computes all neighborhood queries, which increases
    the memory complexity to O(n.d) where d is the average number of neighbors,
    while original DBSCAN had memory complexity O(n).

    References
    ----------
    Ester, M., H. P. Kriegel, J. Sander, and X. Xu, "A Density-Based
    Algorithm for Discovering Clusters in Large Spatial Databases with Noise".
    In: Proceedings of the 2nd International Conference on Knowledge Discovery
    and Data Mining, Portland, OR, AAAI Press, pp. 226-231. 1996
    """

    def __init__(self, eps=0.5, min_samples=5, metric='euclidean',
                 algorithm='auto', leaf_size=30, p=None, random_state=None):
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric
        self.algorithm = algorithm
        self.leaf_size = leaf_size
        self.p = p
        self.random_state = random_state

    def fit(self, X, y=None, sample_weight=None):
        """Perform DBSCAN clustering from features or distance matrix.

        Parameters
        ----------
        X : array or sparse (CSR) matrix of shape (n_samples, n_features), or \
                array of shape (n_samples, n_samples)
            A feature array, or array of distances between samples if
            ``metric='precomputed'``.
        sample_weight : array, shape (n_samples,), optional
            Weight of each sample, such that a sample with a weight of at least
            ``min_samples`` is by itself a core sample; a sample with negative
            weight may inhibit its eps-neighbor from being core.
            Note that weights are absolute, and default to 1.
        """
        X = check_array(X, accept_sparse='csr')
        clust = dbscan(X, sample_weight=sample_weight, **self.get_params())
        self.core_sample_indices_, self.labels_ = clust
        if len(self.core_sample_indices_):
            # fix for scipy sparse indexing issue
            self.components_ = X[self.core_sample_indices_].copy()
        else:
            # no core samples
            self.components_ = np.empty((0, X.shape[1]))
        return self

    def fit_predict(self, X, y=None, sample_weight=None):
        """Performs clustering on X and returns cluster labels.

        Parameters
        ----------
        X : array or sparse (CSR) matrix of shape (n_samples, n_features), or \
                array of shape (n_samples, n_samples)
            A feature array, or array of distances between samples if
            ``metric='precomputed'``.
        sample_weight : array, shape (n_samples,), optional
            Weight of each sample, such that a sample with a weight of at least
            ``min_samples`` is by itself a core sample; a sample with negative
            weight may inhibit its eps-neighbor from being core.
            Note that weights are absolute, and default to 1.

        Returns
        -------
        y : ndarray, shape (n_samples,)
            cluster labels
        """
        self.fit(X, sample_weight=sample_weight)
        return self.labels_
