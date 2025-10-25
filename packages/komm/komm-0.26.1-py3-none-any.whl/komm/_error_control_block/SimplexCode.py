from functools import cache

from typeguard import typechecked

from .._util.docs import mkdocstrings
from .HammingCode import hamming_parity_submatrix
from .SystematicBlockCode import SystematicBlockCode


@mkdocstrings(filters=["!.*"])
@typechecked
class SimplexCode(SystematicBlockCode):
    r"""
    Simplex (maximum-length) code. For a given parameter $\kappa \geq 2$, it is the [linear block code](/ref/BlockCode) with generator matrix whose columns are all the $2^\kappa - 1$ nonzero binary $\kappa$-tuples. The simplex code (also known as maximum-length code) has the following parameters:

    - Length: $n = 2^\kappa - 1$
    - Dimension: $k = \kappa$
    - Redundancy: $m = 2^\kappa - \kappa - 1$
    - Minimum distance: $d = 2^{\kappa - 1}$

    In its extended version, the simplex code has the following parameters:

    - Length: $n = 2^\kappa$
    - Dimension: $k = \kappa + 1$
    - Redundancy: $m = 2^\kappa - \kappa - 1$
    - Minimum distance: $d = 2^{\kappa - 1}$

    Notes:
        - For $\kappa = 2$ it reduces to the [single parity-check code](/ref/SingleParityCheckCode) of length $3$.
        - Its dual is the [Hamming code](/ref/HammingCode).
        - Simplex codes are constant-weight codes.

    Parameters:
        kappa: The parameter $\kappa$ of the code. Must satisfy $\kappa \geq 2$.
        extended: Whether to use the extended version of the Simplex code. Default is `False`.

    This class represents the code in [systematic form](/ref/SystematicBlockCode), with the information set on the left.

    Examples:
        >>> code = komm.SimplexCode(3)
        >>> (code.length, code.dimension, code.redundancy)
        (7, 3, 4)
        >>> code.generator_matrix
        array([[1, 0, 0, 1, 1, 0, 1],
               [0, 1, 0, 1, 0, 1, 1],
               [0, 0, 1, 0, 1, 1, 1]])
        >>> code.check_matrix
        array([[1, 1, 0, 1, 0, 0, 0],
               [1, 0, 1, 0, 1, 0, 0],
               [0, 1, 1, 0, 0, 1, 0],
               [1, 1, 1, 0, 0, 0, 1]])
        >>> code.minimum_distance()
        4

        >>> code = komm.SimplexCode(3, extended=True)
        >>> (code.length, code.dimension, code.redundancy)
        (8, 4, 4)
        >>> code.generator_matrix
        array([[1, 0, 0, 0, 1, 1, 0, 1],
               [0, 1, 0, 0, 1, 0, 1, 1],
               [0, 0, 1, 0, 0, 1, 1, 1],
               [0, 0, 0, 1, 1, 1, 1, 0]])
        >>> code.check_matrix
        array([[1, 1, 0, 1, 1, 0, 0, 0],
               [1, 0, 1, 1, 0, 1, 0, 0],
               [0, 1, 1, 1, 0, 0, 1, 0],
               [1, 1, 1, 0, 0, 0, 0, 1]])
        >>> code.minimum_distance()
        4
    """

    def __init__(self, kappa: int, extended: bool = False) -> None:
        if not kappa >= 2:
            raise ValueError("'kappa' must be at least 2")
        self.kappa = kappa
        self.extended = extended
        super().__init__(parity_submatrix=hamming_parity_submatrix(kappa, extended).T)

    def __repr__(self) -> str:
        args = f"kappa={self.kappa}, extended={self.extended}"
        return f"{self.__class__.__name__}({args})"

    @cache
    def minimum_distance(self) -> int:
        return 2 ** (self.kappa - 1)
