"""PES Arena Black Box package facade.

The app service binder consumes EXPORTED_NAMES from the package itself, so every
exported service function must also be present on this package object.
"""
from . import service as _service
from .service import EXPORTED_NAMES
from .routes import register_routes


def configure(context):
    _service.configure(context)


for _name in EXPORTED_NAMES:
    globals()[_name] = getattr(_service, _name)


__all__ = ("configure", "register_routes", *EXPORTED_NAMES)
