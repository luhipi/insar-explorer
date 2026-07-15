"""Transactional editor for the session-local Time Series X-axis range."""

from datetime import datetime

from qgis.PyQt.QtCore import QDate, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDateEdit, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout,
)

from ...qt_compat import FRAME_SHAPE_STYLED_PANEL, POPUP_WINDOW_FLAG


class ManualXAxisPopup(QFrame):
    """Anchored transactional editor for a manual time range."""

    applyRequested = pyqtSignal(object, object)
    cancelRequested = pyqtSignal()
    currentViewRequested = pyqtSignal()
    previewRequested = pyqtSignal(object, object)

    def __init__(self, parent=None):
        """Create Start/End date editors and transaction actions."""
        super().__init__(parent, POPUP_WINDOW_FLAG)
        self.setObjectName("popup_manual_x_axis")
        self.setFrameShape(FRAME_SHAPE_STYLED_PANEL)
        self._closing_after_commit = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        title = QLabel("Time range", self)
        title.setObjectName("label_manual_x_axis_title")
        layout.addWidget(title)

        form = QGridLayout()
        self.start_edit = self._dateEditor("Manual X-axis start date")
        self.end_edit = self._dateEditor("Manual X-axis end date")
        form.addWidget(QLabel("Start", self), 0, 0)
        form.addWidget(self.start_edit, 0, 1)
        form.addWidget(QLabel("End", self), 1, 0)
        form.addWidget(self.end_edit, 1, 1)
        layout.addLayout(form)

        self.current_view_button = QPushButton("Use current view", self)
        layout.addWidget(self.current_view_button)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.cancel_button = QPushButton("Cancel", self)
        self.apply_button = QPushButton("Apply", self)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.apply_button)
        layout.addLayout(actions)

        self.start_edit.dateChanged.connect(self._updateState)
        self.end_edit.dateChanged.connect(self._updateState)
        self.cancel_button.clicked.connect(self.close)
        self.apply_button.clicked.connect(self._apply)
        self.current_view_button.clicked.connect(self.currentViewRequested.emit)

    def _dateEditor(self, accessible_name):
        """Create one project-compatible calendar date editor."""
        editor = QDateEdit(self)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("yyyy-MM-dd")
        editor.setAccessibleName(accessible_name)
        return editor

    @staticmethod
    def _toQDate(value):
        """Convert a Python date-like value to QDate."""
        return QDate(value.year, value.month, value.day)

    @staticmethod
    def _toDatetime(value):
        """Convert QDate to a midnight datetime."""
        return datetime(value.year(), value.month(), value.day())

    def openForRange(self, start, end):
        """Load the candidate transaction range without previewing initialization."""
        self.start_edit.blockSignals(True)
        self.end_edit.blockSignals(True)
        try:
            self.start_edit.setDate(self._toQDate(start))
            self.end_edit.setDate(self._toQDate(end))
        finally:
            self.start_edit.blockSignals(False)
            self.end_edit.blockSignals(False)
        self._closing_after_commit = False
        self._updateState(preview=False)

    def range(self):
        """Return the currently edited Python datetime range."""
        return self._toDatetime(self.start_edit.date()), self._toDatetime(self.end_edit.date())

    def _updateState(self, *_args, preview=True):
        """Validate the draft and request a live preview only for valid ranges."""
        start, end = self.range()
        valid = start < end
        self.apply_button.setEnabled(valid)
        if valid and preview:
            self.previewRequested.emit(start, end)

    def _apply(self):
        if not self.apply_button.isEnabled():
            return
        self._closing_after_commit = True
        self.applyRequested.emit(*self.range())
        self.close()

    def closeAfterCommit(self):
        """Close after an immediate commit without emitting Cancel."""
        self._closing_after_commit = True
        self.close()

    def closeEvent(self, event):
        """Treat dismissal and Escape as transaction cancellation."""
        if not self._closing_after_commit:
            self.cancelRequested.emit()
        self._closing_after_commit = False
        super().closeEvent(event)
