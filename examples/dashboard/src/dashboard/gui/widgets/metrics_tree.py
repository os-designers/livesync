from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem


class MetricsTree(QTreeWidget):
    def __init__(self, metrics_list: list[str]):
        super().__init__()

        # Set headers
        self.setHeaderLabels(["Metric", "Value"])  # type: ignore

        # Evenly distribute column widths
        header = self.header()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Initialize tree items
        self._items: dict[str, QTreeWidgetItem] = {}
        for metric in metrics_list:
            item = QTreeWidgetItem(self)
            item.setText(0, metric)
            item.setText(1, "0")  # 초기값
            self._items[metric] = item

        # Set style
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            """
            QTreeWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTreeWidget::item {
                height: 25px;
            }
        """
        )

    def update_data(self, data: dict[str, Any]) -> None:
        """Update multiple metrics at once"""
        for key, value in data.items():
            self._update_data(key, value)

    def _update_data(self, key: str, value: Any):
        """Update a single metric value"""
        if key not in self._items:
            return

        item = self._items[key]

        # Format value based on its type
        if isinstance(value, float):
            formatted_value = f"{value:.6f}"
        else:
            formatted_value = str(value)

        item.setText(1, formatted_value)

        # Example color changes for demonstration
        if "Error" in key and isinstance(value, (int, float)) and value > 0:
            item.setForeground(1, Qt.GlobalColor.red)
        elif "Queue" in key and isinstance(value, (int, float)) and value > 10:
            item.setForeground(1, Qt.GlobalColor.darkYellow)
        else:
            item.setForeground(1, Qt.GlobalColor.black)
