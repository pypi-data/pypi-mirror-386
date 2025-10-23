try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings
    warnings.warn("Importing 'jupyter_server_documents' outside a proper installation.")
    __version__ = "dev"


from .app import ServerDocsApp
from .events import JSD_AWARENESS_EVENT_URI, JSD_ROOM_EVENT_URI


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "@jupyter-ai-contrib/server-documents"
    }]


def _jupyter_server_extension_points():
    return [{
        "module": "jupyter_server_documents",
        "app": ServerDocsApp
    }]
