DARK_QSS = """
QMainWindow, QWidget { background: #0b1220; }
QWidget { font-size: 12px; }

QGroupBox {
    color: #e9eef5;
    border: 1px solid #1c2633;
    border-radius: 14px;
    margin-top: 12px;
    padding: 10px;
    background: #0e141c;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    font-weight: 600;
    color: #e9eef5;
}

QLabel { color: #d6deea; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0b0f14;
    color: #e9eef5;
    border: 1px solid #223042;
    border-radius: 10px;
    padding: 8px;
    selection-background-color: #3b82f6;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #4cc9f0;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #1f2937, stop:1 #111827);
    color: #e9eef5;
    border: 1px solid #223042;
    border-radius: 12px;
    padding: 10px 12px;
    font-weight: 600;
}
QPushButton:hover {
    border: 1px solid #4cc9f0;
}
QPushButton:pressed {
    background: #0b1220;
}
QPushButton:disabled {
    color: #6b7280;
    background: #0e141c;
    border: 1px solid #223042;
}

QComboBox QAbstractItemView {
    background: #0b0f14;
    color: #e9eef5;
    selection-background-color: #3b82f6;
}

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: #0b0f14;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #223042;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #2d3f57; }

QCheckBox { color: #d6deea; }
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}
QCheckBox::indicator:unchecked {
    border: 1px solid #223042;
    border-radius: 6px;
    background: #0b0f14;
}
QCheckBox::indicator:checked {
    border: 1px solid #4cc9f0;
    border-radius: 6px;
    background: #0ea5e9;
}

QSlider::groove:horizontal {
    border: 1px solid #223042;
    height: 8px;
    background: #0b0f14;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: #4cc9f0;
    border: 1px solid #223042;
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
"""