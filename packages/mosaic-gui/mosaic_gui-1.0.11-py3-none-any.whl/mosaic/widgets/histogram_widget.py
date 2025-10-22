"""
Variety of widgets used throughout the GUI.

Copyright (c) 2024 European Molecular Biology Laboratory

Author: Valentin Maurer <valentin.maurer@embl-hamburg.de>
"""

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Qt, Signal, QLocale
from qtpy.QtGui import QColor, QDoubleValidator
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSlider,
    QLineEdit,
    QLabel,
    QSpinBox,
    QSizePolicy,
    QComboBox,
    QGridLayout,
)

from ..stylesheets import QSlider_style


class RangeSlider(QWidget):
    """A custom slider that allows selecting a range with two handles."""

    rangeChanged = Signal(float, float)

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.lower_value = 0
        self.upper_value = 100

        layout = (
            QHBoxLayout() if orientation == Qt.Orientation.Horizontal else QVBoxLayout()
        )
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.lower_slider = QSlider(orientation)
        self.upper_slider = QSlider(orientation)

        # Emulate range slider appearance
        self._apply_slider_styles()

        for slider, value, callback in [
            (self.lower_slider, 0, self._lower_slider_changed),
            (self.upper_slider, 100, self._upper_slider_changed),
        ]:
            slider.setRange(0, 100)
            slider.setValue(value)
            slider.valueChanged.connect(callback)
            layout.addWidget(slider)

    def _apply_slider_styles(self):
        """Apply custom styles to achieve right-side coloring for lower slider."""
        lower_slider_style = (
            QSlider_style
            + """
        QSlider::sub-page:horizontal {
            background: #e2e8f0;
            border-radius: 2px;
        }
        QSlider::sub-page:horizontal:disabled {
            background: #f1f5f9;
        }
        QSlider::add-page:horizontal {
            background: #94a3b8;
            border-radius: 2px;
        }
        QSlider::add-page:horizontal:disabled {
            background: #cbd5e1;
        }
        """
        )

        upper_slider_style = (
            QSlider_style
            + """
        QSlider::sub-page:horizontal {
            background: #94a3b8;
            border-radius: 2px;
        }
        QSlider::sub-page:horizontal:disabled {
            background: #cbd5e1;
        }
        QSlider::add-page:horizontal {
            background: #e2e8f0;
            border-radius: 2px;
        }
        QSlider::add-page:horizontal:disabled {
            background: #f1f5f9;
        }
        """
        )

        self.lower_slider.setStyleSheet(lower_slider_style)
        self.upper_slider.setStyleSheet(upper_slider_style)

    def _lower_slider_changed(self, value):
        if value > self.upper_slider.value():
            self.lower_slider.setValue(self.upper_slider.value())
            return

        self.lower_value = value
        self.rangeChanged.emit(self.lower_value, self.upper_value)

    def _upper_slider_changed(self, value):
        if value < self.lower_slider.value():
            self.upper_slider.setValue(self.lower_slider.value())
            return

        self.upper_value = value
        self.rangeChanged.emit(self.lower_value, self.upper_value)

    def setRange(self, minimum, maximum):
        self.lower_slider.setRange(minimum, maximum)
        self.upper_slider.setRange(minimum, maximum)

    def setValues(self, lower, upper):
        # Block signals to avoid triggering callbacks
        for slider, value in [(self.lower_slider, lower), (self.upper_slider, upper)]:
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)

        self.lower_value = lower
        self.upper_value = upper


class HistogramWidget(QWidget):
    cutoff_changed = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.data = []
        self.min_value = 0
        self.max_value = 1
        self.bin_count = 20

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.histogram_plot = pg.PlotWidget()
        self.histogram_plot.setBackground(None)
        self.histogram_plot.getAxis("left").setPen(pg.mkPen(color=(0, 0, 0)))
        self.histogram_plot.getAxis("bottom").setPen(pg.mkPen(color=(0, 0, 0)))
        self.histogram_plot.setLabel("left", "Count")
        self.histogram_plot.setLabel("bottom", "Cluster Size")
        self.histogram_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        controls_layout = self._create_controls()
        self.lower_cutoff_line, self.upper_cutoff_line = self._create_cutoff_lines()

        self.range_slider = RangeSlider(Qt.Orientation.Horizontal)
        self.range_slider.rangeChanged.connect(self._on_slider_range_changed)
        self.range_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.range_slider.setMinimumHeight(30)
        self.range_slider.setRange(0, 100)

        main_layout.addWidget(self.histogram_plot)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.range_slider)

    def _create_cutoff_lines(self):
        line_configs = [
            {
                "color": QColor(70, 130, 180),
                "callback": lambda: self._handle_cutoff_drag(is_lower=True),
            },
            {
                "color": QColor(220, 70, 70),
                "callback": lambda: self._handle_cutoff_drag(is_lower=False),
            },
        ]

        lines = []
        for config in line_configs:
            line = pg.InfiniteLine(
                angle=90,
                movable=True,
                pen=pg.mkPen(config["color"], width=2, style=Qt.PenStyle.DotLine),
            )
            line.sigDragged.connect(config["callback"])
            self.histogram_plot.addItem(line)
            lines.append(line)

        return lines

    def _create_controls(self):
        """Create all control widgets and layouts"""
        controls_layout = QGridLayout()
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.min_value_input = QLineEdit()
        self.max_value_input = QLineEdit()
        self.transform_combo = QComboBox()
        self.bin_count_spinner = QSpinBox()

        widget_width = 80
        for widget in [
            self.min_value_input,
            self.max_value_input,
            self.transform_combo,
            self.bin_count_spinner,
        ]:
            widget.setMinimumWidth(widget_width)

        validator = QDoubleValidator()
        validator.setLocale(QLocale.c())
        self.min_value_input.setValidator(validator)
        self.max_value_input.setValidator(validator)

        self.transform_combo.addItems(["Linear", "Log"])
        self.transform_combo.currentTextChanged.connect(self._draw_histogram)

        self.bin_count_spinner.setRange(5, 100)
        self.bin_count_spinner.setValue(self.bin_count)
        self.bin_count_spinner.valueChanged.connect(self._on_bin_count_changed)

        self.min_value_input.editingFinished.connect(
            lambda: self._handle_input_change(is_lower=True)
        )
        self.max_value_input.editingFinished.connect(
            lambda: self._handle_input_change(is_lower=False)
        )

        controls_layout.addWidget(
            QLabel("Transform:"), 0, 0, Qt.AlignmentFlag.AlignRight
        )
        controls_layout.addWidget(self.transform_combo, 0, 1)
        controls_layout.addWidget(QLabel("Bins:"), 0, 3, Qt.AlignmentFlag.AlignRight)
        controls_layout.addWidget(self.bin_count_spinner, 0, 4)

        controls_layout.addWidget(
            QLabel("Min Value:"), 1, 0, Qt.AlignmentFlag.AlignRight
        )
        controls_layout.addWidget(self.min_value_input, 1, 1)
        controls_layout.addWidget(
            QLabel("Max Value:"), 1, 3, Qt.AlignmentFlag.AlignRight
        )
        controls_layout.addWidget(self.max_value_input, 1, 4)

        return controls_layout

    def update_histogram(self, data):
        """Update the histogram with new data"""
        self.data = np.asarray(data)

        if self.data.size == 0:
            try:
                return self.plot_widget.clear()
            except Exception:
                return None
        return self._draw_histogram()

    def _invert_scaling(self, value):
        if self.transform_combo.currentText().lower() == "log":
            return 10**value
        return value

    def _draw_histogram(self):
        self.histogram_plot.clear()

        data = self.data
        log_scale = self.transform_combo.currentText().lower() == "log"
        if log_scale:
            data = np.log10(self.data[self.data > 0])

        self.min_value = data.min() - 1
        self.max_value = data.max() + 1
        self._update_cutoff_values(self.min_value, None)

        y, x = np.histogram(data, bins=self.bin_count)
        bar_graph = pg.BarGraphItem(
            x=x[:-1],
            height=y,
            width=(x[1] - x[0]) * 0.8,
            brush=QColor(70, 130, 180),
        )
        self.histogram_plot.addItem(bar_graph)

        self.histogram_plot.addItem(self.lower_cutoff_line)
        self.histogram_plot.addItem(self.upper_cutoff_line)

        label = "Cluster Size" + (" (log scale)" if log_scale else "")
        self.histogram_plot.setLabel("bottom", label)

    def _update_cutoff_values(self, lower_value=None, upper_value=None):
        """Central method to update cutoff values and propagate changes to all UI elements."""
        if lower_value is None:
            lower_value = self.lower_cutoff_line.value()
        if upper_value is None:
            upper_value = self.upper_cutoff_line.value()

        range_span = self.max_value - self.min_value
        if range_span <= 0:
            return None

        lower_value = max(lower_value, self.min_value)
        upper_value = min(max(upper_value, lower_value), self.max_value)

        lower_percent = int(((lower_value - self.min_value) / range_span) * 100)
        upper_percent = int(((upper_value - self.min_value) / range_span) * 100)

        block_elements = [
            self.lower_cutoff_line,
            self.upper_cutoff_line,
            self.range_slider,
            self.min_value_input,
            self.max_value_input,
        ]

        for element in block_elements:
            element.blockSignals(True)

        self.lower_cutoff_line.setValue(lower_value)
        self.upper_cutoff_line.setValue(upper_value)

        locale = QLocale.c()
        self.min_value_input.setText(locale.toString(float(lower_value), "d"))
        self.max_value_input.setText(locale.toString(float(upper_value), "d"))
        self.range_slider.setValues(lower_percent, upper_percent)

        for element in block_elements:
            element.blockSignals(False)

        self.cutoff_changed.emit(
            self._invert_scaling(lower_value), self._invert_scaling(upper_value)
        )

    def _on_slider_range_changed(self, lower_percent, upper_percent):
        """Handle range slider value changes."""
        range_span = self.max_value - self.min_value
        lower_value = self.min_value + (lower_percent / 100.0) * range_span
        upper_value = self.min_value + (upper_percent / 100.0) * range_span
        self._update_cutoff_values(lower_value, upper_value)

    def _handle_cutoff_drag(self, is_lower):
        """Handle dragging of cutoff lines."""
        line = self.lower_cutoff_line if is_lower else self.upper_cutoff_line
        if is_lower:
            self._update_cutoff_values(lower_value=line.value())
        else:
            self._update_cutoff_values(upper_value=line.value())

    def _handle_input_change(self, is_lower):
        """Handle changes to either min/max input field."""
        try:
            input_field = self.min_value_input if is_lower else self.max_value_input
            locale = QLocale.c()
            value = locale.toDouble(input_field.text())[0]

            if is_lower:
                return self._update_cutoff_values(lower_value=value)
            return self._update_cutoff_values(upper_value=value)

        except (ValueError, AttributeError):
            line = self.lower_cutoff_line if is_lower else self.upper_cutoff_line
            input_field.setText(str(int(line.value())))

    def _on_bin_count_changed(self, value):
        """Update the number of bins used in the histogram"""
        self.bin_count = value
        self._draw_histogram()
