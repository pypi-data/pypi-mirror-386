import logging
import os

import odoo

from . import redis_session

from .redis_config import RedisConfig
from .redis_session import RedisSessionStore

_logger = logging.getLogger("odoo.session.REDIS")

try:
    import redis

    _logger.info("Lib redis installed")
except ImportError:
    redis = None

MAJOR = odoo.release.version_info[0]
if MAJOR >= 16:
    from odoo.http import Session as OdooSessionClass
else:
    from odoo.http import OpenERPSession as OdooSessionClass


@odoo.tools.func.lazy_property
def session_store(self):
    config = RedisConfig.create_config(odoo.tools.config)
    return RedisSessionStore(redis_config=config, session_class=OdooSessionClass)


def _post_load_module():
    if "redis_session_store" not in odoo.conf.server_wide_modules:
        return
    if not redis:
        raise ImportError("Please install package redis")
    redis_config = RedisConfig.create_config(odoo.tools.config)
    server_info = redis_config.connect().info()
    # In case this is a Materia KV Redis compatible database
    if not server_info.get("redis_version") and server_info.get("Materia KV "):
        server_info = {"redis_version": f"Materia KV - {server_info['Materia KV ']}"}
    if not server_info:
        raise ValueError("Can't display server info")
    _logger.info("Redis Session enable [%s]", server_info)
    if MAJOR <= 15.0:
        odoo.http.Root.session_store = session_store
        odoo.http.session_gc = lambda s: None
    elif MAJOR >= 16.0:
        odoo.http.Application.session_store = session_store
        # There is no more session_gc global function.
        # Now See FilesystemSessionStore#vacuum
        # So no more patch need
    from . import patcher
