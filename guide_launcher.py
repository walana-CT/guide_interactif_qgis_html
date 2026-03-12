# -*- coding: utf-8 -*-
"""Dock widget for launching HTML guides in external browser."""

import os

from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QBrush, QColor, QDesktopServices, QFont
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class GuideLauncherDockWidget(QDockWidget):
    """Dock widget listing available local HTML guides, grouped by subdirectory."""

    def __init__(self, plugin_dir, parent=None):
        super(GuideLauncherDockWidget, self).__init__("Guides QGIS", parent)
        self.plugin_dir = plugin_dir
        self.guides_dir = os.path.join(self.plugin_dir, "web", "guides")

        container = QWidget(self)
        layout = QVBoxLayout(container)

        title = QLabel("Guides QGIS ONF")
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)

        description = QLabel(
            "Le guide va s'ouvrir dans votre navigateur WEB."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.search_bar = QLineEdit(container)
        self.search_bar.setPlaceholderText("Rechercher un guide...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._filter_guides)
        layout.addWidget(self.search_bar)

        self.guide_tree = QTreeWidget(container)
        self.guide_tree.setHeaderHidden(True)
        self.guide_tree.setIndentation(18)
        self.guide_tree.itemDoubleClicked.connect(self.open_selected_guide)
        layout.addWidget(self.guide_tree)

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
        self.search_bar.clear()
        self.guide_tree.clear()
        structure = self._discover_guides()
        total = 0

        for category, guide_paths in sorted(structure.items()):
            # Category header item (not selectable)
            cat_item = QTreeWidgetItem(self.guide_tree)
            cat_item.setText(0, self._format_name(category))
            cat_item.setFlags(Qt.ItemIsEnabled)  # not selectable
            cat_font = QFont()
            cat_font.setBold(True)
            cat_item.setFont(0, cat_font)
            cat_item.setForeground(0, QBrush(QColor("#4e9a3a")))

            for guide_path in sorted(guide_paths):
                guide_item = QTreeWidgetItem(cat_item)
                has_video = self._has_video(guide_path)
                label = self._format_name(
                    os.path.splitext(os.path.basename(guide_path))[0]
                )
                if has_video:
                    label = "[vidéo] " + label
                guide_item.setText(0, label)
                guide_item.setData(0, Qt.UserRole, guide_path)
                if has_video:
                    guide_item.setToolTip(0, "Ce guide contient une vidéo")
                total += 1

            cat_item.setExpanded(True)

        has_guides = total > 0
        self.open_button.setEnabled(has_guides)
        if has_guides:
            self.status_label.setText("{} guide(s) disponible(s)".format(total))
        else:
            self.status_label.setText(
                "Aucun guide HTML trouvé. Ajoute des fichiers .html dans web/guides/<categorie>/."
            )

    def open_selected_guide(self, item=None):
        selected_item = item or self.guide_tree.currentItem()
        if selected_item is None:
            QMessageBox.information(self, "Aucun guide", "Sélectionne d'abord un guide.")
            return

        guide_path = selected_item.data(0, Qt.UserRole)
        if not guide_path:
            # User clicked a category header — try to expand/collapse it
            selected_item.setExpanded(not selected_item.isExpanded())
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(guide_path))

    def _discover_guides(self):
        """Return a dict {category_name: [list of html paths]}.

        A category is a direct subdirectory of guides_dir that contains .html files.
        HTML files directly at the root of guides_dir are grouped under 'Général'.
        """
        structure = {}

        if not os.path.isdir(self.guides_dir):
            return structure

        for entry in sorted(os.listdir(self.guides_dir)):
            full_path = os.path.join(self.guides_dir, entry)

            if os.path.isdir(full_path):
                html_files = [
                    os.path.join(full_path, f)
                    for f in sorted(os.listdir(full_path))
                    if f.lower().endswith(".html")
                ]
                if html_files:
                    structure[entry] = html_files

            elif os.path.isfile(full_path) and entry.lower().endswith(".html"):
                structure.setdefault("Général", []).append(full_path)

        return structure

    def _filter_guides(self, text):
        """Show only guide items whose title contains the search text."""
        query = text.strip().lower()

        for i in range(self.guide_tree.topLevelItemCount()):
            cat_item = self.guide_tree.topLevelItem(i)
            visible_children = 0

            for j in range(cat_item.childCount()):
                guide_item = cat_item.child(j)
                match = query in guide_item.text(0).lower()
                guide_item.setHidden(not match)
                if match:
                    visible_children += 1

            # hide category only if no child matches and search is active
            cat_item.setHidden(bool(query) and visible_children == 0)
            if visible_children > 0:
                cat_item.setExpanded(True)

    @staticmethod
    def _has_video(html_path):
        """Return True if the HTML file declares guide-features=video in its <head>."""
        try:
            with open(html_path, "r", encoding="utf-8", errors="ignore") as fh:
                for _ in range(20):
                    line = fh.readline()
                    if not line:
                        break
                    if 'guide-features' in line and 'video' in line:
                        return True
        except OSError:
            pass
        return False

    @staticmethod
    def _format_name(raw):
        return raw.replace("_", " ").title()