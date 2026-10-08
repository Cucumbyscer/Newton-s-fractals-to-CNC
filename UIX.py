import traceback
import numpy

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGroupBox, QLabel, QLineEdit,
                             QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QSlider, QFileDialog, QScrollArea,
                             QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt

from fractal_math import compile_function
from creat_CNC import contours_to_gcode_mach3
from worker import ComputeWorker
from canvas import MplCanvas
from polynomials import polynomials


# Показать окно ошибки
def nice_error(msg: str):
    box = QMessageBox()
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle("Ошибка")
    box.setText(msg)
    box.exec_()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Программа для визуализации и ЧПУ программирования фракталов Ньютона в коде ISO")
        self.resize(1280, 760)

        self.last_data = None  # сюда кладём последний рассчитанный фрактал (iters/heightmap/contours)
        self.worker = None  # поток вычислений

        # крутилка
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Панель параметров
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left_container)
        splitter.addWidget(scroll)

        splitter.setStretchFactor(0, 0)  # фиксированная
        splitter.setStretchFactor(1, 1)  # тугая
        splitter.setSizes([550, 1000])

        # профили качества
        g_quality = QGroupBox("Качество фрактала")
        lq = QVBoxLayout(g_quality)

        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Низкое")
        self.quality_combo.addItem("Среднее")
        self.quality_combo.addItem("Высокое")

        lq.addWidget(QLabel("Профиль качества:"))
        lq.addWidget(self.quality_combo)
        left_layout.addWidget(g_quality)

        # полином
        g_func = QGroupBox("Полином f(z)")
        lf = QVBoxLayout(g_func)

        self.poly_edit = QLineEdit("z**3 - 1")
        self.poly_edit.setPlaceholderText("Введите функцию полинома")
        self.poly_edit.setToolTip('''<b>Правила ввода для парсера (SymPy):</b><br>
                                     Умножение: <b>*</b> (2*z)<br>
                                     Деление: <b>/</b> (1/3)<br>
                                     Возведение в степень: <b>**</b> (z**3)<br>
                                     Мнимая единица (i): <b>i</b><br>"
                                     Функции: sin(z), cos(z)''')

        lf.addWidget(self.poly_edit)

        btn_row = QHBoxLayout()
        self.btn_random = QPushButton("Случайный полином")
        self.btn_calc = QPushButton("Пересчитать")
        self.btn_calc.setToolTip("При изменении параметров в секторе \"ЧПУ\" необходимо сделать пересчёт для обновления"
                                 " параметров в исходном коде")
        btn_row.addWidget(self.btn_random)
        btn_row.addWidget(self.btn_calc)
        lf.addLayout(btn_row)

        self.err_label = QLabel("")
        self.err_label.setStyleSheet("color: #ff6b6b; font-weight: 600;")
        lf.addWidget(self.err_label)

        left_layout.addWidget(g_func)

        # окно комплексной плоскости
        g_plane = QGroupBox("Окно комплексной плоскости")
        lp = QVBoxLayout(g_plane)

        row1 = QHBoxLayout()
        self.x_min = QDoubleSpinBox()
        self.x_min.setRange(-2000, 2000)
        self.x_min.setDecimals(3)
        self.x_min.setValue(-2.0)
        self.x_min.setToolTip(
            "x_min — левая граница по Re(z)")

        self.x_max = QDoubleSpinBox()
        self.x_max.setRange(-2000, 2000)
        self.x_max.setDecimals(3)
        self.x_max.setValue(2.0)
        self.x_max.setToolTip(
            "x_max — правая граница по Re(z)")

        row1.addWidget(QLabel("x_min"))
        row1.addWidget(self.x_min)
        row1.addWidget(QLabel("x_max"))
        row1.addWidget(self.x_max)
        lp.addLayout(row1)

        row2 = QHBoxLayout()
        self.y_min = QDoubleSpinBox()
        self.y_min.setRange(-2000, 2000)
        self.y_min.setDecimals(3)
        self.y_min.setValue(-2.0)
        self.y_min.setToolTip(
            "y_min — нижняя граница по Im(z)")

        self.y_max = QDoubleSpinBox()
        self.y_max.setRange(-2000, 2000)
        self.y_max.setDecimals(3)
        self.y_max.setValue(2.0)
        self.y_max.setToolTip(
            "y_max — верхняя граница по Im(z)")

        row2.addWidget(QLabel("y_min"))
        row2.addWidget(self.y_min)
        row2.addWidget(QLabel("y_max"))
        row2.addWidget(self.y_max)
        lp.addLayout(row2)

        self.chk_square = QCheckBox("Сохранять квадратное окно")
        self.chk_square.setChecked(True)
        self.chk_square.setToolTip("Удобно для симметричных фракталов.")
        lp.addWidget(self.chk_square)

        left_layout.addWidget(g_plane)

        # метод Ньютона (параметры итераций)
        g_newton = QGroupBox("Метод Ньютона")
        ln = QVBoxLayout(g_newton)

        row3 = QHBoxLayout()
        self.max_iter = QSpinBox()
        self.max_iter.setRange(5, 500)
        self.max_iter.setValue(60)
        self.max_iter.setToolTip("При увеличении можно детализировать границы")
        row3.addWidget(QLabel("Макс. итераций:"))
        row3.addWidget(self.max_iter)
        ln.addLayout(row3)

        row4 = QHBoxLayout()
        self.eps_combo = QComboBox()
        self.eps_combo.addItems(["1e-3", "1e-4", "1e-5", "1e-6", "1e-7", "1e-8", "1e-9"])
        self.eps_combo.setCurrentText("1e-6")
        self.eps_combo.setToolTip(
            "eps — критерий сходимости: |f(z)| < eps")
        row4.addWidget(QLabel("Точность (ε):"))
        row4.addWidget(self.eps_combo)
        ln.addLayout(row4)

        row5 = QHBoxLayout()
        self.df_eps_combo = QComboBox()
        self.df_eps_combo.addItems(["1e-10", "1e-12", "1e-14", "1e-16"])
        self.df_eps_combo.setCurrentText("1e-14")
        self.df_eps_combo.setToolTip("Уменьшение df_eps увеличивает риск появления артефактов")
        row5.addWidget(QLabel("Защита производной:"))
        row5.addWidget(self.df_eps_combo)
        ln.addLayout(row5)

        left_layout.addWidget(g_newton)

        # предпросмотр
        g_prev = QGroupBox("Предпросмотр")
        lpr = QVBoxLayout(g_prev)

        self.res_label = QLabel("Плотность вычислений: 700 × 700")
        lpr.addWidget(self.res_label)

        self.res_slider = QSlider(Qt.Horizontal)
        self.res_slider.setRange(1, 2000)
        self.res_slider.setValue(700)
        self.res_slider.setSingleStep(10)
        self.res_slider.setToolTip("Разрешение сетки nx × ny")
        lpr.addWidget(self.res_slider)

        row6 = QHBoxLayout()
        self.view_mode = QComboBox()
        self.view_mode.addItem("Всё", "Both")
        self.view_mode.addItem("Только рельеф", "Heatmap")
        self.view_mode.addItem("Только контуры", "Contours")

        self.cmap = QComboBox()
        self.cmap.addItems(["magma", "viridis", "turbo"])
        self.cmap.setCurrentText("magma")
        self.cmap.setToolTip("Цветовая карта для отображения рельефа")

        row6.addWidget(QLabel("Вид:"))
        row6.addWidget(self.view_mode)
        row6.addSpacing(10)
        row6.addWidget(QLabel("Цветовая карта:"))
        row6.addWidget(self.cmap)
        lpr.addLayout(row6)

        left_layout.addWidget(g_prev)

        # ЧПУ
        g_cnc = QGroupBox("ЧПУ (Mach3)")
        lc = QVBoxLayout(g_cnc)

        row7 = QHBoxLayout()
        self.board_w = QDoubleSpinBox()
        self.board_w.setRange(10, 2000)
        self.board_w.setDecimals(2)

        self.board_h = QDoubleSpinBox()
        self.board_h.setRange(10, 2000)
        self.board_h.setDecimals(2)
        self.board_h.setValue(100.0)

        row7.addWidget(QLabel("Ширина (мм):"))
        row7.addWidget(self.board_w)
        row7.addWidget(QLabel("Высота (мм):"))
        row7.addWidget(self.board_h)
        lc.addLayout(row7)

        row8 = QHBoxLayout()
        self.zmax = QDoubleSpinBox()
        self.zmax.setRange(0.1, 5.0)
        self.zmax.setDecimals(3)
        self.zmax.setValue(2.0)
        self.zmax.setToolTip("Максимальная допустимая глубина резки (мм).\n"
                             "Исходная глубина зависит от количества квантилей уровней изолиний и указанного максимума")

        self.safe_z = QDoubleSpinBox()
        self.safe_z.setRange(3.0, 50.0)
        self.safe_z.setDecimals(3)
        self.safe_z.setValue(5.0)
        self.safe_z.setToolTip("На этой высоте инструмент перемещается между контурами\n"
                               "(должна быть строго выше максимальной глубины резки)")

        row8.addWidget(QLabel("Макс. глубина (мм):"))
        row8.addWidget(self.zmax)
        row8.addWidget(QLabel("Безопасная высота (мм):"))
        row8.addWidget(self.safe_z)
        lc.addLayout(row8)

        row9 = QHBoxLayout()
        self.feed_xy = QSpinBox()
        self.feed_xy.setRange(300, 2000)
        self.feed_xy.setValue(400)
        self.feed_xy.setToolTip("Слишком большая подача может сломать фрезу,\n"
                                "а слишком маленькая приводит к появлению наклёпа")

        self.feed_z = QSpinBox()
        self.feed_z.setRange(200, 2000)
        self.feed_z.setValue(300)
        self.feed_z.setToolTip("Подачу на погружение стоит настраивать медленнее перемещений по XY.\n"
                               "Слишком быстрое погружение может сломать фрезу.")

        row9.addWidget(QLabel("Подача XY (мм/мин):"))
        row9.addWidget(self.feed_xy)
        row9.addWidget(QLabel("Подача Z (мм/мин):"))
        row9.addWidget(self.feed_z)
        lc.addLayout(row9)

        row10 = QHBoxLayout()
        self.spindle = QSpinBox()
        self.spindle.setRange(1000, 12000)
        self.spindle.setValue(4000)
        self.spindle.setToolTip("Обороты шпинделя (RPM).\n"
                                "Точное значение зависит от фрезы и материала.\n"
                                "(Для обработки пластика оборотов и подачи необходимо меньше, чем для дерева).")
        row10.addWidget(QLabel("Обороты шпинделя:"))
        row10.addWidget(self.spindle)
        lc.addLayout(row10)

        row11 = QHBoxLayout()
        self.n_levels = QSpinBox()
        self.n_levels.setRange(1, 30)
        self.n_levels.setValue(6)
        self.n_levels.setToolTip("Количество квантилей уровней изолиний")

        self.min_depth = QDoubleSpinBox()
        self.min_depth.setRange(0.0, 50.0)
        self.min_depth.setDecimals(3)
        self.min_depth.setValue(0.2)
        self.min_depth.setToolTip("Контуры меньше данной глубины не обрабатываются")

        row11.addWidget(QLabel("Кол-во уровней:"))
        row11.addWidget(self.n_levels)
        row11.addWidget(QLabel("Мин. глубина (мм):"))
        row11.addWidget(self.min_depth)
        lc.addLayout(row11)

        row12 = QHBoxLayout()
        self.min_len = QDoubleSpinBox()
        self.min_len.setRange(0.0, 5000.0)
        self.min_len.setDecimals(2)
        self.min_len.setValue(8.0)
        self.min_len.setToolTip("Минимальная длина контура (мм)")
        row12.addWidget(QLabel("Мин. длина контура (мм):"))
        row12.addWidget(self.min_len)
        lc.addLayout(row12)

        # Сглаживание контуров
        row13 = QHBoxLayout()
        self.chk_smooth = QCheckBox("Сглаживать контуры")
        self.chk_smooth.setChecked(True)
        self.chk_smooth.setToolTip("Сглаживание траектории по алгоритму Чайкина")

        self.smooth_strength = QSpinBox()
        self.smooth_strength.setRange(1, 10)
        self.smooth_strength.setValue(2)
        self.smooth_strength.setToolTip("оптимально 2-4")
        row13.addWidget(self.chk_smooth)
        row13.addWidget(QLabel("Сила сглаживания:"))
        row13.addWidget(self.smooth_strength)
        lc.addLayout(row13)

        self.btn_export = QPushButton("Экспортировать G-code")
        self.btn_calc.setToolTip("При изменении параметров в секторе \"ЧПУ\" необходимо сделать пересчёт для обновления"
                                 " параметров в исходном коде")
        self.btn_export.setEnabled(False)
        lc.addWidget(self.btn_export)

        left_layout.addWidget(g_cnc)

        # Строка состояния
        self.status_label = QLabel("Готово")
        self.status_label.setStyleSheet("color:#9fb1c7; padding: 6px;")
        left_layout.addWidget(self.status_label)

        # Фрактал
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        splitter.addWidget(right_container)
        self.canvas = MplCanvas()
        right_layout.addWidget(self.canvas, stretch=5)
        self.stats = QLabel("")
        self.stats.setStyleSheet("color:#cfe0f5; padding: 8px;")
        right_layout.addWidget(self.stats)

        # Сигналы
        self.res_slider.valueChanged.connect(self._on_res_changed)
        self.btn_calc.clicked.connect(self.recalculate)
        self.btn_random.clicked.connect(self.random_polynomial)
        self.btn_export.clicked.connect(self.export_gcode)
        self.poly_edit.textChanged.connect(self.validate_poly_live)

        self.x_min.valueChanged.connect(self._square_sync)
        self.x_max.valueChanged.connect(self._square_sync)
        self.y_min.valueChanged.connect(self._square_sync)
        self.y_max.valueChanged.connect(self._square_sync)

        self.quality_combo.currentIndexChanged.connect(self.apply_quality_profile)
        self.quality_combo.setCurrentIndex(1)
        self.apply_quality_profile()

        # обновление графика без пересчёта
        self.view_mode.currentIndexChanged.connect(self.redraw_if_possible)
        self.cmap.currentIndexChanged.connect(self.redraw_if_possible)
        self.board_w.valueChanged.connect(self.redraw_if_possible)
        self.board_h.valueChanged.connect(self.redraw_if_possible)

        # Инициализация
        self._on_res_changed(self.res_slider.value())
        self.validate_poly_live()

        self.recalculate()

    # UI функции
    def _on_res_changed(self, v: int):
        self.res_label.setText(f"Плотность вычислений: {v} × {v}")

    # Выравниваение диапазона под квадрат
    def _square_sync(self):
        if not self.chk_square.isChecked():
            return

        x_range = self.x_max.value() - self.x_min.value()
        y_range = self.y_max.value() - self.y_min.value()
        target = max(abs(x_range), abs(y_range))

        cx = 0.5 * (self.x_min.value() + self.x_max.value())
        cy = 0.5 * (self.y_min.value() + self.y_max.value())

        self.x_min.blockSignals(True)
        self.x_max.blockSignals(True)
        self.y_min.blockSignals(True)
        self.y_max.blockSignals(True)

        self.x_min.setValue(cx - target / 2)
        self.x_max.setValue(cx + target / 2)
        self.y_min.setValue(cy - target / 2)
        self.y_max.setValue(cy + target / 2)

        self.x_min.blockSignals(False)
        self.x_max.blockSignals(False)
        self.y_min.blockSignals(False)
        self.y_max.blockSignals(False)

    # Полиномы
    def validate_poly_live(self):
        s = self.poly_edit.text().strip()
        if not s:
            self.err_label.setText("Введите функцию, например: z**3 - 1")
            self.btn_calc.setEnabled(False)
            return

        try:
            _expr, _dexpr, _, _ = compile_function(s)
            self.err_label.setText("")
            self.btn_calc.setEnabled(True)
        except Exception as e:
            self.err_label.setText(f"Ошибка ввода: {e}")
            self.btn_calc.setEnabled(False)

    def random_polynomial(self):
        self.poly_edit.setText(numpy.random.choice(polynomials))

    # Профиль качества
    def apply_quality_profile(self):
        key = self.quality_combo.currentData()

        profiles = {"low": {"res": 320,
                            "max_iter": 45,
                            "eps": "1e-5",
                            "df_eps": "1e-12",
                            "n_levels": 4,
                            "min_depth": 0.25,
                            "zmax": 1.5},
                    "medium": {"res": 700,
                               "max_iter": 60,
                               "eps": "1e-6",
                               "df_eps": "1e-14",
                               "n_levels": 6,
                               "min_depth": 0.20,
                               "zmax": 2.0},
                    "high": {"res": 1600,
                             "max_iter": 90,
                             "eps": "1e-8",
                             "df_eps": "1e-16",
                             "n_levels": 10,
                             "min_depth": 0.10,
                             "zmax": 2.5}}

        p = profiles.get(key, profiles["medium"])

        # ставим значения с блокировкой сигналов
        self.res_slider.blockSignals(True)
        self.res_slider.setValue(int(p["res"]))
        self.res_slider.blockSignals(False)
        self._on_res_changed(self.res_slider.value())

        self.max_iter.setValue(int(p["max_iter"]))
        self.eps_combo.setCurrentText(p["eps"])
        self.df_eps_combo.setCurrentText(p["df_eps"])

        self.n_levels.setValue(int(p["n_levels"]))
        self.min_depth.setValue(float(p["min_depth"]))

        # логическая защита на максимумы и минимумы глубины
        zmax_target = float(p["zmax"])
        safe = float(self.safe_z.value())
        zmax_target = min(zmax_target, max(0.1, safe - 0.5))
        self.zmax.setValue(zmax_target)

        self.redraw_if_possible()

    # Подготовка параметров для worker
    def _gather_params(self):
        eps = float(self.eps_combo.currentText())
        df_eps = float(self.df_eps_combo.currentText())
        n = int(self.res_slider.value())
        return {"expr_str": self.poly_edit.text().strip(),

                "x_min": float(self.x_min.value()),
                "x_max": float(self.x_max.value()),
                "y_min": float(self.y_min.value()),
                "y_max": float(self.y_max.value()),

                "nx": n,
                "ny": n,

                "max_iter": int(self.max_iter.value()),
                "eps": eps,
                "df_eps": df_eps,

                "zmax_mm": float(self.zmax.value()),
                "n_levels": int(self.n_levels.value()),
                "min_depth_mm": float(self.min_depth.value())}

    # Пересчёт
    def recalculate(self):
        if not self.btn_calc.isEnabled():
            return

        if self.worker is not None and self.worker.isRunning():
            return

        # логическая защита: диапазон не должен быть вырожденным
        if self.x_max.value() <= self.x_min.value() or self.y_max.value() <= self.y_min.value():
            nice_error("Ошибка диапазона: x_max должно быть большн x_min и y_max должно быть большн y_min.")
            return

        self.btn_calc.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.status_label.setText("Вычисляем…")
        self.stats.setText("")

        params = self._gather_params()

        self.worker = ComputeWorker(params)
        self.worker.done.connect(self._on_compute_done)
        self.worker.fail.connect(self._on_compute_fail)
        self.worker.start()

    # Перерисовка без пересчёта
    def redraw_if_possible(self):
        if not self.last_data:
            return

        data = self.last_data
        hm = data["heightmap_mm"]
        contours_by_level = data["contours_by_level"]
        z_levels = data["z_levels"]

        title = f"f(z) = {data['expr']}   |   Уровни: {len(z_levels)}"
        self.canvas.plot_heatmap_and_contours(heightmap_mm=hm,
                                              contours_by_level=contours_by_level,
                                              view_mode=self.view_mode.currentData(),
                                              cmap=self.cmap.currentText(),
                                              title=title)
        return

    # Обработка ошибки или исполнения при расчёте
    def _on_compute_fail(self, tb: str):
        self.btn_calc.setEnabled(True)
        self.status_label.setText("Ошибка при расчёте")
        nice_error(tb)

    def _on_compute_done(self, data: dict):
        self.last_data = data
        self.btn_calc.setEnabled(True)
        self.btn_export.setEnabled(True)

        hm = data["heightmap_mm"]
        iters = data["iters"]
        z_levels = data["z_levels"]
        contours_by_level = data["contours_by_level"]

        title = f"f(z) = {data['expr']}   |   Уровней: {len(z_levels)}"

        self.canvas.plot_heatmap_and_contours(heightmap_mm=hm,
                                              contours_by_level=contours_by_level,
                                              view_mode=self.view_mode.currentData(),
                                              cmap=self.cmap.currentText(),
                                              title=title)

        depth_min = float(hm.min())
        depth_max = float(hm.max())
        it_min = int(iters.min())
        it_max = int(iters.max())
        it_mean = float(iters.mean())

        total_contours = sum(len(v) for v in contours_by_level.values()) if contours_by_level else 0

        self.stats.setText(f"Итерации: мин={it_min}, макс.={it_max}, ср.={it_mean:.2f}    |    "
                           f"Z(mm): мин.={depth_min:.3f}, макс.={depth_max:.3f}    |    "
                           f"Контуров: {total_contours}    |    Уровни: {', '.join(map(str, map(float, z_levels)))}")

        self.status_label.setText("Предпросмотр обновлён")

    # Экспорт G-code
    def export_gcode(self):
        if not self.last_data:
            return

        # диалог сохранения
        default_name = "newton_contours_mach3.nc"
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить G-code",
                                              default_name, "G-code (*.nc *.tap *.gcode);;All files (*.*)")
        if not path:
            return

        data = self.last_data
        hm = data["heightmap_mm"]
        contours_by_level = data["contours_by_level"]

        # Защита от опасных настроек
        safe_z = float(self.safe_z.value())
        zmax = float(self.zmax.value())
        feed_xy = int(self.feed_xy.value())
        feed_z = int(self.feed_z.value())
        spindle = int(self.spindle.value())

        # безопасная высота должна быть выше максимальной глубины
        if safe_z <= -zmax + 0.2:
            nice_error("Опасные параметры!\n\n"
                       "Рекомендация: безопасная глубина >= максимальная глубина + 1 мм")
            return

        # минимальные значения
        if spindle < 1000:
            nice_error("Обороты шпинделя слишком малы. Минимум: 1000 RPM.")
            return
        if feed_xy < 300:
            nice_error("Подача XY слишком мала. Минимум: 300 мм/мин.")
            return
        if feed_z < 200:
            nice_error("Подача Z слишком мала. Минимум: 200 мм/мин.")
            return

        # Z быстрее XY (предупреждение)
        if feed_z > feed_xy:
            r = QMessageBox.warning(
                self,
                "Предупреждение",
                "Подача по Z выше, чем по XY.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            if r != QMessageBox.Yes:
                return

        # проверка размеров заготовки
        if self.board_w.value() <= 0 or self.board_h.value() <= 0:
            nice_error("Размеры заготовки должны быть > 0.")
            return

        # Экспорт
        try:
            contours_to_gcode_mach3(contours_by_level=contours_by_level,
                                    heightmap_shape=hm.shape,
                                    board_width_mm=float(self.board_w.value()),
                                    board_height_mm=float(self.board_h.value()),
                                    safe_z=float(self.safe_z.value()),
                                    feed_xy=int(self.feed_xy.value()),
                                    feed_z=int(self.feed_z.value()),
                                    spindle_rpm=int(self.spindle.value()),
                                    min_contour_len_mm=float(self.min_len.value()),
                                    smooth_enabled=self.chk_smooth.isChecked(),
                                    smooth_iterations=int(self.smooth_strength.value()),
                                    filename=path)
            self.status_label.setText(f"Экспортировано: {path}")
            QMessageBox.information(self, "Экспорт завершён", f"G-code сохранён:\n{path}")
        except Exception:
            nice_error(traceback.format_exc())
