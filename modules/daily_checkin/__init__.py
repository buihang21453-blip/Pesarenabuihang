"""Module điểm danh Zcoin hằng ngày."""

from .service import EXPORTED_NAMES
from . import service as _service
from . import repository as _repository
from .routes import register_routes


def configure(context):
    _repository.configure(context)
    enriched = dict(context)
    for name in EXPORTED_NAMES:
        enriched[name] = getattr(_service, name)
    _service.configure(enriched)


for _name in EXPORTED_NAMES:
    globals()[_name] = getattr(_service, _name)

__all__ = ("configure", "register_routes", *EXPORTED_NAMES)
