"""Unsupervised Embedding Quality Evaluation metrics.

https://arxiv.org/pdf/2305.16562.pdf
"""

from typing import Any, Literal, cast, overload

import numpy as np
from numpy import linalg
from numpy.typing import ArrayLike, NDArray

from corvic import result


@overload
def norm(
    x: ArrayLike,
    order: float | Literal["fro", "nuc"] | None,
    axis: None = None,
    *,
    keepdims: bool = False,
) -> float: ...


@overload
def norm(
    x: NDArray[Any],
    order: float | Literal["fro", "nuc"] | None,
    axis: int,
    *,
    keepdims: bool = False,
) -> float: ...


def norm(
    x: ArrayLike,
    order: float | Literal["fro", "nuc"] | None,
    axis: int | None = None,
    *,
    keepdims: bool = False,
) -> float | NDArray[Any]:
    return linalg.norm(  # pyright: ignore[reportReturnType]
        x=x,
        ord=order,
        axis=axis,
        keepdims=keepdims,
    )


def _validate_embedding_array(
    embeddings: NDArray[Any],
) -> result.Ok[None] | result.InvalidArgumentError:
    embeddings_ndim = 2
    if embeddings.ndim != embeddings_ndim:
        return result.InvalidArgumentError(
            f"embeddings ndim must be {embeddings_ndim}",
            ndim=embeddings.ndim,
        )
    if not np.issubdtype(embeddings.dtype, np.number):
        return result.InvalidArgumentError(
            "embeddings must have a numerical dtype",
            dtype=str(embeddings.dtype),
        )
    return result.Ok(None)


def stable_rank(
    embeddings: NDArray[Any], *, normalize: bool = False
) -> result.InvalidArgumentError | result.Ok[float]:
    r"""Stable rank metric.

    Stable rank (also called effective rank or intrinsic dimension
    of a matrix) is another fundamental quality in numerical
    analysis of random matrices.

    Numerical rank of a matrix M is defined as:

    .. math::
        \frac{\|\mathbf{M}\|_F}{\|\mathbf{M}\|_2^2}
    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    try:
        numerator = norm(embeddings, order="fro")
        denominator = norm(embeddings, order=2) ** 2
    except np.linalg.LinAlgError as err:
        return result.InvalidArgumentError.from_(err)

    if not np.isfinite(numerator):
        return result.InvalidArgumentError("embeddings norm_fro is not finite")

    if not np.isfinite(denominator):
        return result.InvalidArgumentError("embeddings norm_2 is not finite")

    if not denominator:
        return result.InvalidArgumentError("embeddings norm_2 is zero")

    metric = numerator / denominator
    if normalize:
        metric = 1 - 1 / (1 + metric)
    return result.Ok(float(metric))


def self_cluster(
    embeddings: NDArray[Any],
) -> result.InvalidArgumentError | result.Ok[float]:
    r"""SelfCluster metric.

    SelfCluster allows us to estimate how much the embeddings
    are clustered in the embedding space compared to random
    distribution on a sphere. The downside of this metric is the
    requirement of pairwise computations, which is expensive
    for large number of points.

    .. math::
        \frac{d\left\|\mathbf{W} \mathbf{W}^{\top}\right\|_F-n(d+n-1)}{(d-1)(n-1) n}

    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    n = embeddings.shape[0]
    d = embeddings.shape[1]

    # Calculate L2 norm along each row
    l2_norms = norm(
        embeddings,
        order=2,
        axis=1,
        keepdims=True,
    )

    normed_embeddings = embeddings / l2_norms
    numerator = d * norm(normed_embeddings @ normed_embeddings.T, order="fro") - n * (
        d + n - 1
    )
    denominator = (d - 1) * (n - 1) * n
    return result.Ok(float(numerator / denominator))


def ne_sum(
    embeddings: NDArray[Any], *, normalize: bool = False
) -> result.InvalidArgumentError | result.Ok[float]:
    r"""NESum metric.

    NESum  analyzes eigenspectrum of the covariance matrix of
    representations. It is introduced as a heuristic metric
    complementing the analysis of features learned by
    the barlow twins loss.

    .. math::
        \sum_i \frac{\lambda_i}{\lambda_0}

    The NESum metric provides insights into the distribution of learned features
    by examining the spread of eigenvalues in the covariance matrix. Higher NESum
    values suggest a broader distribution of features, potentially indicating
    more diverse representation.

    Args:
        embeddings: An array of float.
        normalize: Whether to normalize the result by the number of dimensions.

    Returns:
        The NESum metric value.
    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    covariance = np.cov(embeddings.T)
    try:
        eigenvalues = linalg.eigvals(covariance)
    except np.linalg.LinAlgError as err:
        return result.InvalidArgumentError.from_(err)

    # Discard imaginary part
    eigenvalues = eigenvalues.real

    # Sort eigenvalues in decreasing order
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sorted_indices]

    if eigenvalues[0] == 0:
        return result.Ok(0.0)

    ne_sum_value = float(np.sum(eigenvalues) / eigenvalues[0])
    if normalize:
        ne_sum_value = ne_sum_value / embeddings.shape[0]
    return result.Ok(ne_sum_value)


def condition_number(
    embeddings: NDArray[Any],
    p: float | Literal["fro", "nuc"] = 2,
    *,
    normalize: bool = False,
) -> result.InvalidArgumentError | result.Ok[float]:
    """Pseudo-condition number metric.

    Numerical linear algebra provides us with more tools for
    analysing behaviors of linear classifiers. One of the classic
    ones is the condition number, or, in the case of non-square
    matrices, its generalized version. For
    example, k2 is used to detect multicollinearity in linear and
    logistic regression

    Args:
        embeddings: The matrix whose condition number is sought.
        p: {1, -1, 2, -2, inf, -inf, 'fro'}, optional
        Order of the norm used in the condition number computation:

        =====  ============================
        p      norm for matrices
        =====  ============================
        None   2-norm, computed directly using the ``SVD``
        'fro'  Frobenius norm
        inf    max(sum(abs(x), axis=1))
        -inf   min(sum(abs(x), axis=1))
        1      max(sum(abs(x), axis=0))
        -1     min(sum(abs(x), axis=0))
        2      2-norm (largest sing. value)
        -2     smallest singular value
        =====  ============================

        inf means the `numpy.inf` object, and the Frobenius norm is
        the root-of-sum-of-squares norm.
        normalize: Whether to normalize the result between 0 and 1.

    Returns:
        {float, inf}
        The condition number of the matrix. May be infinite.
    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    try:
        metric = float(np.linalg.cond(embeddings, p=p))
    except np.linalg.LinAlgError as err:
        return result.InvalidArgumentError.from_(err)

    if normalize:
        metric = 1 - 1 / (1 + metric)
    return result.Ok(metric)


def rcondition_number(
    embeddings: NDArray[Any],
    p: float | Literal["fro", "nuc"] = 2,
    *,
    normalize: bool = False,
) -> result.InvalidArgumentError | result.Ok[float]:
    """Reciprocal of the condition number."""
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    try:
        metric = float(1 / np.linalg.cond(embeddings, p=p))
    except np.linalg.LinAlgError as err:
        return result.InvalidArgumentError.from_(err)

    if normalize:
        metric = 1 - 1 / (1 + metric)
    return result.Ok(metric)


def rank_me(
    embeddings: NDArray[Any], epsilon: float = 1e-7
) -> result.InvalidArgumentError | result.Ok[float]:
    r"""RankMe metric.

    RankMe is a method based on estimating the effective rank of a matrix.
    In a strict numerical linear algebraic sense, most embed-
    ding matrices are full-rank. “Softer” definitions allow to
    capture not only fully collapsed dimensions but also general
    underutilization of the parameter space.

    ϵ is a small constant dependent on the data type,
    typically 10**-7 for float32

    https://arxiv.org/pdf/2210.02885.pdf
    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    sigma = np.linalg.svd(embeddings, compute_uv=False)
    pk = (sigma / np.linalg.norm(sigma, ord=1)) + epsilon
    entropy = -np.sum(pk * np.log(pk))
    return result.Ok(float(np.exp(entropy)))


def mu_coherence(
    embeddings: NDArray[Any],
) -> result.InvalidArgumentError | result.Ok[float]:
    """Coherence metric.

    Matrix coherence measures the extent to which the
    singular vectors of a matrix are correlated with the
    standard basis.

    https://arxiv.org/ftp/arxiv/papers/1408/1408.2044.pdf
    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    u, _, _ = np.linalg.svd(embeddings, compute_uv=True, full_matrices=False)
    n = u.shape[0]
    r = u.shape[1]
    assert r < n  # noqa: S101
    return result.Ok(float(np.sqrt(n) * np.max(np.abs(u))))


def mu0_coherence(
    embeddings: NDArray[Any],
) -> result.InvalidArgumentError | result.Ok[float]:
    """μ0-Coherence metric.

    Matrix coherence measures the extent to which the
    singular vectors of a matrix are correlated with the
    standard basis. In comparison to μ, μ0 is a more
    robust measure of coherence, as it deals with row
    norms of U, rather than the maximum entry of U.

    https://www.cs.cmu.edu/~atalwalk/coh.pdf
    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    u, _, _ = np.linalg.svd(embeddings, compute_uv=True, full_matrices=False)
    n = u.shape[0]
    r = u.shape[1]
    assert r < n  # noqa: S101
    return result.Ok(float((n / r) * np.max(linalg.norm(u, axis=1, ord=2) ** 2)))


def alpha_req(
    embeddings: NDArray[Any],
) -> result.InvalidArgumentError | result.Ok[float]:
    r"""alpha-ReQ metric.

    alpha-ReQ metric fits a power-law to the sin-
    gular values of representations. Logarithmic
    decay of the spectrum with slope alpha = 1 was recently
    proven to provide the best generalization in infinite-
    dimensional analysis of linear regression. In practice,
    a simple linear regression estimator on a log-log scale
    is used to estimate the value of alpha. This approach
    for estimating the power-law exponent is considered
    inaccurate.

    https://arxiv.org/pdf/2202.05808.pdf
    """
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    from sklearn.linear_model import LinearRegression

    covariance = np.cov(embeddings.T)
    eigenvalues = linalg.eigvals(covariance)

    # Sort eigenvalues in decreasing order
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sorted_indices]

    index = np.arange(0, eigenvalues.shape[0], dtype=int) + 1
    log_index = np.log(index)
    log_eigenvalues = np.log(eigenvalues)

    reg = LinearRegression().fit(
        log_index.reshape(-1, 1), log_eigenvalues.reshape(-1, 1)
    )
    coef = cast(
        float,
        reg.coef_[0][0],  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    )
    alpha = -coef
    return result.Ok(float(alpha))


def classification(
    embeddings: NDArray[Any], target: NDArray[np.int32]
) -> result.InvalidArgumentError | result.Ok[float]:
    """Accuracy classification score on a target column."""
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    from sklearn.svm import SVC

    x_train, x_test, y_train, y_test = train_test_split(
        embeddings, target, test_size=0.33, random_state=42
    )

    x_train = cast(NDArray[Any], x_train)
    x_test = cast(NDArray[Any], x_test)
    y_train = cast(NDArray[np.int32], y_train)
    y_test = cast(NDArray[np.int32], y_test)

    model = SVC(class_weight="balanced")
    _ = model.fit(X=x_train, y=y_train)
    y_pred = model.predict(X=x_test)
    return result.Ok(float(accuracy_score(y_true=y_test, y_pred=y_pred)))


def regression(
    embeddings: NDArray[Any], target: NDArray[Any]
) -> result.InvalidArgumentError | result.Ok[float]:
    """Mean absolute error regression loss on a target column."""
    match _validate_embedding_array(embeddings):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            pass

    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import train_test_split
    from sklearn.svm import SVR

    x_train, x_test, y_train, y_test = train_test_split(
        embeddings, target, test_size=0.33, random_state=42
    )

    x_train = cast(NDArray[Any], x_train)
    x_test = cast(NDArray[Any], x_test)
    y_train = cast(NDArray[Any], y_train)
    y_test = cast(NDArray[Any], y_test)

    model = SVR()
    _ = model.fit(X=x_train, y=y_train)
    y_pred = model.predict(X=x_test)
    return result.Ok(float(mean_absolute_error(y_true=y_test, y_pred=y_pred)))
