from typing import Annotated, overload

import numpy
from numpy.typing import NDArray


build_time: str = '2025-10-23T15:57:52Z'

commit_hash: str = '42a4b5c0c28b2ca237982197d54851054b584a80'

@overload
def update_cholesky_inplace(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')]) -> None:
    """
    Cholesky factorization update. Overwrites its arguments.

    L̃L̃ᵀ + ÃÃᵀ = LLᵀ + AAᵀ

    Parameters
    ----------
    L : (k × n), lower-trapezoidal, Fortran order
        On entry, the original Cholesky factor L.
        On exit, contains the updated Cholesky factor L̃.

    A : (k × m), rectangular, Fortran order
        On entry, the update matrix A.
        On exit, contains the k-n bottom rows of the remaining update matrix Ã
        (the top n rows of Ã are zero).
    """

@overload
def update_cholesky_inplace(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')]) -> None: ...

@overload
def downdate_cholesky_inplace(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')]) -> None:
    """
    Cholesky factorization downdate. Overwrites its arguments.

    L̃L̃ᵀ - ÃÃᵀ = LLᵀ - AAᵀ

    Parameters
    ----------
    L : (k × n), lower-trapezoidal, Fortran order
        On entry, the original Cholesky factor L.
        On exit, contains the updated Cholesky factor L̃.

    A : (k × m), rectangular, Fortran order
        On entry, the downdate matrix A.
        On exit, contains the k-n bottom rows of the remaining downdate matrix Ã
        (the top n rows of Ã are zero).
    """

@overload
def downdate_cholesky_inplace(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')]) -> None: ...

@overload
def update_cholesky_sign_inplace(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')], signs: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> None:
    """
    Cholesky factorization update with signed columns. Overwrites its arguments.

    L̃L̃ᵀ + ÃSÃᵀ = LLᵀ + ASAᵀ,
    where S = np.diag(np.copysign(np.ones(m), signs)) and signs contains ±0.

    Parameters
    ----------
    L : (k × n), lower-trapezoidal, Fortran order
        On entry, the original Cholesky factor L.
        On exit, contains the updated Cholesky factor L̃.

    A : (k × m), rectangular, Fortran order
        On entry, the update matrix A.
        On exit, contains the k-n bottom rows of the remaining update matrix Ã
        (the top n rows of Ã are zero).

    signs : m-vector
        Signs that determine whether a column of A is added (+0) or removed (-0).
        Values other than ±0 are not allowed.
    """

@overload
def update_cholesky_sign_inplace(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')], signs: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> None: ...

@overload
def update_cholesky_diag_inplace(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu')], diag: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> None:
    """
    Cholesky factorization update with diagonal scaling. Overwrites its arguments.

    L̃L̃ᵀ + ÃDÃᵀ = LLᵀ + ADAᵀ,
    where D = np.diag(diag).

    Parameters
    ----------
    L : (k × n), lower-trapezoidal, Fortran order
        On entry, the original Cholesky factor L.
        On exit, contains the updated Cholesky factor L̃.

    A : (k × m), rectangular, Fortran order
        On entry, the update matrix A.
        On exit, contains the k-n bottom rows of the remaining update matrix Ã
        (the top n rows of Ã are zero).

    diag : m-vector
        Scale factors corresponding to the columns of A.
    """

@overload
def update_cholesky_diag_inplace(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu')], diag: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> None: ...

@overload
def update_cholesky(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Cholesky factorization update. Returns updated copies.

    L̃L̃ᵀ + ÃÃᵀ = LLᵀ + AAᵀ

    Parameters
    ----------
    L : (k × n), lower-trapezoidal
        The original Cholesky factor.

    A : (k × m), rectangular
        The update matrix.

    Returns
    -------
    L̃ : (k × n)
        The updated Cholesky factor.

    A_rem : (k × m)
        Contains the k-n bottom rows of the remaining update matrix Ã.
        The top n rows of Ã are zero (not stored explicitly).
        The top n rows of A_rem contain Householder reflectors.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization update. Together with the top n rows of A_rem,
        this can be used to apply the block Householder transformation to other matrices.
        The number of rows depends on the block size and is architecture-dependent.
    """

@overload
def update_cholesky(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...

@overload
def downdate_cholesky(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Cholesky factorization downdate. Returns updated copies.

    L̃L̃ᵀ - ÃÃᵀ = LLᵀ - AAᵀ

    Parameters
    ----------
    L : (k × n), lower-trapezoidal
        The original Cholesky factor.

    A : (k × m), rectangular
        The downdate matrix.

    Returns
    -------
    L̃ : (k × n)
        The updated Cholesky factor.

    A_rem : (k × m)
        Contains the k-n bottom rows of the remaining downdate matrix Ã.
        The top n rows of Ã are zero (not stored explicitly).
        The top n rows of A_rem contain Householder reflectors.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization update. Together with the top n rows of A_rem,
        this can be used to apply the block Householder transformation to other matrices.
        The number of rows depends on the block size and is architecture-dependent.
    """

@overload
def downdate_cholesky(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...

@overload
def update_cholesky_sign(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], signs: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Cholesky factorization update with signed columns. Returns updated copies.

    L̃L̃ᵀ + ÃSÃᵀ = LLᵀ + ASAᵀ,
    where S = np.diag(np.copysign(np.ones(m), signs)) and signs contains ±0.

    Parameters
    ----------
    L : (k × n), lower-trapezoidal
        The original Cholesky factor.

    A : (k × m), rectangular
        The update matrix.

    signs : m-vector
        Signs that determine whether a column of A is added (+0) or removed (-0).
        Values other than ±0 are not allowed.

    Returns
    -------
    L̃ : (k × n)
        The updated Cholesky factor.

    A_rem : (k × m)
        Contains the k-n bottom rows of the remaining update matrix Ã.
        The top n rows of Ã are zero (not stored explicitly).
        The top n rows of A_rem contain Householder reflectors.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization update. Together with the top n rows of A_rem,
        this can be used to apply the block Householder transformation to other matrices.
        The number of rows depends on the block size and is architecture-dependent.
    """

@overload
def update_cholesky_sign(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], signs: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...

@overload
def update_cholesky_diag(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], diag: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Cholesky factorization update with diagonal scaling. Returns updated copies.

    L̃L̃ᵀ + ÃDÃᵀ = LLᵀ + ADAᵀ,
    where D = np.diag(diag).

    Parameters
    ----------
    L : (k × n), lower-trapezoidal
        The original Cholesky factor.

    A : (k × m), rectangular
        The update matrix.

    diag : m-vector
        Scale factors corresponding to the columns of A.

    Returns
    -------
    L̃ : (k × n)
        The updated Cholesky factor.

    A_rem : (k × m)
        Contains the k-n bottom rows of the remaining update matrix Ã.
        The top n rows of Ã are zero (not stored explicitly).
        The top n rows of A_rem contain Householder reflectors.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization update. Together with the top n rows of A_rem,
        this can be used to apply the block Householder transformation to other matrices.
        The number of rows depends on the block size and is architecture-dependent.
    """

@overload
def update_cholesky_diag(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], diag: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='A', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...

@overload
def update_apply_householder(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], W: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Apply a block Householder transformation generated during a Cholesky
    factorization update. Returns updated copies.

    (L̃ Ã) = (L A) Q

    where Q is the block Householder transformation represented by W and B.

    Parameters
    ----------
    L : (l × n), rectangular
        Matrix to apply the transformation to.

    A : (l × m), rectangular
        Matrix to apply the transformation to.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization update.

    B : (k × m), rectangular
        The Householder reflector vectors generated during the Cholesky
        factorization update.

    Returns
    -------
    L̃ : (l × n)
        The updated matrix L.

    Ã : (l × m)
        The updated matrix A.
    """

@overload
def update_apply_householder(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], W: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...

@overload
def downdate_apply_householder(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], W: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Apply a block Householder transformation generated during a Cholesky
    factorization downdate. Returns updated copies.

    (L̃ Ã) = (L A) Q

    where Q is the block Householder transformation represented by W and B.

    Parameters
    ----------
    L : (l × n), rectangular
        Matrix to apply the transformation to.

    A : (l × m), rectangular
        Matrix to apply the transformation to.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization downdate.

    B : (k × m), rectangular
        The Householder reflector vectors generated during the Cholesky
        factorization downdate.

    Returns
    -------
    L̃ : (l × n)
        The updated matrix L.

    Ã : (l × m)
        The updated matrix A.
    """

@overload
def downdate_apply_householder(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], W: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...

@overload
def update_apply_householder_sign(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], signs: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='A', device='cpu', writable=False)], W: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Apply a block Householder transformation generated during a Cholesky
    factorization update with signed columns. Returns updated copies.

    (L̃ Ã) = (L A) Q

    where Q is the block Householder transformation represented by W, B and signs.

    Parameters
    ----------
    L : (l × n), rectangular
        Matrix to apply the transformation to.

    A : (l × m), rectangular
        Matrix to apply the transformation to.

    signs : m-vector
        Signs that determine whether a column of A was added (+0) or removed (-0).
        Values other than ±0 are not allowed.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization update.

    B : (k × m), rectangular
        The Householder reflector vectors generated during the Cholesky
        factorization update.

    Returns
    -------
    L̃ : (l × n)
        The updated matrix L.

    Ã : (l × m)
        The updated matrix A.
    """

@overload
def update_apply_householder_sign(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], signs: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='A', device='cpu', writable=False)], W: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...

@overload
def update_apply_householder_diag(L: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float64], dict(shape=(None, None), device='cpu', writable=False)], diag: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='A', device='cpu', writable=False)], W: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]:
    """
    Apply a block Householder transformation generated during a Cholesky
    factorization update with diagonal scaling. Returns updated copies.

    (L̃ Ã) = (L A) Q

    where Q is the block Householder transformation represented by W, B and diag.

    Parameters
    ----------
    L : (l × n), rectangular
        Matrix to apply the transformation to.

    A : (l × m), rectangular
        Matrix to apply the transformation to.

    diag : m-vector
        Scale factors corresponding to the columns of A used when generating the
        Householder transformation.

    W : (r × n)
        The upper triangular Householder representations generated during the
        Cholesky factorization update.

    B : (k × m), rectangular
        The Householder reflector vectors generated during the Cholesky
        factorization update.

    Returns
    -------
    L̃ : (l × n)
        The updated matrix L.

    Ã : (l × m)
        The updated matrix A.
    """

@overload
def update_apply_householder_diag(L: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], A: Annotated[NDArray[numpy.float32], dict(shape=(None, None), device='cpu', writable=False)], diag: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='A', device='cpu', writable=False)], W: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)], B: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F', device='cpu', writable=False)]) -> tuple[Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]]: ...
