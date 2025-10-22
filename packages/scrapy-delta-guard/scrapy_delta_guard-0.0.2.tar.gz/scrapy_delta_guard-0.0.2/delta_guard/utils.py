import importlib
import logging
logger = logging.getLogger("delta_guard.utils")

def load_object(path):
    """Import object from a dotted path string. Returns None on failure."""
    if not path:
        return None
    try:
        module_name, attr = path.rsplit(".", 1)
        mod = importlib.import_module(module_name)
        return getattr(mod, attr)
    except Exception:
        logger.exception("Failed to import %s", path)
        return None

def safe_getattr(obj, attr):
    """Safely read attribute `attr` from obj.
    - If obj is dict-like, use dict get.
    - Otherwise try getattr (supports dot-nested attributes: 'a.b')
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(attr)
    # support nested attr path like "a.b"
    parts = str(attr).split(".")
    cur = obj
    for p in parts:
        try:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                cur = getattr(cur, p, None)
        except Exception:
            return None
        if cur is None:
            return None
    return cur
