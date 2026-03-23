import os
from qgis.PyQt.QtWidgets import (
    QDialog, QFileDialog, QVBoxLayout, QPushButton,
    QComboBox, QLineEdit, QLabel, QCheckBox, QScrollArea, QWidget, QMessageBox
)
from qgis.core import QgsProject, QgsMapLayerType
from qgis import processing

class ExportPATDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAT_export")

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Seleziona layer da esportare:"))

        self.layer_checks = []
        container = QWidget()
        container_layout = QVBoxLayout()

        layers = QgsProject.instance().mapLayers().values()
        for l in layers:
            if l.type() == QgsMapLayerType.VectorLayer:
                chk = QCheckBox(l.name())
                chk.layer = l
                self.layer_checks.append(chk)
                container_layout.addWidget(chk)

        container.setLayout(container_layout)

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        layout.addWidget(QLabel("Layer maschera (opzionale):"))
        self.combo_mask = QComboBox()
        self.combo_mask.addItem("Nessuna maschera", None)

        for l in layers:
            if l.type() == QgsMapLayerType.VectorLayer:
                self.combo_mask.addItem(l.name(), l)

        layout.addWidget(self.combo_mask)

        layout.addWidget(QLabel("Cartella root (PAT):"))
        self.txt_folder = QLineEdit()
        layout.addWidget(self.txt_folder)

        btn_folder = QPushButton("Seleziona cartella")
        btn_folder.clicked.connect(self.select_folder)
        layout.addWidget(btn_folder)

        btn_run = QPushButton("Esegui export")
        btn_run.clicked.connect(self.run_export)
        layout.addWidget(btn_run)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Cartella root PAT")
        self.txt_folder.setText(folder)

    def get_original_name(self, layer):
        source = layer.source()
        if '|layername=' in source:
            return source.split('|layername=')[1]
        return os.path.splitext(os.path.basename(source))[0]

    def get_output_folder(self, base_name, root):
        prefix = base_name[:5]

        # ricerca ricorsiva
        for dirpath, dirnames, filenames in os.walk(root):
            for dirname in dirnames:
                if dirname[:5] == prefix:
                    return os.path.join(dirpath, dirname)

        return root

    def run_export(self):

        root = self.txt_folder.text()

        if not root:
            QMessageBox.warning(self, "Errore", "Seleziona una cartella root")
            return

        selected_layers = [chk.layer for chk in self.layer_checks if chk.isChecked()]

        if not selected_layers:
            QMessageBox.warning(self, "Errore", "Seleziona almeno un layer")
            return

        mask = self.combo_mask.currentData()

        ok = 0
        errori = 0
        fallback = set()

        for layer in selected_layers:
            try:
                base = self.get_original_name(layer)
                out_folder = self.get_output_folder(base, root)

                if out_folder == root:
                    fallback.add(base[:5])

                out_path = os.path.join(out_folder, f"{base}.shp")

                if mask:
                    res = processing.run("native:clip", {
                        'INPUT': layer,
                        'OVERLAY': mask,
                        'OUTPUT': 'memory:'
                    })
                    data = res['OUTPUT']
                else:
                    data = layer

                fixed = processing.run("native:fixgeometries", {
                    'INPUT': data,
                    'OUTPUT': 'memory:'
                })['OUTPUT']

                processing.run("native:savefeatures", {
                    'INPUT': fixed,
                    'OUTPUT': out_path
                })

                ok += 1

            except Exception as e:
                errori += 1
                print(f"Errore su {layer.name()}: {e}")

        msg = f"Export completato\nOK: {ok}\nErrori: {errori}"

        if fallback:
            msg += "\n\nPrefissi non trovati (salvati in root):\n" + ", ".join(sorted(fallback))

        QMessageBox.information(self, "Completato", msg)
