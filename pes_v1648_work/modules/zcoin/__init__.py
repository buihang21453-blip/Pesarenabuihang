"""Module Zcoin độc lập: service, route và dữ liệu quản trị."""

from .service import EXPORTED_NAMES
from . import service as _service
from . import admin as _admin
from .routes import register_routes


def configure(context):
    _service.configure(context)
    enriched = dict(context)
    for name in EXPORTED_NAMES:
        enriched[name] = getattr(_service, name)
    _admin.configure(enriched)


def build_admin_context(players, actor):
    return _admin.build_admin_context(players, actor)


for _name in EXPORTED_NAMES:
    globals()[_name] = getattr(_service, _name)

__all__ = ("configure", "register_routes", "build_admin_context", *EXPORTED_NAMES)
