import traceback
from PyQt5.QtCore import QThread, pyqtSignal

from fractal_math import newton_fractal_iters
from creat_CNC import iters_to_heightmap_mm, auto_z_levels, extract_contours_by_level
from fractal_types import (ComputeParams, ComputeResult, NewtonResult,
                           HeightMapMM, ZLevelsMM, ContoursByLevel)


class ComputeWorker(QThread):
    done = pyqtSignal(dict)
    fail = pyqtSignal(str)

    def __init__(self, params: ComputeParams) -> None:
        super().__init__()
        self.params: ComputeParams = params

    def run(self) -> None:
        try:
            params = self.params

            data: NewtonResult = newton_fractal_iters(expr_str=params["expr_str"],
                                                      x_min=params["x_min"], x_max=params["x_max"],
                                                      y_min=params["y_min"], y_max=params["y_max"],
                                                      nx=params["nx"], ny=params["ny"],
                                                      max_iter=params["max_iter"],
                                                      eps=params["eps"],
                                                      df_eps=params["df_eps"])

            heightmap_mm: HeightMapMM = iters_to_heightmap_mm(data["iters"], params["max_iter"], params["zmax_mm"])

            z_levels: ZLevelsMM = auto_z_levels(heightmap_mm=heightmap_mm,
                                                n_levels=params["n_levels"],
                                                min_depth_mm=params["min_depth_mm"])

            contours_by_level: ContoursByLevel = extract_contours_by_level(heightmap_mm, z_levels)

            result: ComputeResult = {**data,
                                     "heightmap_mm": heightmap_mm,
                                     "z_levels": z_levels,
                                     "contours_by_level": contours_by_level}

            self.done.emit(result)

        except Exception:
            self.fail.emit(traceback.format_exc())
