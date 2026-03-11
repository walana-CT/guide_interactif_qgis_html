# -*- coding: utf-8 -*-
"""Dock widget for launching HTML guides in external browser."""

import os

from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GuideLauncherDockWidget(QDockWidget):
    """Dock widget listing available local HTML guides."""

    def __init__(self, plugin_dir, parent=None):
        super(GuideLauncherDockWidget, self).__init__("Guides interactifs", parent)
        self.plugin_dir = plugin_dir
        self.guides_dir = os.path.join(self.plugin_dir, "web", "guides")

        container = QWidget(self)
        layout = QVBoxLayout(container)

        title = QLabel("Choisir un guide HTML")
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)

        description = QLabel(
            "Le guide s'ouvre dans une fenêtre indépendante pour laisser QGIS utilisable."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.guide_list = QListWidget(container)
        self.guide_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.guide_list.itemDoubleClicked.connect(self.open_selected_guide)
        layout.addWidget(self.guide_list)

        button_row = QHBoxLayout()
        self.open_button = QPushButton("Ouvrir le guide", container)
        self.refresh_button = QPushButton("Actualiser", container)
        self.open_button.clicked.connect(self.open_selected_guide)
        self.refresh_button.clicked.connect(self.reload_guides)
        button_row.addWidget(self.open_button)
        button_row.addWidget(self.refresh_button)
        layout.addLayout(button_row)

        self.status_label = QLabel(container)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.setWidget(container)
        self.reload_guides()

    def reload_guides(self):
        self.guide_list.clear()
        guide_paths = self._discover_guides()

        for guide_path in guide_paths:
            item = QListWidgetItem(self._format_guide_name(guide_path))
            item.setData(Qt.UserRole, guide_path)
            self.guide_list.addItem(item)

        has_guides = bool(guide_paths)
        self.open_button.setEnabled(has_guides)
        if has_guides:
            self.guide_list.setCurrentRow(0)
            self.status_label.setText(
                "{0} guide(s) disponible(s) dans {1}".format(
                    len(guide_paths), self.guides_dir
                )
            )
        else:
            self.status_label.setText(
                "Aucun guide HTML trouvé. Ajoute des fichiers .html dans le dossier web/guides."
            )

    def open_selected_guide(self, item=None):
        selected_item = item or self.guide_list.currentItem()
        if selected_item is None:
            QMessageBox.information(
                self,
                "Aucun guide",
                "Sélectionne d'abord un guide dans la liste."
            )
            return

        guide_path = selected_item.data(Qt.UserRole)
        # Open the HTML file directly in the default web browser
        file_url = QUrl.fromLocalFile(guide_path)
        QDesktopServices.openUrl(file_url)

    def _discover_guides(self):
        if not os.path.isdir(self.guides_dir):
            return []

        guide_paths = []
        for entry in sorted(os.listdir(self.guides_dir)):
            full_path = os.path.join(self.guides_dir, entry)
            if os.path.isfile(full_path) and entry.lower().endswith(".html"):
                guide_paths.append(full_path)

        return guide_paths

    @staticmethod
    def _format_guide_name(guide_path):
        filename = os.path.splitext(os.path.basename(guide_path))[0]
        return filename.replace("_", " ").title()