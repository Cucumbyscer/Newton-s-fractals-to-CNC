import sympy
import numpy

from fractal_types import (AxisX, AxisY, RealGrid, ComplexGrid, BoolMask2D, ComplexVector, BoolVector, FlatIndices,
                           IterMap, ComplexFunc, NewtonResult)


def compile_function(expr_str: str) -> tuple[sympy.Expr, sympy.Expr, ComplexFunc, ComplexFunc]:
    z: sympy.Symbol = sympy.Symbol("z")
    expr: sympy.Expr = sympy.sympify(expr_str, locals={"z": z, "i": sympy.I})
    dexpr: sympy.Expr = sympy.diff(expr, z)

    f: ComplexFunc = sympy.lambdify(z, expr, modules=["numpy"])
    df: ComplexFunc = sympy.lambdify(z, dexpr, modules=["numpy"])
    return expr, dexpr, f, df


def newton_fractal_iters(expr_str: str,
                         x_min: float = -2.0, x_max: float = 2.0,
                         y_min: float = -2.0, y_max: float = 2.0,
                         eps: float = 1e-6, df_eps: float = 1e-14,
                         nx: int = 350, ny: int = 350,
                         max_iter: int = 60) -> NewtonResult:

    expr, dexpr, f, df = compile_function(expr_str)

    # задаём комплексную плоскость
    xs: AxisX = numpy.linspace(x_min, x_max, nx)        # (nx,)  Re(z)
    ys: AxisY = numpy.linspace(y_min, y_max, ny)        # (ny,)  Im(z)
    X: RealGrid                                         # (ny, nx), X[iy, ix] = xs[ix]
    Y: RealGrid                                         # (ny, nx), Y[iy, ix] = ys[iy]
    X, Y = numpy.meshgrid(xs, ys)
    Z: ComplexGrid = X + 1j * Y                         # (ny, nx) complex128

    iters: IterMap = numpy.zeros(Z.shape, dtype=numpy.int32)   # (ny, nx), все 0
    active: BoolMask2D = numpy.ones(Z.shape, dtype=bool)       # (ny, nx), все True

    # совершаем итерации по методу Ньютона
    for i in range(1, max_iter + 1):
        if not active.any():
            break

        # одномерные массивы
        Z_active: ComplexVector = Z[active]                 # (k,)
        f_Z_active: ComplexVector = f(Z_active)             # (k,)  f(z)
        df_Z_active: ComplexVector = df(Z_active)           # (k,)  f'(z)

        safe: BoolVector = numpy.abs(df_Z_active) > df_eps  # (k,)
        step: ComplexVector = numpy.zeros_like(Z_active, dtype=numpy.complex128)  # (k,)
        step[safe] = f_Z_active[safe] / df_Z_active[safe]

        # выполняем один шаг метода Ньютона
        Z_active_next: ComplexVector = Z_active - step      # (k,)
        Z[active] = Z_active_next                           # раскладываем обратно в (ny, nx)

        # корень удовлетворяет при достижении порога сходимости
        permissible_value: BoolVector = numpy.abs(f(Z_active_next)) < eps   # (k,)

        # idx_active[j] является одномерным номером ячейки (ny*nx) для j-й активной точки
        idx_active: FlatIndices = numpy.flatnonzero(active)                 # (k,)
        converged_idx: FlatIndices = idx_active[permissible_value]          # (c,), c ≤ k
        iters.flat[converged_idx] = i
        active.flat[converged_idx] = False

    # не сошедшиеся точки помечаем как максимальную итерацию
    iters[active] = max_iter

    return {"expr": expr,
            "dexpr": dexpr,
            "iters": iters,
            "grid": (xs, ys),
            "params": dict(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                           eps=eps, df_eps=df_eps,
                           max_iter=max_iter,
                           nx=nx, ny=ny)}
