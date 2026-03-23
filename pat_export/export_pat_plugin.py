from qgis.PyQt.QtWidgets import QAction
from .export_pat_dialog import ExportPATDialog

class ExportPATPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction("PAT_export", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        dlg = ExportPATDialog()
        dlg.exec_()
