from typing import Annotated, Callable, TypeAlias, TypedDict

import numpy
import sympy
from numpy.typing import NDArray


# чтение аннотаций пользователем
class Shape:
    def __init__(self, *sizes: str):
        self.sizes = sizes

    def __repr__(self):
        return f"Shape({', '.join(self.sizes)})"


# (ny, nx)
GridShape: TypeAlias = tuple[int, int]

ZLevelMM: TypeAlias = numpy.float64

AxisX: TypeAlias = Annotated[NDArray[numpy.float64], Shape("nx")]
AxisY: TypeAlias = Annotated[NDArray[numpy.float64], Shape("ny")]
RealGrid: TypeAlias = Annotated[NDArray[numpy.float64], Shape("ny", "nx")]
ComplexGrid: TypeAlias = Annotated[NDArray[numpy.complex128], Shape("ny", "nx")]

BoolMask2D: TypeAlias = Annotated[NDArray[numpy.bool_], Shape("ny", "nx")]
ComplexVector: TypeAlias = Annotated[NDArray[numpy.complex128], Shape("k")]
BoolVector: TypeAlias = Annotated[NDArray[numpy.bool_], Shape("k")]
ComplexFunc: TypeAlias = Callable[[ComplexVector], ComplexVector]

FlatIndices: TypeAlias = Annotated[NDArray[numpy.intp], Shape("k")]  # одномерные индексы для двумерных массивов
                                                                     # (j в (iy, ix): (j // nx, j % nx))

IterMap: TypeAlias = Annotated[NDArray[numpy.int32], Shape("ny", "nx")]


# CNC
NormMap: TypeAlias = Annotated[NDArray[numpy.float64], Shape("ny", "nx")]
HeightMapMM: TypeAlias = Annotated[NDArray[numpy.float64], Shape("ny", "nx")]
DepthsMM: TypeAlias = Annotated[NDArray[numpy.float64], Shape("k")]

QuantileProbs: TypeAlias = Annotated[NDArray[numpy.float64], Shape("n_levels")]
QuantileDepthsMM: TypeAlias = Annotated[NDArray[numpy.float64], Shape("n_levels")]

ZLevelsMM: TypeAlias = list[ZLevelMM]

PointYX: TypeAlias = Annotated[NDArray[numpy.float64], Shape("2")]

Contour: TypeAlias = Annotated[NDArray[numpy.float64], Shape("m", "2")]
ContourList: TypeAlias = list[Contour]
ContoursByLevel: TypeAlias = dict[ZLevelMM, ContourList]


NewtonParams: TypeAlias = TypedDict('NewtonParams', {'x_min': float, 'x_max': float,
                                                     'y_min': float, 'y_max': float,
                                                     'eps': float, 'df_eps': float,
                                                     'max_iter': int,
                                                     'nx': int, 'ny': int})
NewtonParamsDict: TypeAlias = NewtonParams


NewtonResult: TypeAlias = TypedDict('NewtonResult', {'expr': sympy.Expr,
                                                     'dexpr': sympy.Expr,
                                                     'iters': 'IterMap',
                                                     'grid': tuple['AxisX', 'AxisY'],
                                                     'params': NewtonParamsDict})

ComputeParams: TypeAlias = TypedDict('ComputeParams', {'expr_str': str,
                                                       'x_min': float, 'x_max': float,
                                                       'y_min': float, 'y_max': float,
                                                       'nx': int, 'ny': int,
                                                       'max_iter': int,
                                                       'eps': float, 'df_eps': float,
                                                       'zmax_mm': float,
                                                       'n_levels': int,
                                                       'min_depth_mm': float})

ComputeResult: TypeAlias = TypedDict('ComputeResult', {**NewtonResult.__annotations__,
                                                       'heightmap_mm': 'HeightMapMM',
                                                       'z_levels': 'ZLevelsMM',
                                                       'contours_by_level': 'ContoursByLevel'})
