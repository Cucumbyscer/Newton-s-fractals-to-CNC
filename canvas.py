from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

matplotlib.use("Qt5Agg")


# Обёртка графика matplotlib для pyqt5
class MplCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(facecolor="#0b1220")
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor("#0b1220")

        super().__init__(self.figure)
        self._colorbar = None

    def clear(self):
        self.figure.clear()
        self.figure.set_facecolor("#0b1220")

        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor("#0b1220")
        self._colorbar = None

    def plot_heatmap_and_contours(self, heightmap_mm, contours_by_level,
                                  view_mode="both", cmap="magma", title="",
                                  contour_alpha=0.9, contours_color="#c7d2fe"):

        self.clear()

        show_heat = view_mode in ("Heatmap", "Both")
        show_cont = view_mode in ("Contours", "Both")

        if show_heat:
            im = self.axes.imshow(heightmap_mm, origin="lower", cmap=cmap)
            self._colorbar = self.figure.colorbar(im, ax=self.axes, fraction=0.046, pad=0.04)
            self._colorbar.ax.tick_params(colors="#cfd8e3")
            self._colorbar.set_label("Глубина (мм)", color="#cfd8e3")

        if show_cont and contours_by_level:
            z_levels = sorted(contours_by_level.keys(), reverse=True)

            for z in z_levels:
                for contour in contours_by_level[z]:
                    if contour is None or len(contour) < 2:
                        continue
                    ys = contour[:, 0]
                    xs = contour[:, 1]
                    self.axes.plot(xs, ys,
                                   alpha=contour_alpha,
                                   color=contours_color)

        # Оформление графика
        self.axes.set_title(title, color="#e9eef5", fontsize=12, pad=10)
        self.axes.tick_params(colors="#7f8ea3")
        self.axes.set_xlabel("X", color="#7f8ea3")
        self.axes.set_ylabel("Y", color="#7f8ea3")
        self.axes.set_aspect("equal")

        self.draw()
