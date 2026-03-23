def classFactory(iface):
    from .export_pat_plugin import ExportPATPlugin
    return ExportPATPlugin(iface)
