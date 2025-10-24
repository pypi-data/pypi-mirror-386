from __future__ import annotations

import operator
from enum import IntEnum

import numpy as np
import builtins
import copy
import functools
import math
import sys
from copy import copy, deepcopy
from dataclasses import dataclass, field, InitVar
from typing_extensions import (
    Optional,
    List,
    Tuple,
    Dict,
    Sequence,
    Any,
    Type,
    Self,
    ClassVar,
    TYPE_CHECKING,
    Iterable,
    Union,
    TypeVar,
    Callable,
    overload,
)

import casadi as ca
from scipy import sparse as sp

from ..exceptions import (
    HasFreeSymbolsError,
    NotSquareMatrixError,
    WrongDimensionsError,
    SpatialTypesError,
)

if TYPE_CHECKING:
    from ..world_description.world_entity import KinematicStructureEntity, Connection

EPS: float = sys.float_info.epsilon * 4.0


@dataclass
class CompiledFunction:
    """
    A compiled symbolic function that can be efficiently evaluated with CasADi.

    This class compiles symbolic expressions into optimized CasADi functions that can be
    evaluated efficiently. It supports both sparse and dense matrices and handles
    parameter substitution automatically.
    """

    expression: SymbolicType
    """
    The symbolic expression to compile.
    """
    symbol_parameters: Optional[List[List[Symbol]]] = None
    """
    The input parameters for the compiled symbolic expression.
    """
    sparse: bool = False
    """
    Whether to return a sparse matrix or a dense numpy matrix
    """

    _compiled_casadi_function: ca.Function = field(init=False)

    _function_buffer: ca.FunctionBuffer = field(init=False)
    _function_evaluator: functools.partial = field(init=False)
    """
    Helpers to avoid new memory allocation during function evaluation
    """

    _out: Union[np.ndarray, sp.csc_matrix] = field(init=False)
    """
    The result of a function evaluation is stored in this variable.
    """

    _is_constant: bool = False
    """
    Used to memorize if the result must be recomputed every time.
    """

    def __post_init__(self):
        if self.symbol_parameters is None:
            self.symbol_parameters = [self.expression.free_symbols()]
        else:
            symbols = set()
            for symbol_parameter in self.symbol_parameters:
                symbols.update(set(symbol_parameter))
            missing_symbols = set(self.expression.free_symbols()).difference(symbols)
            if missing_symbols:
                raise HasFreeSymbolsError(missing_symbols)

        if len(self.symbol_parameters) == 1 and len(self.symbol_parameters[0]) == 0:
            self.symbol_parameters = []

        if len(self.expression) == 0:
            self._setup_empty_result()
            return

        self._setup_compiled_function()
        self._setup_output_buffer()
        if len(self.symbol_parameters) == 0:
            self._setup_constant_result()

    def _setup_empty_result(self) -> None:
        """
        Setup result for empty expressions.
        """
        if self.sparse:
            self._out = sp.csc_matrix(np.empty(self.expression.shape))
        else:
            self._out = np.empty(self.expression.shape)
        self._is_constant = True

    def _setup_compiled_function(self) -> None:
        """
        Setup the CasADi compiled function.
        """
        casadi_parameters = []
        if len(self.symbol_parameters) > 0:
            # create an array for each List[Symbol]
            casadi_parameters = [
                Expression(data=p).casadi_sx for p in self.symbol_parameters
            ]

        if self.sparse:
            self._compile_sparse_function(casadi_parameters)
        else:
            self._compile_dense_function(casadi_parameters)

    def _compile_sparse_function(self, casadi_parameters: List[Expression]) -> None:
        """
        Compile function for sparse matrices.
        """
        self.expression.casadi_sx = ca.sparsify(self.expression.casadi_sx)
        self._compiled_casadi_function = ca.Function(
            "f", casadi_parameters, [self.expression.casadi_sx]
        )

        self._function_buffer, self._function_evaluator = (
            self._compiled_casadi_function.buffer()
        )
        self.csc_indices, self.csc_indptr = (
            self.expression.casadi_sx.sparsity().get_ccs()
        )
        self.zeroes = np.zeros(self.expression.casadi_sx.nnz())

    def _compile_dense_function(self, casadi_parameters: List[Symbol]) -> None:
        """
        Compile function for dense matrices.

        :param casadi_parameters: List of CasADi parameters for the function
        """
        self.expression.casadi_sx = ca.densify(self.expression.casadi_sx)
        self._compiled_casadi_function = ca.Function(
            "f", casadi_parameters, [self.expression.casadi_sx]
        )

        self._function_buffer, self._function_evaluator = (
            self._compiled_casadi_function.buffer()
        )

    def _setup_output_buffer(self) -> None:
        """
        Setup the output buffer for the compiled function.
        """
        if self.sparse:
            self._setup_sparse_output_buffer()
        else:
            self._setup_dense_output_buffer()

    def _setup_sparse_output_buffer(self) -> None:
        """
        Setup output buffer for sparse matrices.
        """
        self._out = sp.csc_matrix(
            arg1=(
                self.zeroes,
                self.csc_indptr,
                self.csc_indices,
            ),
            shape=self.expression.shape,
        )
        self._function_buffer.set_res(0, memoryview(self._out.data))

    def _setup_dense_output_buffer(self) -> None:
        """
        Setup output buffer for dense matrices.
        """
        if self.expression.shape[1] <= 1:
            shape = self.expression.shape[0]
        else:
            shape = self.expression.shape
        self._out = np.zeros(shape, order="F")
        self._function_buffer.set_res(0, memoryview(self._out))

    def _setup_constant_result(self) -> None:
        """
        Setup result for constant expressions (no parameters).

        For expressions with no free parameters, we can evaluate once and return
        the constant result for all future calls.
        """
        self._function_evaluator()
        self._is_constant = True

    def __call__(self, *args: np.ndarray) -> Union[np.ndarray, sp.csc_matrix]:
        """
        Efficiently evaluate the compiled function with positional arguments, by directly writing the memory of the
        numpy arrays to the memoryview of the compiled function.
        Similarly, the result will be written to the output buffer and doesn't allocate new memory on each eval.

        (Yes, this makes a significant speed different.)

        :param args: A numpy array for each List[Symbol] in self.symbol_parameters.
            .. warning:: Make sure the numpy array is of type float! (check is too expensive)
        :return: The evaluated result as numpy array or sparse matrix
        """
        if self._is_constant:
            return self._out
        for arg_idx, arg in enumerate(args):
            self._function_buffer.set_arg(arg_idx, memoryview(arg))
        self._function_evaluator()
        return self._out

    def call_with_kwargs(self, **kwargs: float) -> np.ndarray:
        """
        Call the object instance with the provided keyword arguments. This method retrieves
        the required arguments from the keyword arguments based on the defined
        `symbol_parameters`, compiles them into an array, and then calls the instance
        with the constructed array.

        :param kwargs: A dictionary of keyword arguments containing the parameters
            that match the symbols defined in `symbol_parameters`.
        :return: A NumPy array resulting from invoking the callable object instance
            with the filtered arguments.
        """
        args = []
        for params in self.symbol_parameters:
            for param in params:
                args.append(kwargs[str(param)])
        filtered_args = np.array(args, dtype=float)
        return self(filtered_args)


@dataclass
class CompiledFunctionWithViews:
    """
    A wrapper for CompiledFunction which automatically splits the result array into multiple views, with minimal
    overhead.
    Useful, when many arrays must be evaluated at the same time, especially when they depend on the same symbols.
    """

    expressions: List[Expression]
    """
    The list of expressions to be compiled, the first len(expressions) many results of __call__ correspond to those
    """

    symbol_parameters: List[List[Symbol]]
    """
    The input parameters for the compiled symbolic expression.
    """

    additional_views: Optional[List[slice]] = None
    """
    If additional views are required that don't correspond to the expressions directly.
    """

    compiled_function: CompiledFunction = field(init=False)
    """
    Reference to the compiled function.
    """

    split_out_view: List[np.ndarray] = field(init=False)
    """
    Views to the out buffer of the compiled function.
    """

    def __post_init__(self):
        combined_expression = Expression.vstack(self.expressions)
        self.compiled_function = combined_expression.compile(
            parameters=self.symbol_parameters, sparse=False
        )
        slices = []
        start = 0
        for expression in self.expressions[:-1]:
            end = start + expression.shape[0]
            slices.append(end)
            start = end
        self.split_out_view = np.split(self.compiled_function._out, slices)
        if self.additional_views is not None:
            for expression_slice in self.additional_views:
                self.split_out_view.append(
                    self.compiled_function._out[expression_slice]
                )

    def __call__(self, *args: np.ndarray) -> List[np.ndarray]:
        """
        :param args: A numpy array for each List[Symbol] in self.symbol_parameters.
        :return: A np array for each expression, followed by arrays corresponding to the additional views.
            They are all views on self.compiled_function.out.
        """
        self.compiled_function(*args)
        return self.split_out_view


def _operation_type_error(arg1: object, operation: str, arg2: object) -> TypeError:
    return TypeError(
        f"unsupported operand type(s) for {operation}: '{arg1.__class__.__name__}' "
        f"and '{arg2.__class__.__name__}'"
    )


@dataclass(eq=False)
class SymbolicType:
    """
    A wrapper around CasADi's ca.SX, with better usability
    """

    casadi_sx: ca.SX = field(kw_only=True, default_factory=ca.SX)
    """
    Reference to the casadi data structure of type casadi.SX
    """

    def __str__(self):
        return str(self.casadi_sx)

    def pretty_str(self) -> List[List[str]]:
        """
        Turns a symbolic type into a more or less readable string.
        """
        result_list = np.zeros(self.shape).tolist()
        for x_index in range(self.shape[0]):
            for y_index in range(self.shape[1]):
                s = str(self[x_index, y_index])
                parts = s.split(", ")
                result = parts[-1]
                for x in reversed(parts[:-1]):
                    equal_position = len(x.split("=")[0])
                    index = x[:equal_position]
                    sub = x[equal_position + 1 :]
                    result = result.replace(index, sub)
                result_list[x_index][y_index] = result
        return result_list

    def __repr__(self):
        return repr(self.casadi_sx)

    def __hash__(self) -> int:
        return self.casadi_sx.__hash__()

    def __getitem__(
        self,
        item: Union[
            np.ndarray, Union[int, slice], Tuple[Union[int, slice], Union[int, slice]]
        ],
    ) -> Expression:
        if isinstance(item, np.ndarray) and item.dtype == bool:
            item = (np.where(item)[0], slice(None, None))
        return Expression(self.casadi_sx[item])

    def __setitem__(
        self,
        key: Union[Union[int, slice], Tuple[Union[int, slice], Union[int, slice]]],
        value: ScalarData,
    ):
        self.casadi_sx[key] = value.casadi_sx if hasattr(value, "casadi_sx") else value

    @property
    def shape(self) -> Tuple[int, int]:
        return self.casadi_sx.shape

    def __len__(self) -> int:
        return self.shape[0]

    def free_symbols(self) -> List[Symbol]:
        return [Symbol._registry[str(s)] for s in ca.symvar(self.casadi_sx)]

    def is_constant(self) -> bool:
        return len(self.free_symbols()) == 0

    def to_np(self) -> np.ndarray:
        """
        Transforms the data into a numpy array.
        Only works if the expression has no free symbols.
        """
        if not self.is_constant():
            raise HasFreeSymbolsError(self.free_symbols())
        if self.shape[0] == self.shape[1] == 0:
            return np.eye(0)
        elif self.casadi_sx.shape[0] == 1 or self.casadi_sx.shape[1] == 1:
            return np.array(ca.evalf(self.casadi_sx)).ravel()
        else:
            return np.array(ca.evalf(self.casadi_sx))

    def compile(
        self, parameters: Optional[List[List[Symbol]]] = None, sparse: bool = False
    ) -> CompiledFunction:
        """
        Compiles the function into a representation that can be executed efficiently. This method
        allows for optional parameterization and the ability to specify whether the compilation
        should consider a sparse representation.

        :param parameters: A list of parameter sets, where each set contains symbols that define
            the configuration for the compiled function. If set to None, no parameters are applied.
        :param sparse: A boolean that determines whether the compiled function should use a
            sparse representation. Defaults to False.
        :return: The compiled function as an instance of CompiledFunction.
        """
        return CompiledFunction(self, parameters, sparse)

    def substitute(
        self,
        old_symbols: List[Symbol],
        new_symbols: List[Union[Symbol, Expression]],
    ) -> Self:
        """
        Replace symbols in an expression with new symbols or expressions.

        This function substitutes symbols in the given expression with the provided
        new symbols or expressions. It ensures that the original expression remains
        unaltered and creates a new instance with the substitutions applied.

        :param old_symbols: A list of symbols in the expression which need to be replaced.
        :param new_symbols: A list of new symbols or expressions which will replace the old symbols.
            The length of this list must correspond to the `old_symbols` list.
        :return: A new expression with the specified symbols replaced.
        """
        old_symbols = Expression(data=[to_sx(s) for s in old_symbols]).casadi_sx
        new_symbols = Expression(data=[to_sx(s) for s in new_symbols]).casadi_sx
        result = copy(self)
        result.casadi_sx = ca.substitute(self.casadi_sx, old_symbols, new_symbols)
        return result

    def norm(self) -> Expression:
        return Expression(ca.norm_2(self.casadi_sx))

    def equivalent(self, other: ScalarData) -> bool:
        """
        Determines whether two scalar expressions are mathematically equivalent by simplifying
        and comparing them.

        :param other: Second scalar expression to compare
        :return: True if the two expressions are equivalent, otherwise False
        """
        other_expression = to_sx(other)
        return ca.is_equal(
            ca.simplify(self.casadi_sx), ca.simplify(other_expression), 5
        )


class BasicOperatorMixin:
    """
    Base class providing arithmetic operations for symbolic types.
    """

    casadi_sx: ca.SX
    """
    Reference to the casadi data structure of type casadi.SX
    """

    def _binary_operation(
        self, other: ScalarData, operation: Callable, reverse: bool = False
    ) -> Expression:
        """
        Performs a binary operation between the current instance and another operand.

        Symbol only allows ScalarData on the righthand sight and implements the reverse version only for NumericalScalaer

        :param other: The operand to be used in the binary operation. Either `ScalarData`
            or `NumericalScalar` types are expected, depending on the context.
        :param operation_name: The name of the binary operation (e.g., "add", "sub", "mul").
        :param reverse: A boolean indicating whether the operation is a reverse operation.
            Defaults to `False`.
        :return: An `Expression` instance resulting from the binary operation, or
            `NotImplemented` if the operand type does not match the expected type.
        """
        if reverse:
            # For reverse operations, check if other is NumericalScalar
            if not isinstance(other, NumericalScalar):
                return NotImplemented
            return Expression(operation(other, self.casadi_sx))
        else:
            # For regular operations, check if other is ScalarData
            if isinstance(other, SymbolicScalar):
                other = other.casadi_sx
            elif not isinstance(other, NumericalScalar):
                return NotImplemented
            return Expression(operation(self.casadi_sx, other))

    # %% arthimetic operators
    def __neg__(self) -> Expression:
        return Expression(self.casadi_sx.__neg__())

    def __add__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.add)

    def __radd__(self, other: NumericalScalar) -> Expression:
        return self._binary_operation(other, operator.add, reverse=True)

    def __sub__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.sub)

    def __rsub__(self, other: NumericalScalar) -> Expression:
        return self._binary_operation(other, operator.sub, reverse=True)

    def __mul__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.mul)

    def __rmul__(self, other: NumericalScalar) -> Expression:
        return self._binary_operation(other, operator.mul, reverse=True)

    def __truediv__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.truediv)

    def __rtruediv__(self, other: NumericalScalar) -> Expression:
        return self._binary_operation(other, operator.truediv, reverse=True)

    def __pow__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.pow)

    def __rpow__(self, other: NumericalScalar) -> Expression:
        return self._binary_operation(other, operator.pow, reverse=True)

    def __floordiv__(self, other: ScalarData) -> Expression:
        return floor(self / other)

    def __rfloordiv__(self, other: ScalarData) -> Expression:
        return floor(other / self)

    def __mod__(self, other: ScalarData) -> Expression:
        return fmod(self.casadi_sx, other)

    def __rmod__(self, other: ScalarData) -> Expression:
        return fmod(other, self.casadi_sx)

    def __divmod__(self, other: ScalarData) -> Tuple[Expression, Expression]:
        return self // other, self % other

    def __rdivmod__(self, other: ScalarData) -> Tuple[Expression, Expression]:
        return other // self, other % self

    # %% logical operators

    def __invert__(self) -> Expression:
        return logic_not(self.casadi_sx)

    def __eq__(self, other: ScalarData) -> Expression:
        if isinstance(other, SymbolicType):
            other = other.casadi_sx
        return Expression(self.casadi_sx.__eq__(other))

    def __ne__(self, other):
        if isinstance(other, SymbolicType):
            other = other.casadi_sx
        return Expression(self.casadi_sx.__ne__(other))

    def __or__(self, other: ScalarData) -> Expression:
        return logic_or(self.casadi_sx, other)

    def __and__(self, other: ScalarData) -> Expression:
        return logic_and(self.casadi_sx, other)

    def __lt__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.lt)

    def __le__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.le)

    def __gt__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.gt)

    def __ge__(self, other: ScalarData) -> Expression:
        return self._binary_operation(other, operator.ge)

    def safe_division(
        self,
        other: ScalarData,
        if_nan: Optional[ScalarData] = None,
    ) -> Expression:
        """
        A version of division where no sub-expression is ever NaN. The expression would evaluate to 'if_nan', but
        you should probably never work with the 'if_nan' result. However, if one sub-expressions is NaN, the whole expression
        evaluates to NaN, even if it is only in a branch of an if-else, that is not returned.
        This method is a workaround for such cases.
        """
        other = Expression(data=other)
        if if_nan is None:
            if_nan = 0
        if_nan = Expression(data=if_nan)
        save_denominator = if_eq_zero(
            condition=other, if_result=Expression(data=1), else_result=other
        )
        return if_eq_zero(other, if_result=if_nan, else_result=self / save_denominator)


class VectorOperationsMixin:
    casadi_sx: ca.SX
    """
    Reference to the casadi data structure of type casadi.SX
    """

    def euclidean_distance(self, other: Self) -> Expression:
        difference = self - other
        distance = difference.norm()
        return distance


class MatrixOperationsMixin:
    casadi_sx: ca.SX
    """
    Reference to the casadi data structure of type casadi.SX
    """
    shape: Tuple[int, int]

    def sum(self) -> Expression:
        """
        the equivalent to np.sum(matrix)
        """
        return Expression(ca.sum1(ca.sum2(self.casadi_sx)))

    def sum_row(self) -> Expression:
        """
        the equivalent to np.sum(matrix, axis=0)
        """
        return Expression(ca.sum1(self.casadi_sx))

    def sum_column(self) -> Expression:
        """
        the equivalent to np.sum(matrix, axis=1)
        """
        return Expression(ca.sum2(self.casadi_sx))

    def trace(self) -> Expression:
        if not self.is_square():
            raise NotSquareMatrixError(actual_dimensions=self.casadi_sx.shape)
        s = 0
        for i in range(self.casadi_sx.shape[0]):
            s += self.casadi_sx[i, i]
        return Expression(s)

    def det(self) -> Expression:
        """
        Calculate the determinant of the given expression.

        This function computes the determinant of the provided mathematical expression.
        The input can be an instance of either `Expression`, `RotationMatrix`, or
        `TransformationMatrix`. The result is returned as an `Expression`.

        :return: An `Expression` representing the determinant of the input.
        """
        if not self.is_square():
            raise NotSquareMatrixError(actual_dimensions=self.casadi_sx.shape)
        return Expression(ca.det(self.casadi_sx))

    def is_square(self):
        return self.casadi_sx.shape[0] == self.casadi_sx.shape[1]

    def entrywise_product(self, other: Expression) -> Expression:
        """
        Computes the entrywise (element-wise) product of two matrices, assuming they have the same dimensions. The
        operation multiplies each corresponding element of the input matrices and stores the result in a new matrix
        of the same shape.

        :param other: The second matrix, represented as an object of type `Expression`, whose shape
                        must match the shape of `matrix1`.
        :return: A new matrix of type `Expression` containing the entrywise product of `matrix1` and `matrix2`.
        """
        assert self.shape == other.shape
        result = Expression.zeros(*self.shape)
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                result[i, j] = self[i, j] * other[i, j]
        return result


@dataclass(eq=False)
class Symbol(SymbolicType, BasicOperatorMixin):
    """
    A symbolic expression, which should be only a single symbols.
    No matrix and no numbers.
    """

    name: str = field(kw_only=True)

    casadi_sx: ca.SX = field(kw_only=True, init=False, default=None)

    _registry: ClassVar[Dict[str, Symbol]] = {}
    """
    To avoid two symbols with the same name, references to existing symbols are stored on a class level.
    """

    def __new__(cls, name: str):
        """
        Multiton design pattern prevents two symbol instances with the same name.
        """
        if name in cls._registry:
            return cls._registry[name]
        instance = super().__new__(cls)
        instance.casadi_sx = ca.SX.sym(name)
        instance.name = name
        cls._registry[name] = instance
        return instance

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Symbol({self})"

    def __hash__(self):
        return hash(self.name)


@dataclass(eq=False)
class Expression(
    SymbolicType, BasicOperatorMixin, VectorOperationsMixin, MatrixOperationsMixin
):
    """
    Represents symbolic expressions with rich mathematical capabilities, including matrix
    operations, derivatives, and manipulation of symbolic representations.

    This class is designed to encapsulate symbolic mathematical expressions and provide a wide
    range of features for computations, including matrix constructions (zeros, ones, identity),
    derivative computations (Jacobian, total derivatives, Hessian), reshaping, and scaling.
    It is essential to symbolic computation workflows in applications that require gradient
    analysis, second-order derivatives, or other advanced mathematical operations. The class
    leverages symbolic computation libraries for handling low-level symbolic details efficiently.
    """

    casadi_sx: ca.SX = field(kw_only=True, default_factory=lambda: ca.SX())

    data: InitVar[
        Optional[
            Union[
                SymbolicData,
                NumericalScalar,
                NumericalArray,
                Numerical2dMatrix,
                Iterable[Symbol],
                Iterable[Expression],
            ]
        ]
    ] = None

    def __post_init__(
        self,
        data: Optional[
            Union[
                ca.SX,
                SymbolicData,
                NumericalScalar,
                NumericalArray,
                Numerical2dMatrix,
                Iterable[Symbol],
            ]
        ],
    ):
        if data is None:
            return
        if isinstance(data, ca.SX):
            self.casadi_sx = data
        elif isinstance(data, SymbolicType):
            self.casadi_sx = data.casadi_sx
        elif isinstance(data, Iterable):
            self._from_iterable(data)
        else:
            self.casadi_sx = ca.SX(data)

    def _from_iterable(
        self, data: Union[NumericalArray, Numerical2dMatrix, Iterable[Symbol]]
    ):
        x = len(data)
        if x == 0:
            self.casadi_sx = ca.SX()
            return
        if (
            isinstance(data[0], list)
            or isinstance(data[0], tuple)
            or isinstance(data[0], np.ndarray)
        ):
            y = len(data[0])
        else:
            y = 1
        casadi_sx = ca.SX(x, y)
        for i in range(casadi_sx.shape[0]):
            if y > 1:
                for j in range(casadi_sx.shape[1]):
                    casadi_sx[i, j] = to_sx(data[i][j])
            else:
                casadi_sx[i] = to_sx(data[i])
        self.casadi_sx = casadi_sx

    @classmethod
    def zeros(cls, rows: int, columns: int) -> Expression:
        return cls(casadi_sx=ca.SX.zeros(rows, columns))

    @classmethod
    def ones(cls, x: int, y: int) -> Expression:
        return cls(casadi_sx=ca.SX.ones(x, y))

    @classmethod
    def tri(cls, dimension: int) -> Expression:
        return cls(data=np.tri(dimension))

    @classmethod
    def eye(cls, size: int) -> Expression:
        return cls(casadi_sx=ca.SX.eye(size))

    @classmethod
    def diag(cls, args: Union[List[ScalarData], Expression]) -> Expression:
        return cls(casadi_sx=ca.diag(to_sx(args)))

    @classmethod
    def vstack(
        cls,
        list_of_matrices: List[SymbolicArray],
    ) -> Self:
        if len(list_of_matrices) == 0:
            return cls(data=[])
        return cls(casadi_sx=ca.vertcat(*[to_sx(x) for x in list_of_matrices]))

    @classmethod
    def hstack(
        cls,
        list_of_matrices: Union[List[TransformationMatrix], List[Expression]],
    ) -> Self:
        if len(list_of_matrices) == 0:
            return cls(data=[])
        return cls(casadi_sx=ca.horzcat(*[to_sx(x) for x in list_of_matrices]))

    @classmethod
    def diag_stack(
        cls,
        list_of_matrices: Union[List[TransformationMatrix], List[Expression]],
    ) -> Expression:
        num_rows = int(math.fsum(e.shape[0] for e in list_of_matrices))
        num_columns = int(math.fsum(e.shape[1] for e in list_of_matrices))
        combined_matrix = Expression.zeros(num_rows, num_columns)
        row_counter = 0
        column_counter = 0
        for matrix in list_of_matrices:
            combined_matrix[
                row_counter : row_counter + matrix.shape[0],
                column_counter : column_counter + matrix.shape[1],
            ] = matrix
            row_counter += matrix.shape[0]
            column_counter += matrix.shape[1]
        return combined_matrix

    def remove(self, rows: List[int], columns: List[int]):
        self.casadi_sx.remove(rows, columns)

    def split(self) -> List[Expression]:
        assert self.shape[0] == 1 and self.shape[1] == 1
        parts = [
            Expression(self.casadi_sx.dep(i)) for i in range(self.casadi_sx.n_dep())
        ]
        return parts

    def __copy__(self) -> Expression:
        return Expression(copy(self.casadi_sx))

    def dot(self, other: Expression) -> Expression:
        if isinstance(other, Expression):
            if self.shape[1] == 1 and other.shape[1] == 1:
                return Expression(ca.mtimes(self.T.casadi_sx, other.casadi_sx))
            return Expression(ca.mtimes(self.casadi_sx, other.casadi_sx))
        raise _operation_type_error(self, "dot", other)

    @property
    def T(self) -> Expression:
        return Expression(self.casadi_sx.T)

    def reshape(self, new_shape: Tuple[int, int]) -> Expression:
        return Expression(self.casadi_sx.reshape(new_shape))

    def jacobian(self, symbols: Iterable[Symbol]) -> Expression:
        """
        Compute the Jacobian matrix of a vector of expressions with respect to a vector of symbols.

        This function calculates the Jacobian matrix, which is a matrix of all first-order
        partial derivatives of a vector of functions with respect to a vector of variables.

        :param symbols: The symbols with respect to which the partial derivatives are taken.
        :return: The Jacobian matrix as an Expression.
        """
        return Expression(
            ca.jacobian(self.casadi_sx, Expression(data=symbols).casadi_sx)
        )

    def jacobian_dot(
        self, symbols: Iterable[Symbol], symbols_dot: Iterable[Symbol]
    ) -> Expression:
        """
        Compute the total derivative of the Jacobian matrix.

        This function calculates the time derivative of a Jacobian matrix given
        a set of expressions and symbols, along with their corresponding
        derivatives. For each element in the Jacobian matrix, this method
        computes the total derivative based on the provided symbols and
        their time derivatives.

        :param symbols: Iterable containing the symbols with respect to which
            the Jacobian is calculated.
        :param symbols_dot: Iterable containing the time derivatives of the
            corresponding symbols in `symbols`.
        :return: The time derivative of the Jacobian matrix.
        """
        Jd = self.jacobian(symbols)
        for i in range(Jd.shape[0]):
            for j in range(Jd.shape[1]):
                Jd[i, j] = Jd[i, j].total_derivative(symbols, symbols_dot)
        return Jd

    def jacobian_ddot(
        self,
        symbols: Iterable[Symbol],
        symbols_dot: Iterable[Symbol],
        symbols_ddot: Iterable[Symbol],
    ) -> Expression:
        """
        Compute the second-order total derivative of the Jacobian matrix.

        This function computes the Jacobian matrix of the given expressions with
        respect to specified symbols and further calculates the second-order
        total derivative for each element in the Jacobian matrix with respect to
        the provided symbols, their first-order derivatives, and their second-order
        derivatives.

        :param symbols: An iterable of symbolic variables representing the
            primary variables with respect to which the Jacobian and derivatives
            are calculated.
        :param symbols_dot: An iterable of symbolic variables representing the
            first-order derivatives of the primary variables.
        :param symbols_ddot: An iterable of symbolic variables representing the
            second-order derivatives of the primary variables.
        :return: A symbolic matrix representing the second-order total derivative
            of the Jacobian matrix of the provided expressions.
        """
        Jdd = self.jacobian(symbols)
        for i in range(Jdd.shape[0]):
            for j in range(Jdd.shape[1]):
                Jdd[i, j] = Jdd[i, j].second_order_total_derivative(
                    symbols, symbols_dot, symbols_ddot
                )
        return Jdd

    def total_derivative(
        self,
        symbols: Iterable[Symbol],
        symbols_dot: Iterable[Symbol],
    ) -> Expression:
        """
        Compute the total derivative of an expression with respect to given symbols and their derivatives
        (dot symbols).

        The total derivative accounts for a dependent relationship where the specified symbols represent
        the variables of interest, and the dot symbols represent the time derivatives of those variables.

        :param symbols: Iterable of symbols with respect to which the derivative is computed.
        :param symbols_dot: Iterable of dot symbols representing the derivatives of the symbols.
        :return: The expression resulting from the total derivative computation.
        """
        symbols = Expression(data=symbols)
        symbols_dot = Expression(data=symbols_dot)
        return Expression(
            ca.jtimes(self.casadi_sx, symbols.casadi_sx, symbols_dot.casadi_sx)
        )

    def second_order_total_derivative(
        self,
        symbols: Iterable[Symbol],
        symbols_dot: Iterable[Symbol],
        symbols_ddot: Iterable[Symbol],
    ) -> Expression:
        """
        Computes the second-order total derivative of an expression with respect to a set of symbols.

        This function takes an expression and computes its second-order total derivative
        using provided symbols, their first-order derivatives, and their second-order
        derivatives. The computation internally constructs a Hessian matrix of the
        expression and multiplies it by a vector that combines the provided derivative
        data.

        :param symbols: Iterable containing the symbols with respect to which the derivative is calculated.
        :param symbols_dot: Iterable containing the first-order derivatives of the symbols.
        :param symbols_ddot: Iterable containing the second-order derivatives of the symbols.
        :return: The computed second-order total derivative, returned as an `Expression`.
        """
        symbols = Expression(data=symbols)
        symbols_dot = Expression(data=symbols_dot)
        symbols_ddot = Expression(data=symbols_ddot)
        v = []
        for i in range(len(symbols)):
            for j in range(len(symbols)):
                if i == j:
                    v.append(symbols_ddot[i].casadi_sx)
                else:
                    v.append(symbols_dot[i].casadi_sx * symbols_dot[j].casadi_sx)
        v = Expression(data=v)
        H = Expression(ca.hessian(self.casadi_sx, symbols.casadi_sx)[0])
        H = H.reshape((1, len(H) ** 2))
        return H.dot(v)

    def hessian(self, symbols: Iterable[Symbol]) -> Expression:
        """
        Calculate the Hessian matrix of a given expression with respect to specified symbols.

        The function computes the second-order partial derivatives (Hessian matrix) for a
        provided mathematical expression using the specified symbols. It utilizes a symbolic
        library for the internal operations to generate the Hessian.

        :param symbols: An iterable containing the symbols with respect to which the derivatives
            are calculated.
        :return: The resulting Hessian matrix as an expression.
        """
        expressions = self.casadi_sx
        return Expression(
            ca.hessian(expressions, Expression(data=symbols).casadi_sx)[0]
        )

    def inverse(self) -> Expression:
        """
        Computes the matrix inverse. Only works if the expression is square.
        """
        assert self.shape[0] == self.shape[1]
        return Expression(ca.inv(self.casadi_sx))

    def scale(self, a: ScalarData) -> Expression:
        return self.safe_division(self.norm()) * a

    def kron(self, other: Expression) -> Expression:
        """
        Compute the Kronecker product of two given matrices.

        The Kronecker product is a block matrix construction, derived from the
        direct product of two matrices. It combines the entries of the first
        matrix (`m1`) with each entry of the second matrix (`m2`) by a rule
        of scalar multiplication. This operation extends to any two matrices
        of compatible shapes.

        :param other: The second matrix to be used in calculating the Kronecker product.
                   Supports symbolic or numerical matrix types.
        :return: An Expression representing the resulting Kronecker product as a
                 symbolic or numerical matrix of appropriate size.
        """
        m1 = to_sx(self)
        m2 = to_sx(other)
        return Expression(ca.kron(m1, m2))


def create_symbols(names: Union[List[str], int]) -> List[Symbol]:
    """
    Generates a list of symbolic objects based on the input names or an integer value.

    This function takes either a list of names or an integer. If an integer is
    provided, it generates symbolic objects with default names in the format
    `s_<index>` for numbers up to the given integer. If a list of names is
    provided, it generates symbolic objects for each name in the list.

    :param names: A list of strings representing names of symbols or an integer
        specifying the number of symbols to generate.
    :return: A list of symbolic objects created based on the input.
    """
    if isinstance(names, int):
        names = [f"s_{i}" for i in range(names)]
    return [Symbol(name=x) for x in names]


def diag(args: Union[List[ScalarData], Expression]) -> Expression:
    return Expression.diag(args)


def vstack(args: Union[List[Expression], Expression]) -> Expression:
    return Expression.vstack(args)


def hstack(args: Union[List[Expression], Expression]) -> Expression:
    return Expression.hstack(args)


def diag_stack(args: Union[List[Expression], Expression]) -> Expression:
    return Expression.diag_stack(args)


def abs(x: SymbolicType) -> Expression:
    x_sx = to_sx(x)
    result = ca.fabs(x_sx)
    return Expression(result)


def max(x: ScalarData, y: ScalarData) -> Expression:
    x = to_sx(x)
    y = to_sx(y)
    return Expression(ca.fmax(x, y))


def min(x: ScalarData, y: ScalarData) -> Expression:
    x = to_sx(x)
    y = to_sx(y)
    return Expression(ca.fmin(x, y))


def limit(
    x: ScalarData, lower_limit: ScalarData, upper_limit: ScalarData
) -> Expression:
    return Expression(data=max(lower_limit, min(upper_limit, x)))


def to_sx(thing: Union[ca.SX, SymbolicType]) -> ca.SX:
    if isinstance(thing, SymbolicType):
        return thing.casadi_sx
    if isinstance(thing, ca.SX):
        return thing
    return ca.SX(thing)


def dot(e1: Expression, e2: Expression) -> Expression:
    return e1.dot(e2)


def fmod(a: ScalarData, b: ScalarData) -> Expression:
    a = to_sx(a)
    b = to_sx(b)
    return Expression(ca.fmod(a, b))


def normalize_angle_positive(angle: ScalarData) -> Expression:
    """
    Normalizes the angle to be 0 to 2*pi
    It takes and returns radians.
    """
    return fmod(fmod(angle, 2.0 * ca.pi) + 2.0 * ca.pi, 2.0 * ca.pi)


def normalize_angle(angle: ScalarData) -> Expression:
    """
    Normalizes the angle to be -pi to +pi
    It takes and returns radians.
    """
    a = normalize_angle_positive(angle)
    return if_greater(a, ca.pi, a - 2.0 * ca.pi, a)


def shortest_angular_distance(
    from_angle: ScalarData, to_angle: ScalarData
) -> Expression:
    """
    Given 2 angles, this returns the shortest angular
    difference.  The inputs and outputs are of course radians.

    The result would always be -pi <= result <= pi. Adding the result
    to "from" will always get you an equivalent angle to "to".
    """
    return normalize_angle(to_angle - from_angle)


def safe_acos(angle: ScalarData) -> Expression:
    """
    Limits the angle between -1 and 1 to avoid acos becoming NaN.
    """
    angle = limit(angle, -1, 1)
    return acos(angle)


def floor(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.floor(x))


def ceil(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.ceil(x))


def sign(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.sign(x))


def cos(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.cos(x))


def sin(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.sin(x))


def exp(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.exp(x))


def log(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.log(x))


def tan(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.tan(x))


def cosh(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.cosh(x))


def sinh(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.sinh(x))


def sqrt(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.sqrt(x))


def acos(x: ScalarData) -> Expression:
    x = to_sx(x)
    return Expression(ca.acos(x))


def atan2(x: ScalarData, y: ScalarData) -> Expression:
    x = to_sx(x)
    y = to_sx(y)
    return Expression(ca.atan2(x, y))


def solve_for(
    expression: Expression,
    target_value: float,
    start_value: float = 0.0001,
    max_tries: int = 10000,
    eps: float = 1e-10,
    max_step: float = 1,
) -> float:
    """
    Solves for a value `x` such that the given mathematical expression, when evaluated at `x`,
    is approximately equal to the target value. The solver iteratively adjusts the value of `x`
    using a numerical approach based on the derivative of the expression.

    :param expression: The mathematical expression to solve. It is assumed to be differentiable.
    :param target_value: The value that the expression is expected to approximate.
    :param start_value: The initial guess for the iterative solver. Defaults to 0.0001.
    :param max_tries: The maximum number of iterations the solver will perform. Defaults to 10000.
    :param eps: The maximum tolerated absolute error for the solution. If the difference
        between the computed value and the target value is less than `eps`, the solution is considered valid. Defaults to 1e-10.
    :param max_step: The maximum adjustment to the value of `x` at each iteration step. Defaults to 1.
    :return: The estimated value of `x` that solves the equation for the given expression and target value.
    :raises ValueError: If no solution is found within the allowed number of steps or if convergence criteria are not met.
    """
    f_dx = expression.jacobian(expression.free_symbols()).compile()
    f = expression.compile()
    x = start_value
    for tries in range(max_tries):
        err = f(np.array([x]))[0] - target_value
        if builtins.abs(err) < eps:
            return x
        slope = f_dx(np.array([x]))[0]
        if slope == 0:
            if start_value > 0:
                slope = -0.001
            else:
                slope = 0.001
        x -= builtins.max(builtins.min(err / slope, max_step), -max_step)
    raise ValueError("no solution found")


def gauss(n: ScalarData) -> Expression:
    """
    Calculate the sum of the first `n` natural numbers using the Gauss formula.

    This function computes the sum of an arithmetic series where the first term
    is 1, the last term is `n`, and the total count of the terms is `n`. The
    result is derived from the formula `(n * (n + 1)) / 2`, which simplifies
    to `(n ** 2 + n) / 2`.

    :param n: The upper limit of the sum, representing the last natural number
              of the series to include.
    :return: The sum of the first `n` natural numbers.
    """
    return (n**2 + n) / 2


# %% binary logic
BinaryTrue = Expression(data=True)
BinaryFalse = Expression(data=False)


def is_false_symbol(expression: Expression) -> bool:
    try:
        return bool((expression == BinaryFalse).to_np())
    except Exception as e:
        return False


def logic_and(*args: ScalarData) -> ScalarData:
    assert len(args) >= 2, "and must be called with at least 2 arguments"
    # if there is any False, return False
    if [x for x in args if is_false_symbol(x)]:
        return BinaryFalse
    # filter all True
    args = [x for x in args if not is_true_symbol(x)]
    if len(args) == 0:
        return BinaryTrue
    if len(args) == 1:
        return args[0]
    if len(args) == 2:
        cas_a = to_sx(args[0])
        cas_b = to_sx(args[1])
        return Expression(ca.logic_and(cas_a, cas_b))
    else:
        return Expression(
            ca.logic_and(args[0].casadi_sx, logic_and(*args[1:]).casadi_sx)
        )


def logic_not(expression: ScalarData) -> Expression:
    cas_expr = to_sx(expression)
    return Expression(ca.logic_not(cas_expr))


def logic_any(args: Expression) -> ScalarData:
    return Expression(ca.logic_any(args.casadi_sx))


def logic_all(args: Expression) -> ScalarData:
    return Expression(ca.logic_all(args.casadi_sx))


def logic_or(*args: ScalarData, simplify: bool = True) -> ScalarData:
    assert len(args) >= 2, "and must be called with at least 2 arguments"
    # if there is any True, return True
    if simplify and [x for x in args if is_true_symbol(x)]:
        return BinaryTrue
    # filter all False
    if simplify:
        args = [x for x in args if not is_false_symbol(x)]
    if len(args) == 0:
        return BinaryFalse
    if len(args) == 1:
        return args[0]
    if len(args) == 2:
        return Expression(ca.logic_or(to_sx(args[0]), to_sx(args[1])))
    else:
        return Expression(
            ca.logic_or(to_sx(args[0]), to_sx(logic_or(*args[1:], False)))
        )


def is_true_symbol(expression: Expression) -> bool:
    try:
        equality_expr = expression == BinaryTrue
        return bool(equality_expr.to_np())
    except Exception as e:
        return False


# %% trinary logic
TrinaryFalse: Expression = Expression(data=0.0)
TrinaryUnknown: Expression = Expression(data=0.5)
TrinaryTrue: Expression = Expression(data=1.0)


def trinary_logic_not(expression: ScalarData) -> Expression:
    return Expression(data=1 - expression)


def trinary_logic_and(*args: ScalarData) -> ScalarData:
    assert len(args) >= 2, "and must be called with at least 2 arguments"
    # if there is any False, return False
    if [x for x in args if is_false_symbol(x)]:
        return TrinaryFalse
    # filter all True
    args = [x for x in args if not is_true_symbol(x)]
    if len(args) == 0:
        return TrinaryTrue
    if len(args) == 1:
        return args[0]
    if len(args) == 2:
        cas_a = to_sx(args[0])
        cas_b = to_sx(args[1])
        return min(cas_a, cas_b)
    else:
        return trinary_logic_and(args[0], trinary_logic_and(*args[1:]))


def trinary_logic_or(a: ScalarData, b: ScalarData) -> ScalarData:
    cas_a = to_sx(a)
    cas_b = to_sx(b)
    return max(cas_a, cas_b)


def is_trinary_true(expression: Union[Symbol, Expression]) -> Expression:
    return expression == TrinaryTrue


def is_trinary_true_symbol(expression: Expression) -> bool:
    try:
        return bool((expression == TrinaryTrue).to_np())
    except Exception as e:
        return False


def is_trinary_false(expression: Union[Symbol, Expression]) -> Expression:
    return expression == TrinaryFalse


def is_trinary_false_symbol(expression: Expression) -> bool:
    try:
        return bool((expression == TrinaryFalse).to_np())
    except Exception as e:
        return False


def is_trinary_unknown(expression: Union[Symbol, Expression]) -> Expression:
    return expression == TrinaryUnknown


def is_trinary_unknown_symbol(expression: Expression) -> bool:
    try:
        return bool((expression == TrinaryUnknown).to_np())
    except Exception as e:
        return False


def replace_with_trinary_logic(expression: Expression) -> Expression:
    """
    Converts a given logical expression into a three-valued logic expression.

    This function recursively processes a logical expression and replaces it
    with its three-valued logic equivalent. The three-valued logic can represent
    true, false, or an indeterminate state. The method identifies specific
    operations like NOT, AND, and OR and applies three-valued logic rules to them.

    :param expression: The logical expression to be converted.
    :return: The converted logical expression in three-valued logic.
    """
    cas_expr = to_sx(expression)
    if cas_expr.n_dep() == 0:
        if is_true_symbol(cas_expr):
            return TrinaryTrue
        if is_false_symbol(cas_expr):
            return TrinaryFalse
        return expression
    op = cas_expr.op()
    if op == ca.OP_NOT:
        return trinary_logic_not(replace_with_trinary_logic(cas_expr.dep(0)))
    if op == ca.OP_AND:
        return trinary_logic_and(
            replace_with_trinary_logic(cas_expr.dep(0)),
            replace_with_trinary_logic(cas_expr.dep(1)),
        )
    if op == ca.OP_OR:
        return trinary_logic_or(
            replace_with_trinary_logic(cas_expr.dep(0)),
            replace_with_trinary_logic(cas_expr.dep(1)),
        )
    return expression


# %% ifs
def _get_return_type(thing: Any):
    """
    Determines the return type based on the input's type and returns the appropriate type.
    Used in "if" expressions.

    :param thing: The input whose type is analyzed.
    :return: The appropriate type based on the input type. If the input type is `int`, `float`, or `Symbol`,
        the return type is `Expression`. Otherwise, the return type is the input's type.
    """
    return_type = type(thing)
    if return_type in (int, float, Symbol):
        return Expression
    return return_type


def _recreate_return_type(thing: Any, return_type: Type) -> Any:
    """
    Transforms the input object into the specified return type. Supports specialized
    conversion for specific types like Point3, Vector3, and Quaternion. For these types,
    it initializes the object using the `from_iterable` method. For other types,
    a standard initialization is used.

    Used in conjunction with `_get_return_type` in "if" expressions.

    :param thing: An object that will be converted to the specified return type.
    :param return_type: The type to which the input object will be converted.
        If the type is Point3, Vector3, or Quaternion, the conversion will be
        performed using `from_iterable`. Otherwise, the type's standard
        constructor will be used.
    :return: An object of the specified return type, initialized using the input object.
    """
    if return_type in (Point3, Vector3, Quaternion):
        return return_type.from_iterable(thing)
    return return_type(thing)


def if_else(
    condition: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if condition:
        return if_result
    else:
        return else_result
    """
    condition = to_sx(condition)
    if isinstance(if_result, NumericalScalar):
        if_result = Expression(data=if_result)
    if isinstance(else_result, NumericalScalar):
        else_result = Expression(data=else_result)
    if isinstance(
        if_result, (Point3, Vector3, TransformationMatrix, RotationMatrix, Quaternion)
    ):
        assert type(if_result) == type(
            else_result
        ), f"if_else: result types are not equal {type(if_result)} != {type(else_result)}"
    return_type = _get_return_type(if_result)
    if_result = to_sx(if_result)
    else_result = to_sx(else_result)
    return _recreate_return_type(
        ca.if_else(condition, if_result, else_result), return_type
    )


def if_greater(
    a: ScalarData,
    b: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if a > b:
        return if_result
    else:
        return else_result
    """
    a = to_sx(a)
    b = to_sx(b)
    return if_else(ca.gt(a, b), if_result, else_result)


def if_less(
    a: ScalarData,
    b: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if a < b:
        return if_result
    else:
        return else_result
    """
    a = to_sx(a)
    b = to_sx(b)
    return if_else(ca.lt(a, b), if_result, else_result)


def if_greater_zero(
    condition: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if condition > 0:
        return if_result
    else:
        return else_result
    """
    condition = to_sx(condition)
    return if_else(ca.gt(condition, 0), if_result, else_result)


def if_greater_eq_zero(
    condition: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if condition >= 0:
        return if_result
    else:
        return else_result
    """
    return if_greater_eq(condition, 0, if_result, else_result)


def if_greater_eq(
    a: ScalarData,
    b: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if a >= b:
        return if_result
    else:
        return else_result
    """
    a = to_sx(a)
    b = to_sx(b)
    return if_else(ca.ge(a, b), if_result, else_result)


def if_less_eq(
    a: ScalarData,
    b: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if a <= b:
        return if_result
    else:
        return else_result
    """
    return if_greater_eq(b, a, if_result, else_result)


def if_eq_zero(
    condition: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if condition == 0:
        return if_result
    else:
        return else_result
    """
    return if_else(condition, else_result, if_result)


def if_eq(
    a: ScalarData,
    b: ScalarData,
    if_result: GenericSymbolicType,
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    Creates an expression that represents:
    if a == b:
        return if_result
    else:
        return else_result
    """
    a = to_sx(a)
    b = to_sx(b)
    return if_else(ca.eq(a, b), if_result, else_result)


def if_eq_cases(
    a: ScalarData,
    b_result_cases: Iterable[Tuple[ScalarData, GenericSymbolicType]],
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    if a == b_result_cases[0][0]:
        return b_result_cases[0][1]
    elif a == b_result_cases[1][0]:
        return b_result_cases[1][1]
    ...
    else:
        return else_result
    """
    return_type = _get_return_type(else_result)
    a = to_sx(a)
    result = to_sx(else_result)
    for b, b_result in b_result_cases:
        b = to_sx(b)
        b_result = to_sx(b_result)
        result = ca.if_else(ca.eq(a, b), b_result, result)
    return _recreate_return_type(result, return_type)


def if_cases(
    cases: Sequence[Tuple[ScalarData, GenericSymbolicType]],
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    if cases[0][0]:
        return cases[0][1]
    elif cases[1][0]:
        return cases[1][1]
    ...
    else:
        return else_result
    """
    return_type = _get_return_type(else_result)
    else_result = to_sx(else_result)
    result = to_sx(else_result)
    for i in reversed(range(len(cases))):
        case = to_sx(cases[i][0])
        case_result = to_sx(cases[i][1])
        result = ca.if_else(case, case_result, result)
    return _recreate_return_type(result, return_type)


def if_less_eq_cases(
    a: ScalarData,
    b_result_cases: Sequence[Tuple[ScalarData, GenericSymbolicType]],
    else_result: GenericSymbolicType,
) -> GenericSymbolicType:
    """
    This only works if b_result_cases is sorted in ascending order.
    if a <= b_result_cases[0][0]:
        return b_result_cases[0][1]
    elif a <= b_result_cases[1][0]:
        return b_result_cases[1][1]
    ...
    else:
        return else_result
    """
    return_type = _get_return_type(else_result)
    a = to_sx(a)
    result = to_sx(else_result)
    for i in reversed(range(len(b_result_cases))):
        b = to_sx(b_result_cases[i][0])
        b_result = to_sx(b_result_cases[i][1])
        result = ca.if_else(ca.le(a, b), b_result, result)
    return _recreate_return_type(result, return_type)


# %% spatial types


@dataclass(eq=False)
class ReferenceFrameMixin:
    """
    Provides functionality to associate a reference frame with an object.

    This mixin class allows the inclusion of a reference frame within objects that
    require spatial or kinematic context. The reference frame is represented by a
    `KinematicStructureEntity`, which provides the necessary structural and spatial
    information.

    """

    reference_frame: Optional[KinematicStructureEntity | Connection] = field(
        kw_only=True, default=None
    )
    """
    The reference frame associated with the object. Can be None if no reference frame is required or applicable.
    """


@dataclass(eq=False)
class TransformationMatrix(SymbolicType, ReferenceFrameMixin, MatrixOperationsMixin):
    """
    Represents a 4x4 transformation matrix used in kinematics and transformations.

    A `TransformationMatrix` encapsulates relationships between a parent coordinate
    system (reference frame) and a child coordinate system through rotation and
    translation. It provides utilities to derive transformations, compute dot
    products, and create transformations from various inputs such as Euler angles or
    quaternions.
    """

    child_frame: Optional[KinematicStructureEntity] = field(kw_only=True, default=None)
    """
    child_frame of this transformation matrix.
    """

    data: InitVar[Optional[Matrix2dData]] = None
    """
    A 4x4 matrix of some form that represents the rotation matrix.
    """

    sanity_check: InitVar[bool] = field(kw_only=True, default=True)
    """
    Whether to perform a sanity check on the matrix data. Can be skipped for performance reasons.
    """

    casadi_sx: ca.SX = field(kw_only=True, default_factory=lambda: ca.SX.eye(4))

    def __post_init__(self, data: Optional[Matrix2dData], sanity_check: bool):
        if data is None:
            return
        self.casadi_sx = copy(Expression(data=data).casadi_sx)
        if sanity_check:
            self._validate()

    def _validate(self):
        if self.shape[0] != 4 or self.shape[1] != 4:
            raise WrongDimensionsError(
                expected_dimensions=(4, 4), actual_dimensions=self.shape
            )
        self[3, 0] = 0.0
        self[3, 1] = 0.0
        self[3, 2] = 0.0
        self[3, 3] = 1.0

    @classmethod
    def from_point_rotation_matrix(
        cls,
        point: Optional[Point3] = None,
        rotation_matrix: Optional[RotationMatrix] = None,
        reference_frame: Optional[KinematicStructureEntity] = None,
        child_frame: Optional[KinematicStructureEntity] = None,
    ) -> TransformationMatrix:
        """
        Constructs a TransformationMatrix object from a given point, a rotation matrix,
        a reference frame, and a child frame.

        :param point: The 3D point used to set the translation part of the
            transformation matrix. If None, no translation is applied.
        :param rotation_matrix: The rotation matrix defines the rotational component
            of the transformation. If None, the identity matrix is assumed.
        :param reference_frame: The reference frame for the transformation matrix.
            It specifies the parent coordinate system.
        :param child_frame: The child or target frame for the transformation. It
            specifies the target coordinate system.
        :return: A `TransformationMatrix` instance initialized with the provided
            parameters or default values.
        """
        if reference_frame is None:
            reference_frame = cls._ensure_consistent_frame([point, rotation_matrix])

        if rotation_matrix is None:
            a_T_b = cls(reference_frame=reference_frame, child_frame=child_frame)
        else:
            a_T_b = cls(
                data=rotation_matrix,
                reference_frame=reference_frame,
                child_frame=child_frame,
                sanity_check=False,
            )
        if point is not None:
            a_T_b[0, 3] = point.x
            a_T_b[1, 3] = point.y
            a_T_b[2, 3] = point.z
        return a_T_b

    @staticmethod
    def _ensure_consistent_frame(
        spatial_objects: List[Optional[ReferenceFrameMixin]],
    ) -> Optional[KinematicStructureEntity]:
        """
        Ensures that all provided spatial objects have a consistent reference frame. If a mismatch
        in the reference frames is detected among the non-null spatial objects, an exception is
        raised. If the list contains only null objects, None is returned.

        This method is primarily used to validate the reference frames of spatial objects before
        proceeding with further operations.

        :param spatial_objects: A list containing zero or more spatial objects, which can either
            be instances of ReferenceFrameMixin or None.
        :return: The common reference frame of the spatial objects if consistent, or None if no
            valid reference frame exists.

        :raises SpatialTypesError: Raised when the reference frames of provided input spatial
            objects are inconsistent.
        """
        reference_frame = None
        for spatial_object in spatial_objects:
            if (
                spatial_object is not None
                and spatial_object.reference_frame is not None
            ):
                if reference_frame is None:
                    reference_frame = spatial_object.reference_frame
                    continue
                if reference_frame != spatial_object.reference_frame:
                    raise SpatialTypesError(
                        f"Reference frames of input parameters don't match ({reference_frame} != {spatial_object.reference_frame})."
                    )
        return reference_frame

    @classmethod
    def from_xyz_rpy(
        cls,
        x: ScalarData = 0,
        y: ScalarData = 0,
        z: ScalarData = 0,
        roll: ScalarData = 0,
        pitch: ScalarData = 0,
        yaw: ScalarData = 0,
        reference_frame: Optional[KinematicStructureEntity] = None,
        child_frame: Optional[KinematicStructureEntity] = None,
    ) -> TransformationMatrix:
        """
        Creates a TransformationMatrix object from position (x, y, z) and Euler angles
        (roll, pitch, yaw) values. The function also accepts optional reference and
        child frame parameters.

        :param x: The x-coordinate of the position
        :param y: The y-coordinate of the position
        :param z: The z-coordinate of the position
        :param roll: The rotation around the x-axis
        :param pitch: The rotation around the y-axis
        :param yaw: The rotation around the z-axis
        :param reference_frame: The reference frame for the transformation
        :param child_frame: The child frame associated with the transformation
        :return: A TransformationMatrix object created using the provided
            position and orientation values
        """
        p = Point3(x_init=x, y_init=y, z_init=z)
        r = RotationMatrix.from_rpy(roll, pitch, yaw)
        return cls.from_point_rotation_matrix(
            p, r, reference_frame=reference_frame, child_frame=child_frame
        )

    @classmethod
    def from_xyz_quaternion(
        cls,
        pos_x: ScalarData = 0,
        pos_y: ScalarData = 0,
        pos_z: ScalarData = 0,
        quat_x: ScalarData = 0,
        quat_y: ScalarData = 0,
        quat_z: ScalarData = 0,
        quat_w: ScalarData = 1,
        reference_frame: Optional[KinematicStructureEntity] = None,
        child_frame: Optional[KinematicStructureEntity] = None,
    ) -> TransformationMatrix:
        """
        Creates a `TransformationMatrix` instance from the provided position coordinates and quaternion
        values representing rotation. This method constructs a 3D point for the position and a rotation
        matrix derived from the quaternion, and initializes the transformation matrix with these along
        with optional reference and child frame entities.

        :param pos_x: X coordinate of the position in space.
        :param pos_y: Y coordinate of the position in space.
        :param pos_z: Z coordinate of the position in space.
        :param quat_w: W component of the quaternion representing rotation.
        :param quat_x: X component of the quaternion representing rotation.
        :param quat_y: Y component of the quaternion representing rotation.
        :param quat_z: Z component of the quaternion representing rotation.
        :param reference_frame: Optional reference frame for the transformation matrix.
        :param child_frame: Optional child frame for the transformation matrix.
        :return: A `TransformationMatrix` object constructed from the given parameters.
        """
        p = Point3(x_init=pos_x, y_init=pos_y, z_init=pos_z)
        r = RotationMatrix.from_quaternion(
            q=Quaternion(w_init=quat_w, x_init=quat_x, y_init=quat_y, z_init=quat_z)
        )
        return cls.from_point_rotation_matrix(
            p, r, reference_frame=reference_frame, child_frame=child_frame
        )

    @classmethod
    def from_xyz_axis_angle(
        cls,
        x: ScalarData = 0,
        y: ScalarData = 0,
        z: ScalarData = 0,
        axis: Vector3 | NumericalArray = None,
        angle: ScalarData = 0,
        reference_frame: Optional[KinematicStructureEntity] = None,
        child_frame: Optional[KinematicStructureEntity] = None,
    ) -> Self:
        """
        Creates an instance of the class from x, y, z coordinates, axis and angle.

        This class method generates an object using provided spatial coordinates and a
        rotation defined by an axis and angle. The resulting object is defined with
        a specified reference frame and child frame.

        :param x: Initial x-coordinate.
        :param y: Initial y-coordinate.
        :param z: Initial z-coordinate.
        :param axis: Vector defining the axis of rotation. Defaults to Vector3(0, 0, 1) if not specified.
        :param angle: Angle of rotation around the specified axis, in radians.
        :param reference_frame: Reference frame entity to be associated with the object.
        :param child_frame: Child frame entity associated with the object.
        :return: An instance of the class with the specified transformations applied.
        """
        axis = axis or Vector3(0, 0, 1)
        rotation_matrix = RotationMatrix.from_axis_angle(axis=axis, angle=angle)
        point = Point3(x_init=x, y_init=y, z_init=z)
        return cls.from_point_rotation_matrix(
            point=point,
            rotation_matrix=rotation_matrix,
            reference_frame=reference_frame,
            child_frame=child_frame,
        )

    @property
    def x(self) -> Expression:
        return self[0, 3]

    @x.setter
    def x(self, value: ScalarData):
        self[0, 3] = value

    @property
    def y(self) -> Expression:
        return self[1, 3]

    @y.setter
    def y(self, value: ScalarData):
        self[1, 3] = value

    @property
    def z(self) -> Expression:
        return self[2, 3]

    @z.setter
    def z(self, value: ScalarData):
        self[2, 3] = value

    def dot(
        self, other: GenericHomogeneousSpatialType
    ) -> GenericHomogeneousSpatialType:
        if isinstance(other, (Vector3, Point3, RotationMatrix, TransformationMatrix)):
            result = ca.mtimes(self.casadi_sx, other.casadi_sx)
            if isinstance(other, Vector3):
                result = Vector3.from_iterable(
                    result, reference_frame=self.reference_frame
                )
                return result
            if isinstance(other, Point3):
                result = Point3.from_iterable(
                    result, reference_frame=self.reference_frame
                )
                return result
            if isinstance(other, RotationMatrix):
                result = RotationMatrix(
                    data=result,
                    reference_frame=self.reference_frame,
                    sanity_check=False,
                )
                return result
            if isinstance(other, TransformationMatrix):
                result = TransformationMatrix(
                    data=result,
                    reference_frame=self.reference_frame,
                    child_frame=other.child_frame,
                    sanity_check=False,
                )
                return result
        raise _operation_type_error(self, "dot", other)

    def __matmul__(self, other: GenericSpatialType) -> GenericSpatialType:
        return self.dot(other)

    def inverse(self) -> TransformationMatrix:
        inv = TransformationMatrix(
            child_frame=self.reference_frame, reference_frame=self.child_frame
        )
        inv[:3, :3] = self[:3, :3].T
        inv[:3, 3] = (-inv[:3, :3]).dot(self[:3, 3])
        return inv

    def to_position(self) -> Point3:
        result = Point3.from_iterable(
            self[:4, 3:], reference_frame=self.reference_frame
        )
        return result

    def to_translation(self) -> TransformationMatrix:
        """
        :return: sets the rotation part of a frame to identity
        """
        r = TransformationMatrix()
        r[0, 3] = self[0, 3]
        r[1, 3] = self[1, 3]
        r[2, 3] = self[2, 3]
        return TransformationMatrix(
            data=r, reference_frame=self.reference_frame, child_frame=None
        )

    def to_rotation_matrix(self) -> RotationMatrix:
        return RotationMatrix(data=self, reference_frame=self.reference_frame)

    def to_quaternion(self) -> Quaternion:
        return Quaternion.from_rotation_matrix(self)

    def __deepcopy__(self, memo) -> TransformationMatrix:
        """
        Even in a deep copy, we don't want to copy the reference and child frame, just the matrix itself,
        because are just references to kinematic structure entities.
        """
        if id(self) in memo:
            return memo[id(self)]
        return TransformationMatrix(
            data=deepcopy(self.casadi_sx),
            reference_frame=self.reference_frame,
            child_frame=self.child_frame,
        )


@dataclass(eq=False)
class RotationMatrix(SymbolicType, ReferenceFrameMixin, MatrixOperationsMixin):
    """
    Class to represent a 4x4 symbolic rotation matrix tied to kinematic references.

    This class provides methods for creating and manipulating rotation matrices within the context
    of kinematic structures. It supports initialization using data such as quaternions, axis-angle,
    other matrices, or directly through vector definitions. The primary purpose is to facilitate
    rotational transformations and computations in a symbolic context, particularly for applications
    like robotic kinematics or mechanical engineering.
    """

    data: InitVar[Optional[Matrix2dData]] = None
    """
    A 4x4 matrix of some form that represents the rotation matrix.
    """

    sanity_check: InitVar[bool] = field(kw_only=True, default=True)
    """
    Whether to perform a sanity check on the matrix data. Can be skipped for performance reasons.
    """

    casadi_sx: ca.SX = field(kw_only=True, default_factory=lambda: ca.SX.eye(4))

    def __post_init__(self, data: Optional[Matrix2dData], sanity_check: bool):
        if data is None:
            return
        if isinstance(data, (RotationMatrix, TransformationMatrix)):
            self.casadi_sx[:3, :3] = copy(data.casadi_sx)[:3, :3]
            return
        self.casadi_sx = Expression(data=data).casadi_sx
        if sanity_check:
            self._validate()

    def _validate(self):
        if self.shape[0] != 4 or self.shape[1] != 4:
            raise WrongDimensionsError(
                expected_dimensions=(4, 4), actual_dimensions=self.shape
            )
        self[0, 3] = 0
        self[1, 3] = 0
        self[2, 3] = 0
        self[3, 0] = 0
        self[3, 1] = 0
        self[3, 2] = 0
        self[3, 3] = 1

    @classmethod
    def from_axis_angle(
        cls,
        axis: Union[Vector3, NumericalArray],
        angle: ScalarData,
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> RotationMatrix:
        """
        Conversion of unit axis and angle to 4x4 rotation matrix according to:
        https://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToMatrix/index.htm
        """
        # use casadi to prevent a bunch of Expression.__init__.py calls
        axis = to_sx(axis)
        angle = to_sx(angle)
        ct = ca.cos(angle)
        st = ca.sin(angle)
        vt = 1 - ct
        m_vt = axis * vt
        m_st = axis * st
        m_vt_0_ax = (m_vt[0] * axis)[1:]
        m_vt_1_2 = m_vt[1] * axis[2]
        s = ca.SX.eye(4)
        ct__m_vt__axis = ct + m_vt * axis
        s[0, 0] = ct__m_vt__axis[0]
        s[0, 1] = -m_st[2] + m_vt_0_ax[0]
        s[0, 2] = m_st[1] + m_vt_0_ax[1]
        s[1, 0] = m_st[2] + m_vt_0_ax[0]
        s[1, 1] = ct__m_vt__axis[1]
        s[1, 2] = -m_st[0] + m_vt_1_2
        s[2, 0] = -m_st[1] + m_vt_0_ax[1]
        s[2, 1] = m_st[0] + m_vt_1_2
        s[2, 2] = ct__m_vt__axis[2]
        return cls(casadi_sx=s, reference_frame=reference_frame, sanity_check=False)

    @classmethod
    def from_quaternion(cls, q: Quaternion) -> RotationMatrix:
        """
        Unit quaternion to 4x4 rotation matrix according to:
        https://github.com/orocos/orocos_kinematics_dynamics/blob/master/orocos_kdl/src/frames.cpp#L167
        """
        x = q[0]
        y = q[1]
        z = q[2]
        w = q[3]
        x2 = x * x
        y2 = y * y
        z2 = z * z
        w2 = w * w
        return cls(
            data=[
                [
                    w2 + x2 - y2 - z2,
                    2 * x * y - 2 * w * z,
                    2 * x * z + 2 * w * y,
                    0,
                ],
                [
                    2 * x * y + 2 * w * z,
                    w2 - x2 + y2 - z2,
                    2 * y * z - 2 * w * x,
                    0,
                ],
                [
                    2 * x * z - 2 * w * y,
                    2 * y * z + 2 * w * x,
                    w2 - x2 - y2 + z2,
                    0,
                ],
                [0, 0, 0, 1],
            ],
            reference_frame=q.reference_frame,
        )

    def x_vector(self) -> Vector3:
        return Vector3(
            x_init=self[0, 0],
            y_init=self[1, 0],
            z_init=self[2, 0],
            reference_frame=self.reference_frame,
        )

    def y_vector(self) -> Vector3:
        return Vector3(
            x_init=self[0, 1],
            y_init=self[1, 1],
            z_init=self[2, 1],
            reference_frame=self.reference_frame,
        )

    def z_vector(self) -> Vector3:
        return Vector3(
            x_init=self[0, 2],
            y_init=self[1, 2],
            z_init=self[2, 2],
            reference_frame=self.reference_frame,
        )

    def dot(self, other: GenericRotatableSpatialType) -> GenericRotatableSpatialType:
        if isinstance(other, (Vector3, RotationMatrix, TransformationMatrix)):
            result = ca.mtimes(self.casadi_sx, other.casadi_sx)
            if isinstance(other, Vector3):
                result = Vector3.from_iterable(result)
            elif isinstance(other, RotationMatrix):
                result = RotationMatrix(data=result, sanity_check=False)
            elif isinstance(other, TransformationMatrix):
                result = TransformationMatrix(result, sanity_check=False)
            result.reference_frame = self.reference_frame
            return result
        raise _operation_type_error(self, "dot", other)

    def __matmul__(
        self, other: GenericRotatableSpatialType
    ) -> GenericRotatableSpatialType:
        return self.dot(other)

    def to_axis_angle(self) -> Tuple[Vector3, Expression]:
        return self.to_quaternion().to_axis_angle()

    def to_angle(self, hint: Optional[Callable] = None) -> Expression:
        """
        :param hint: A function whose sign of the result will be used to determine if angle should be positive or
                        negative
        :return:
        """
        axis, angle = self.to_axis_angle()
        if hint is not None:
            return normalize_angle(
                if_greater_zero(hint(axis), if_result=angle, else_result=-angle)
            )
        else:
            return angle

    @classmethod
    def from_vectors(
        cls,
        x: Optional[Vector3] = None,
        y: Optional[Vector3] = None,
        z: Optional[Vector3] = None,
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> RotationMatrix:
        """
        Create a rotation matrix from 2 or 3 orthogonal vectors.

        If exactly two of x, y, z must be provided. The third will be computed using the cross product.

        Valid combinations:
        - x and y provided: z = x × y
        - x and z provided: y = z × x
        - y and z provided: x = y × z
        - x, y, and z provided: all three used directly
        """
        if x is None and y is None and z is None:
            raise SpatialTypesError("from_vectors requires at least two vectors")
        if x is not None and y is not None and z is None:
            z = x.cross(y)
        elif x is not None and y is None and z is not None:
            y = z.cross(x)
        elif x is None and y is not None and z is not None:
            x = y.cross(z)
        x.scale(1)
        y.scale(1)
        z.scale(1)
        R = cls(
            data=[
                [x[0], y[0], z[0], 0],
                [x[1], y[1], z[1], 0],
                [x[2], y[2], z[2], 0],
                [0, 0, 0, 1],
            ],
            reference_frame=reference_frame,
        )
        return R

    @classmethod
    def from_rpy(
        cls,
        roll: Optional[ScalarData] = None,
        pitch: Optional[ScalarData] = None,
        yaw: Optional[ScalarData] = None,
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> RotationMatrix:
        """
        Conversion of roll, pitch, yaw to 4x4 rotation matrix according to:
        https://github.com/orocos/orocos_kinematics_dynamics/blob/master/orocos_kdl/src/frames.cpp#L167
        """
        roll = 0 if roll is None else roll
        pitch = 0 if pitch is None else pitch
        yaw = 0 if yaw is None else yaw
        roll = to_sx(roll)
        pitch = to_sx(pitch)
        yaw = to_sx(yaw)

        s = ca.SX.eye(4)

        s[0, 0] = ca.cos(yaw) * ca.cos(pitch)
        s[0, 1] = (ca.cos(yaw) * ca.sin(pitch) * ca.sin(roll)) - (
            ca.sin(yaw) * ca.cos(roll)
        )
        s[0, 2] = (ca.sin(yaw) * ca.sin(roll)) + (
            ca.cos(yaw) * ca.sin(pitch) * ca.cos(roll)
        )
        s[1, 0] = ca.sin(yaw) * ca.cos(pitch)
        s[1, 1] = (ca.cos(yaw) * ca.cos(roll)) + (
            ca.sin(yaw) * ca.sin(pitch) * ca.sin(roll)
        )
        s[1, 2] = (ca.sin(yaw) * ca.sin(pitch) * ca.cos(roll)) - (
            ca.cos(yaw) * ca.sin(roll)
        )
        s[2, 0] = -ca.sin(pitch)
        s[2, 1] = ca.cos(pitch) * ca.sin(roll)
        s[2, 2] = ca.cos(pitch) * ca.cos(roll)
        return cls(casadi_sx=s, reference_frame=reference_frame, sanity_check=False)

    def inverse(self) -> RotationMatrix:
        return self.T

    def to_rpy(self) -> Tuple[Expression, Expression, Expression]:
        """
        :return: roll, pitch, yaw
        """
        i = 0
        j = 1
        k = 2

        cy = sqrt(self[i, i] * self[i, i] + self[j, i] * self[j, i])
        if0 = cy - EPS
        ax = if_greater_zero(
            if0, atan2(self[k, j], self[k, k]), atan2(-self[j, k], self[j, j])
        )
        ay = if_greater_zero(if0, atan2(-self[k, i], cy), atan2(-self[k, i], cy))
        az = if_greater_zero(if0, atan2(self[j, i], self[i, i]), Expression(data=0))
        return ax, ay, az

    def to_quaternion(self) -> Quaternion:
        return Quaternion.from_rotation_matrix(self)

    def normalize(self) -> None:
        """Scales each of the axes to the length of one."""
        scale_v = 1.0
        self[:3, 0] = self[:3, 0].scale(scale_v)
        self[:3, 1] = self[:3, 1].scale(scale_v)
        self[:3, 2] = self[:3, 2].scale(scale_v)

    @property
    def T(self) -> RotationMatrix:
        return RotationMatrix(
            casadi_sx=self.casadi_sx.T, reference_frame=self.reference_frame
        )

    def rotational_error(self, other: RotationMatrix) -> Expression:
        """
        Calculate the rotational error between two rotation matrices.

        This function computes the angular difference between two rotation matrices
        by computing the dot product of the first matrix and the inverse of the second.
        Subsequently, it generates the angle of the resulting rotation matrix.

        :param other: The second rotation matrix.
        :return: The angular error between the two rotation matrices as an expression.
        """
        r_distance = self.dot(other.inverse())
        return r_distance.to_angle()


@dataclass(eq=False)
class Point3(SymbolicType, ReferenceFrameMixin, VectorOperationsMixin):
    """
    Represents a 3D point with reference frame handling.

    This class provides a representation of a point in 3D space, including support
    for operations such as addition, subtraction, projection onto planes/lines, and
    distance calculations. It incorporates a reference frame for kinematic computations
    and facilitates mathematical operations essential for 3D geometry modeling.

    .. note:: this is represented as a 4d vector, where the last entry is always a 1.
    """

    x_init: InitVar[Optional[ScalarData]] = None
    """
    X-coordinate of the point. Defaults to 0.
    """
    y_init: InitVar[Optional[ScalarData]] = None
    """
    Y-coordinate of the point. Defaults to 0.
    """
    z_init: InitVar[Optional[ScalarData]] = None
    """
    Z-coordinate of the point. Defaults to 0.
    """

    casadi_sx: ca.SX = field(
        kw_only=True, default_factory=lambda: ca.SX([0.0, 0.0, 0.0, 1.0])
    )

    def __post_init__(self, x_init: ScalarData, y_init: ScalarData, z_init: ScalarData):
        if x_init is not None:
            self[0] = x_init
        if y_init is not None:
            self[1] = y_init
        if z_init is not None:
            self[2] = z_init

    @classmethod
    def from_iterable(
        cls,
        data: Union[NumericalArray, Expression],
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> Point3:
        """
        Creates an instance of Point3 from provided iterable data.

        This class method is used to construct a Point3 object by processing the given
        data and optionally assigning a reference frame. The data can represent
        different array-like objects compatible with the desired format for a Point3
        instance. The provided iterable or array should follow a 1D structure to avoid
        raised errors.

        :param data: The array-like data or object such as a list, tuple, or numpy array
            used to initialize the Point3 instance.
        :param reference_frame: A reference to a `KinematicStructureEntity` object,
            representing the frame of reference for the Point3 instance. If the data
            has a `reference_frame` attribute, and this parameter is not specified,
            it will be taken from the data.
        :return: Returns an instance of Point3 initialized with the processed data
            and an optional reference frame.
        """
        expression = Expression(data=data)
        if expression.shape[0] not in (3, 4) or expression.shape[1] != 1:
            raise WrongDimensionsError(
                expected_dimensions="(3, 1) or (4, 1)",
                actual_dimensions=expression.shape,
            )
        if hasattr(data, "reference_frame") and reference_frame is None:
            reference_frame = data.reference_frame
        return cls(
            x_init=data[0],
            y_init=data[1],
            z_init=data[2],
            reference_frame=reference_frame,
        )

    def norm(self) -> Expression:
        return Expression(ca.norm_2(self[:3].casadi_sx))

    @property
    def x(self) -> Expression:
        return self[0]

    @x.setter
    def x(self, value: ScalarData):
        self[0] = value

    @property
    def y(self) -> Expression:
        return self[1]

    @y.setter
    def y(self, value: ScalarData):
        self[1] = value

    @property
    def z(self) -> Expression:
        return self[2]

    @z.setter
    def z(self, value: ScalarData):
        self[2] = value

    def __add__(self, other: Vector3) -> Point3:
        if isinstance(other, Vector3):
            result = Point3.from_iterable(self.casadi_sx.__add__(other.casadi_sx))
        else:
            return NotImplemented
        result.reference_frame = self.reference_frame
        return result

    @overload
    def __sub__(self, other: Point3) -> Vector3: ...

    @overload
    def __sub__(self, other: Vector3) -> Point3: ...

    def __sub__(self, other):
        if isinstance(other, Point3):
            result = Vector3.from_iterable(self.casadi_sx.__sub__(other.casadi_sx))
        elif isinstance(other, Vector3):
            result = Point3.from_iterable(self.casadi_sx.__sub__(other.casadi_sx))
        else:
            return NotImplemented
        result.reference_frame = self.reference_frame
        return result

    def __neg__(self) -> Point3:
        result = Point3.from_iterable(self.casadi_sx.__neg__())
        result.reference_frame = self.reference_frame
        return result

    def project_to_plane(
        self, frame_V_plane_vector1: Vector3, frame_V_plane_vector2: Vector3
    ) -> Tuple[Point3, Expression]:
        """
        Projects a point onto a plane defined by two vectors.
        This function assumes that all parameters are defined with respect to the same reference frame.

        :param frame_V_plane_vector1: First vector defining the plane
        :param frame_V_plane_vector2: Second vector defining the plane
        :return: Tuple of (projected point on the plane, signed distance from point to plane)
        """
        normal = frame_V_plane_vector1.cross(frame_V_plane_vector2)
        normal.scale(1)
        frame_V_current = self.to_vector3()
        d = normal @ frame_V_current
        projection = self - normal * d
        return projection, d

    def project_to_line(
        self, line_point: Point3, line_direction: Vector3
    ) -> Tuple[Point3, Expression]:
        """
        :param line_point: a point that the line intersects, must have the same reference frame as self
        :param line_direction: the direction of the line, must have the same reference frame as self
        :return: tuple of (closest point on the line, shortest distance between self and the line)
        """
        lp_vector = self - line_point
        cross_product = lp_vector.cross(line_direction)
        distance = cross_product.norm() / line_direction.norm()

        line_direction_unit = line_direction / line_direction.norm()
        projection_length = lp_vector @ line_direction_unit
        closest_point = line_point + line_direction_unit * projection_length

        return closest_point, distance

    def distance_to_line_segment(
        self, line_start: Point3, line_end: Point3
    ) -> Tuple[Expression, Point3]:
        """
        All parameters must have the same reference frame as self.
        :param line_start: start of the approached line
        :param line_end: end of the approached line
        :return: distance to line, the nearest point on the line
        """
        frame_P_current = self
        frame_P_line_start = line_start
        frame_P_line_end = line_end
        frame_V_line_vec = frame_P_line_end - frame_P_line_start
        pnt_vec = frame_P_current - frame_P_line_start
        line_len = frame_V_line_vec.norm()
        line_unitvec = frame_V_line_vec / line_len
        pnt_vec_scaled = pnt_vec / line_len
        t = line_unitvec @ pnt_vec_scaled
        t = limit(t, lower_limit=0.0, upper_limit=1.0)
        frame_V_offset = frame_V_line_vec * t
        dist = (frame_V_offset - pnt_vec).norm()
        frame_P_nearest = frame_P_line_start + frame_V_offset
        return dist, frame_P_nearest

    def to_vector3(self) -> Vector3:
        return Vector3(
            casadi_sx=copy(self.casadi_sx), reference_frame=self.reference_frame
        )


@dataclass(eq=False)
class Vector3(SymbolicType, ReferenceFrameMixin, VectorOperationsMixin):
    """
    Representation of a 3D vector with reference frame support for homogenous transformations.

    This class provides a structured representation of 3D vectors. It includes
    support for operations such as addition, subtraction, scaling, dot product,
    cross product, and more. It is compatible with symbolic computations and
    provides methods to define standard basis vectors, normalize a vector, and
    compute geometric properties such as the angle between vectors. The class
    also includes support for working in different reference frames.

    .. note:: this is represented as a 4d vector, where the last entry is always a 0.
    """

    x_init: InitVar[Optional[ScalarData]] = None
    """
    X-coordinate of the point. Defaults to 0.
    """
    y_init: InitVar[Optional[ScalarData]] = None
    """
    Y-coordinate of the point. Defaults to 0.
    """
    z_init: InitVar[Optional[ScalarData]] = None
    """
    Z-coordinate of the point. Defaults to 0.
    """

    vis_frame: Optional[KinematicStructureEntity] = field(kw_only=True, default=None)
    """
    The reference frame associated with the vector, used for visualization purposes only. Optional.
    It will be visualized at the origin of the vis_frame
    """

    casadi_sx: ca.SX = field(
        kw_only=True, default_factory=lambda: ca.SX([0.0, 0.0, 0.0, 0.0])
    )

    def __post_init__(self, x_init: ScalarData, y_init: ScalarData, z_init: ScalarData):
        if x_init is not None:
            self[0] = x_init
        if y_init is not None:
            self[1] = y_init
        if z_init is not None:
            self[2] = z_init

    @classmethod
    def from_iterable(
        cls,
        data: Union[NumericalArray, Expression],
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> Vector3:
        """
        Creates an instance of Vector3 from provided iterable data.

        This class method is used to construct a Vector3 object by processing the given
        data and optionally assigning a reference frame. The data can represent
        different array-like objects compatible with the desired format for a Vector3
        instance. The provided iterable or array should follow a 1D structure to avoid
        raised errors.

        :param data: The array-like data or object such as a list, tuple, or numpy array
            used to initialize the Vector3 instance.
        :param reference_frame: A reference to a `KinematicStructureEntity` object,
            representing the frame of reference for the Vector3 instance. If the data
            has a `reference_frame` attribute, and this parameter is not specified,
            it will be taken from the data.
        :return: Returns an instance of Vector3 initialized with the processed data
            and an optional reference frame.
        """
        expression = Expression(data=data)
        if expression.shape[0] not in (3, 4) or expression.shape[1] != 1:
            raise WrongDimensionsError(
                expected_dimensions="(3, 1) or (4, 1)",
                actual_dimensions=expression.shape,
            )
        result = cls(
            x_init=data[0],
            y_init=data[1],
            z_init=data[2],
            reference_frame=reference_frame,
        )
        if hasattr(data, "vis_frame"):
            result.vis_frame = data.vis_frame
        return result

    @classmethod
    def X(cls, reference_frame: Optional[KinematicStructureEntity] = None) -> Vector3:
        return cls(x_init=1, y_init=0, z_init=0, reference_frame=reference_frame)

    @classmethod
    def Y(cls, reference_frame: Optional[KinematicStructureEntity] = None) -> Vector3:
        return cls(x_init=0, y_init=1, z_init=0, reference_frame=reference_frame)

    @classmethod
    def Z(cls, reference_frame: Optional[KinematicStructureEntity] = None) -> Vector3:
        return cls(x_init=0, y_init=0, z_init=1, reference_frame=reference_frame)

    @classmethod
    def unit_vector(
        cls,
        x: ScalarData = 0,
        y: ScalarData = 0,
        z: ScalarData = 0,
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> Vector3:
        v = cls(x_init=x, y_init=y, z_init=z, reference_frame=reference_frame)
        v.scale(1, unsafe=True)
        return v

    @property
    def x(self) -> Expression:
        return self[0]

    @x.setter
    def x(self, value: ScalarData):
        self[0] = value

    @property
    def y(self) -> Expression:
        return self[1]

    @y.setter
    def y(self, value: ScalarData):
        self[1] = value

    @property
    def z(self) -> Expression:
        return self[2]

    @z.setter
    def z(self, value: ScalarData):
        self[2] = value

    def __add__(self, other: Vector3) -> Vector3:
        if isinstance(other, Vector3):
            result = Vector3.from_iterable(self.casadi_sx.__add__(other.casadi_sx))
        else:
            return NotImplemented
        result.reference_frame = self.reference_frame
        return result

    def __sub__(self, other: Vector3) -> Vector3:
        if isinstance(other, Vector3):
            result = Vector3.from_iterable(self.casadi_sx.__sub__(other.casadi_sx))
        else:
            return NotImplemented
        result.reference_frame = self.reference_frame
        return result

    def __mul__(self, other: ScalarData) -> Vector3:
        if isinstance(other, ScalarData):
            result = Vector3.from_iterable(self.casadi_sx.__mul__(to_sx(other)))
        else:
            return NotImplemented
        result.reference_frame = self.reference_frame
        return result

    def __rmul__(self, other: float) -> Vector3:
        if isinstance(other, (int, float)):
            result = Vector3.from_iterable(self.casadi_sx.__mul__(other))
        else:
            return NotImplemented
        result.reference_frame = self.reference_frame
        return result

    def __truediv__(self, other: ScalarData) -> Vector3:
        if isinstance(other, ScalarData):
            result = Vector3.from_iterable(self.casadi_sx.__truediv__(to_sx(other)))
        else:
            return NotImplemented
        result.reference_frame = self.reference_frame
        return result

    def safe_division(
        self,
        other: ScalarData,
        if_nan: Optional[Vector3] = None,
    ) -> GenericSymbolicType:
        """
        A version of division where no sub-expression is ever NaN. The expression would evaluate to 'if_nan', but
        you should probably never work with the 'if_nan' result. However, if one sub-expressions is NaN, the whole expression
        evaluates to NaN, even if it is only in a branch of an if-else, that is not returned.
        This method is a workaround for such cases.
        """
        if if_nan is None:
            if_nan = Vector3()
        save_denominator = if_eq_zero(
            condition=other, if_result=Expression(data=1), else_result=other
        )
        return if_eq_zero(other, if_result=if_nan, else_result=self / save_denominator)

    def __neg__(self) -> Vector3:
        result = Vector3.from_iterable(self.casadi_sx.__neg__())
        result.reference_frame = self.reference_frame
        return result

    def dot(self, other: Vector3) -> Expression:
        if isinstance(other, Vector3):
            return Expression(ca.mtimes(self[:3].T.casadi_sx, other[:3].casadi_sx))
        raise _operation_type_error(self, "dot", other)

    def __matmul__(self, other: Vector3) -> Expression:
        return self.dot(other)

    def cross(self, other: Vector3) -> Vector3:
        result = ca.cross(self.casadi_sx[:3], other.casadi_sx[:3])
        result = self.__class__.from_iterable(result)
        result.reference_frame = self.reference_frame
        return result

    def norm(self) -> Expression:
        return Expression(ca.norm_2(self[:3].casadi_sx))

    def scale(self, a: ScalarData, unsafe: bool = False):
        if unsafe:
            self.casadi_sx = ((self / self.norm()) * a).casadi_sx
        else:
            self.casadi_sx = (self.safe_division(self.norm()) * a).casadi_sx

    def project_to_cone(
        self, frame_V_cone_axis: Vector3, cone_theta: Union[Symbol, float, Expression]
    ) -> Vector3:
        """
        Projects a given vector onto the boundary of a cone defined by its axis and angle.

        This function computes the projection of a vector onto the boundary of a
        cone specified by its axis and half-angle. It handles special cases where
        the input vector is collinear with the cone's axis. The projection ensures
        the resulting vector lies within the cone's boundary.

        :param frame_V_cone_axis: The axis of the cone.
        :param cone_theta: The half-angle of the cone in radians. Can be a symbolic value or a float.
        :return: The projection of the input vector onto the cone's boundary.
        """
        frame_V_current = self
        frame_V_cone_axis_normed = copy(frame_V_cone_axis)
        frame_V_cone_axis_normed.scale(1)
        beta = frame_V_current @ frame_V_cone_axis_normed
        norm_v = frame_V_current.norm()

        # Compute the perpendicular component.
        v_perp = frame_V_current - (frame_V_cone_axis_normed * beta)
        norm_v_perp = v_perp.norm()
        v_perp.scale(1)

        s = beta * cos(cone_theta) + norm_v_perp * sin(cone_theta)
        projected_vector = (
            (frame_V_cone_axis_normed * cos(cone_theta)) + (v_perp * sin(cone_theta))
        ) * s
        # Handle the case when v is collinear with a.
        project_on_cone_boundary = if_less(
            a=norm_v_perp,
            b=1e-8,
            if_result=frame_V_cone_axis_normed * norm_v * cos(cone_theta),
            else_result=projected_vector,
        )

        return if_greater_eq(
            a=beta,
            b=norm_v * np.cos(cone_theta),
            if_result=frame_V_current,
            else_result=project_on_cone_boundary,
        )

    def angle_between(self, other: Vector3) -> Expression:
        return acos(
            limit(
                self @ other / (self.norm() * other.norm()),
                lower_limit=-1,
                upper_limit=1,
            )
        )

    def slerp(self, other: Vector3, t: ScalarData) -> Vector3:
        """
        spherical linear interpolation
        :param other: vector of same length as self
        :param t: value between 0 and 1. 0 is v1 and 1 is v2
        """
        angle = safe_acos(self @ other)
        angle2 = if_eq(angle, 0, Expression(data=1), angle)
        return if_eq(
            angle,
            0,
            self,
            self * (sin((1 - t) * angle2) / sin(angle2))
            + other * (sin(t * angle2) / sin(angle2)),
        )

    def to_point3(self) -> Point3:
        return Point3(
            casadi_sx=copy(self.casadi_sx), reference_frame=self.reference_frame
        )


@dataclass(eq=False)
class Quaternion(SymbolicType, ReferenceFrameMixin):
    """
    Represents a quaternion, which is a mathematical entity used to encode
    rotations in three-dimensional space.

    The Quaternion class provides methods for creating quaternion objects
    from various representations, such as axis-angle, roll-pitch-yaw,
    and rotation matrices. It supports operations to define and manipulate
    rotations in 3D space efficiently. Quaternions are used extensively
    in physics, computer graphics, robotics, and aerospace engineering
    to represent orientations and rotations.
    """

    x_init: InitVar[Optional[ScalarData]] = None
    """
    X-coordinate of the point. Defaults to 0.
    """
    y_init: InitVar[Optional[ScalarData]] = None
    """
    Y-coordinate of the point. Defaults to 0.
    """
    z_init: InitVar[Optional[ScalarData]] = None
    """
    Z-coordinate of the point. Defaults to 0.
    """
    w_init: InitVar[Optional[ScalarData]] = None
    """
    W-coordinate of the point. Defaults to 0.
    """

    casadi_sx: ca.SX = field(
        kw_only=True, default_factory=lambda: ca.SX([0.0, 0.0, 0.0, 1.0])
    )

    def __post_init__(
        self,
        x_init: ScalarData,
        y_init: ScalarData,
        z_init: ScalarData,
        w_init: ScalarData,
    ):
        if x_init is not None:
            self[0] = x_init
        if y_init is not None:
            self[1] = y_init
        if z_init is not None:
            self[2] = z_init
        if w_init is not None:
            self[3] = w_init

    def __neg__(self) -> Quaternion:
        return Quaternion.from_iterable(self.casadi_sx.__neg__())

    @classmethod
    def from_iterable(
        cls,
        data: Union[NumericalArray, Expression],
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> Quaternion:
        """
        Creates an instance of Quaternion from provided iterable data.

        This class method is used to construct a Quaternion object by processing the given
        data and optionally assigning a reference frame. The data can represent
        different array-like objects compatible with the desired format for a Quaternion
        instance. The provided iterable or array should follow a 1D structure to avoid
        raised errors.

        :param data: The array-like data or object such as a list, tuple, or numpy array
            used to initialize the Quaternion instance.
        :param reference_frame: A reference to a `KinematicStructureEntity` object,
            representing the frame of reference for the Quaternion instance. If the data
            has a `reference_frame` attribute, and this parameter is not specified,
            it will be taken from the data.

        :return: Returns an instance of Quaternion initialized with the processed data
            and an optional reference frame.
        """
        if hasattr(data, "shape") and len(data.shape) > 1 and data.shape[1] != 1:
            raise ValueError("The iterable must be a 1d list, tuple or array")
        return cls(
            x_init=data[0],
            y_init=data[1],
            z_init=data[2],
            w_init=data[3],
            reference_frame=reference_frame,
        )

    @property
    def x(self) -> Expression:
        return self[0]

    @x.setter
    def x(self, value: ScalarData):
        self[0] = value

    @property
    def y(self) -> Expression:
        return self[1]

    @y.setter
    def y(self, value: ScalarData):
        self[1] = value

    @property
    def z(self) -> Expression:
        return self[2]

    @z.setter
    def z(self, value: ScalarData):
        self[2] = value

    @property
    def w(self) -> Expression:
        return self[3]

    @w.setter
    def w(self, value: ScalarData):
        self[3] = value

    @classmethod
    def from_axis_angle(
        cls,
        axis: Vector3,
        angle: ScalarData,
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> Quaternion:
        """
        Creates a quaternion from an axis-angle representation.

        This method uses the axis of rotation and the rotation angle (in radians)
        to construct a quaternion representation of the rotation. Optionally,
        a reference frame can be specified to which the resulting quaternion is
        associated.

        :param axis: A 3D vector representing the axis of rotation.
        :param angle: The rotation angle in radians.
        :param reference_frame: An optional reference frame entity associated
            with the quaternion, if applicable.
        :return: A quaternion representing the rotation defined by
            the given axis and angle.
        """
        half_angle = angle / 2
        return cls(
            x_init=axis[0] * sin(half_angle),
            y_init=axis[1] * sin(half_angle),
            z_init=axis[2] * sin(half_angle),
            w_init=cos(half_angle),
            reference_frame=reference_frame,
        )

    @classmethod
    def from_rpy(
        cls,
        roll: ScalarData,
        pitch: ScalarData,
        yaw: ScalarData,
        reference_frame: Optional[KinematicStructureEntity] = None,
    ) -> Quaternion:
        """
        Creates a Quaternion instance from specified roll, pitch, and yaw angles.

        The method computes the quaternion representation of the given roll, pitch,
        and yaw angles using trigonometric transformations based on their
        half-angle values for efficient calculations.

        :param roll: The roll angle in radians.
        :param pitch: The pitch angle in radians.
        :param yaw: The yaw angle in radians.
        :param reference_frame: Optional reference frame entity associated with
            the quaternion.
        :return: A Quaternion instance representing the rotation defined by the
            specified roll, pitch, and yaw angles.
        """
        roll = to_sx(roll)
        pitch = to_sx(pitch)
        yaw = to_sx(yaw)
        roll_half = roll / 2.0
        pitch_half = pitch / 2.0
        yaw_half = yaw / 2.0

        c_roll = cos(roll_half)
        s_roll = sin(roll_half)
        c_pitch = cos(pitch_half)
        s_pitch = sin(pitch_half)
        c_yaw = cos(yaw_half)
        s_yaw = sin(yaw_half)

        cc = c_roll * c_yaw
        cs = c_roll * s_yaw
        sc = s_roll * c_yaw
        ss = s_roll * s_yaw

        x = c_pitch * sc - s_pitch * cs
        y = c_pitch * ss + s_pitch * cc
        z = c_pitch * cs - s_pitch * sc
        w = c_pitch * cc + s_pitch * ss

        return cls(
            x_init=x, y_init=y, z_init=z, w_init=w, reference_frame=reference_frame
        )

    @classmethod
    def from_rotation_matrix(
        cls, r: Union[RotationMatrix, TransformationMatrix]
    ) -> Quaternion:
        """
        Creates a Quaternion object initialized from a given rotation matrix.

        This method constructs a quaternion representation of the provided rotation matrix. It is designed to handle
        different cases of rotation matrix configurations to ensure numerical stability during computation. The resultant
        quaternion adheres to the expected mathematical relationship with the given rotation matrix.

        :param r: The input matrix representing a rotation. It can be either a `RotationMatrix` or `TransformationMatrix`.
                  This matrix is expected to have a valid mathematical structure typical for rotation matrices.

        :return: A new instance of `Quaternion` corresponding to the given rotation matrix `r`.
        """
        q = Expression(data=(0, 0, 0, 0))
        t = r.trace()

        if0 = t - r[3, 3]

        if1 = r[1, 1] - r[0, 0]

        m_i_i = if_greater_zero(if1, r[1, 1], r[0, 0])
        m_i_j = if_greater_zero(if1, r[1, 2], r[0, 1])
        m_i_k = if_greater_zero(if1, r[1, 0], r[0, 2])

        m_j_i = if_greater_zero(if1, r[2, 1], r[1, 0])
        m_j_j = if_greater_zero(if1, r[2, 2], r[1, 1])
        m_j_k = if_greater_zero(if1, r[2, 0], r[1, 2])

        m_k_i = if_greater_zero(if1, r[0, 1], r[2, 0])
        m_k_j = if_greater_zero(if1, r[0, 2], r[2, 1])
        m_k_k = if_greater_zero(if1, r[0, 0], r[2, 2])

        if2 = r[2, 2] - m_i_i

        m_i_i = if_greater_zero(if2, r[2, 2], m_i_i)
        m_i_j = if_greater_zero(if2, r[2, 0], m_i_j)
        m_i_k = if_greater_zero(if2, r[2, 1], m_i_k)

        m_j_i = if_greater_zero(if2, r[0, 2], m_j_i)
        m_j_j = if_greater_zero(if2, r[0, 0], m_j_j)
        m_j_k = if_greater_zero(if2, r[0, 1], m_j_k)

        m_k_i = if_greater_zero(if2, r[1, 2], m_k_i)
        m_k_j = if_greater_zero(if2, r[1, 0], m_k_j)
        m_k_k = if_greater_zero(if2, r[1, 1], m_k_k)

        t = if_greater_zero(if0, t, m_i_i - (m_j_j + m_k_k) + r[3, 3])
        q[0] = if_greater_zero(
            if0,
            r[2, 1] - r[1, 2],
            if_greater_zero(if2, m_i_j + m_j_i, if_greater_zero(if1, m_k_i + m_i_k, t)),
        )
        q[1] = if_greater_zero(
            if0,
            r[0, 2] - r[2, 0],
            if_greater_zero(if2, m_k_i + m_i_k, if_greater_zero(if1, t, m_i_j + m_j_i)),
        )
        q[2] = if_greater_zero(
            if0,
            r[1, 0] - r[0, 1],
            if_greater_zero(if2, t, if_greater_zero(if1, m_i_j + m_j_i, m_k_i + m_i_k)),
        )
        q[3] = if_greater_zero(if0, t, m_k_j - m_j_k)

        q *= 0.5 / sqrt(t * r[3, 3])
        return cls.from_iterable(q, reference_frame=r.reference_frame)

    def conjugate(self) -> Quaternion:
        return Quaternion(
            x_init=-self[0],
            y_init=-self[1],
            z_init=-self[2],
            w_init=self[3],
            reference_frame=self.reference_frame,
        )

    def multiply(self, q: Quaternion) -> Quaternion:
        return Quaternion(
            x_init=self.x * q.w + self.y * q.z - self.z * q.y + self.w * q.x,
            y_init=-self.x * q.z + self.y * q.w + self.z * q.x + self.w * q.y,
            z_init=self.x * q.y - self.y * q.x + self.z * q.w + self.w * q.z,
            w_init=-self.x * q.x - self.y * q.y - self.z * q.z + self.w * q.w,
            reference_frame=self.reference_frame,
        )

    def diff(self, q: Quaternion) -> Quaternion:
        """
        :return: quaternion p, such that self*p=q
        """
        return self.conjugate().multiply(q)

    def normalize(self) -> None:
        norm_ = self.norm()
        self.x /= norm_
        self.y /= norm_
        self.z /= norm_
        self.w /= norm_

    def to_axis_angle(self) -> Tuple[Vector3, Expression]:
        self.normalize()
        w2 = sqrt(1 - self.w**2)
        m = if_eq_zero(w2, Expression(data=1), w2)  # avoid /0
        angle = if_eq_zero(w2, Expression(data=0), (2 * acos(limit(self.w, -1, 1))))
        x = if_eq_zero(w2, Expression(data=0), self.x / m)
        y = if_eq_zero(w2, Expression(data=0), self.y / m)
        z = if_eq_zero(w2, Expression(data=1), self.z / m)
        return (
            Vector3(x_init=x, y_init=y, z_init=z, reference_frame=self.reference_frame),
            angle,
        )

    def to_rotation_matrix(self) -> RotationMatrix:
        return RotationMatrix.from_quaternion(self)

    def to_rpy(self) -> Tuple[Expression, Expression, Expression]:
        return self.to_rotation_matrix().to_rpy()

    def dot(self, other: Quaternion) -> Expression:
        if isinstance(other, Quaternion):
            return Expression(ca.mtimes(self.casadi_sx.T, other.casadi_sx))
        return NotImplemented

    def slerp(self, other: Quaternion, t: ScalarData) -> Quaternion:
        """
        Spherical linear interpolation that takes into account that q == -q
        t=0 will return self and t=1 will return other.
        :param other: the other quaternion
        :param t: float, 0-1
        :return: 4x1 Matrix; Return spherical linear interpolation between two quaternions.
        """
        cos_half_theta = self.dot(other)

        if0 = -cos_half_theta
        other = if_greater_zero(if0, -other, other)
        cos_half_theta = if_greater_zero(if0, -cos_half_theta, cos_half_theta)

        if1 = abs(cos_half_theta) - 1.0

        # enforce acos(x) with -1 < x < 1
        cos_half_theta = min(1, cos_half_theta)
        cos_half_theta = max(-1, cos_half_theta)

        half_theta = acos(cos_half_theta)

        sin_half_theta = sqrt(1.0 - cos_half_theta * cos_half_theta)
        if2 = 0.001 - abs(sin_half_theta)

        ratio_a = (sin((1.0 - t) * half_theta)).safe_division(sin_half_theta)
        ratio_b = sin(t * half_theta).safe_division(sin_half_theta)

        mid_quaternion = Quaternion.from_iterable(
            Expression(data=self) * 0.5 + Expression(data=other) * 0.5
        )
        slerped_quaternion = Quaternion.from_iterable(
            Expression(data=self) * ratio_a + Expression(data=other) * ratio_b
        )

        return if_greater_eq_zero(
            if1, self, if_greater_zero(if2, mid_quaternion, slerped_quaternion)
        )


# %% type hints

NumericalScalar = Union[int, float, IntEnum]
NumericalArray = Union[np.ndarray, Iterable[NumericalScalar]]
Numerical2dMatrix = Union[np.ndarray, Iterable[NumericalArray]]
NumericalData = Union[NumericalScalar, NumericalArray, Numerical2dMatrix]

SymbolicScalar = Union[Symbol, Expression]
SymbolicArray = Union[Expression, Point3, Vector3, Quaternion]
Symbolic2dMatrix = Union[Expression, RotationMatrix, TransformationMatrix]
SymbolicData = Union[SymbolicScalar, SymbolicArray, Symbolic2dMatrix]

ScalarData = Union[NumericalScalar, SymbolicScalar]
ArrayData = Union[NumericalArray, SymbolicArray]
Matrix2dData = Union[Numerical2dMatrix, Symbolic2dMatrix]


GenericSpatialType = TypeVar(
    "GenericSpatialType",
    Point3,
    Vector3,
    TransformationMatrix,
    RotationMatrix,
    Quaternion,
)

GenericHomogeneousSpatialType = TypeVar(
    "GenericHomogeneousSpatialType",
    Point3,
    Vector3,
    TransformationMatrix,
    RotationMatrix,
)

GenericRotatableSpatialType = TypeVar(
    "GenericRotatableSpatialType", Vector3, TransformationMatrix, RotationMatrix
)

GenericSymbolicType = TypeVar(
    "GenericSymbolicType",
    Symbol,
    Expression,
    Point3,
    Vector3,
    TransformationMatrix,
    RotationMatrix,
    Quaternion,
)
