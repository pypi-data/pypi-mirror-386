"""
DeltaGuard core logic.

Features:
- List-of-dict `DELTA_GUARD_FIELDS_CONFIG`
- Global default threshold `DELTA_GUARD_DEFAULT_THRESHOLD`
- Batch counting `DELTA_GUARD_BATCH_SIZE`
- Boolean none-ignore policies
- Optional runtime DB object and Jira callback
"""

import logging
import asyncio
from collections import defaultdict
from .utils import safe_getattr, load_object

logger = logging.getLogger("delta_guard.core")

class DeltaGuardCore:
    def __init__(self, settings):
        self.enabled = bool(settings.get("DELTA_GUARD_ENABLED", True))
        self.fields_config = settings.get("DELTA_GUARD_FIELDS_CONFIG", [])
        self.default_threshold = float(settings.get("DELTA_GUARD_DEFAULT_THRESHOLD", 1.0))
        self.batch_size = int(settings.get("DELTA_GUARD_BATCH_SIZE", 100))
        self.db_none_ignore = bool(settings.get("DELTA_GUARD_DB_NONE_IGNORE", False))
        self.spider_none_ignore = bool(settings.get("DELTA_GUARD_SPIDER_NONE_IGNORE", False))
        self.db_object = settings.get("DELTA_GUARD_DB_OBJECT", None)
        self.jira_func = load_object(settings.get("DELTA_GUARD_JIRA_FUNC"))
        self._lock = asyncio.Lock()
        self._reset_counters()

    def _reset_counters(self):
        self.total_checked = defaultdict(int)
        self.total_changed = defaultdict(int)
        self.processed = 0

    def _resolve_db_value(self, item, cfg):
        db_key = cfg.get("db_key") or cfg.get("db_attr")
        if db_key:
            cur = item
            for p in str(db_key).split("."):
                cur = cur.get(p) if isinstance(cur, dict) else getattr(cur, p, None)
                if cur is None:
                    break
            return cur

        db_obj = self.db_object
        if db_obj is not None:
            attr = cfg.get("db_attr") or cfg.get("name")
            return safe_getattr(db_obj, attr)

        old_data = item.get("__old_data", {})
        if isinstance(old_data, dict):
            return old_data.get(cfg.get("name"))
        return item.get(cfg.get("name"))

    def _resolve_spider_value(self, item, cfg):
        key = cfg.get("spider_key") or cfg.get("spider_attr") or cfg.get("name")
        cur = item
        for p in str(key).split("."):
            cur = cur.get(p) if isinstance(cur, dict) else getattr(cur, p, None)
            if cur is None:
                break
        return cur

    def _compute_delta(self, old_val, new_val, db_none_ignore, spider_none_ignore):
        if old_val is None and db_none_ignore:
            return None
        if new_val is None and spider_none_ignore:
            return None
        try:
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                denom = max(abs(old_val), 1)
                return abs(old_val - new_val) / denom
        except Exception:
            return 0.0
        return 0.0 if old_val == new_val else 1.0

    async def process_item(self, item, spider=None):
        if not self.enabled:
            return True, {"reason": "disabled"}

        async with self._lock:
            for cfg in self.fields_config:
                name = cfg.get("name")
                if not name:
                    continue
                db_none_ignore = bool(cfg.get("db_none_ignore", self.db_none_ignore))
                spider_none_ignore = bool(cfg.get("spider_none_ignore", self.spider_none_ignore))

                old_val = self._resolve_db_value(item, cfg)
                new_val = self._resolve_spider_value(item, cfg)
                delta = self._compute_delta(old_val, new_val, db_none_ignore, spider_none_ignore)
                if delta is None:
                    continue

                self.total_checked[name] += 1
                if delta != 0:
                    self.total_changed[name] += 1
                    logger.info("Delta detected for %s: %.2f%%", name, delta * 100)

            self.processed += 1
            if self.processed >= self.batch_size:
                exceeded = []
                for cfg in self.fields_config:
                    name = cfg.get("name")
                    checked = self.total_checked.get(name, 0)
                    changed = self.total_changed.get(name, 0)
                    avg_change = (changed / checked) if checked else 0.0
                    threshold = float(cfg.get("threshold", self.default_threshold))
                    if avg_change > threshold:
                        exceeded.append({
                            "field": name,
                            "avg": avg_change,
                            "threshold": threshold,
                            "checked": checked,
                            "changed": changed
                        })
                self._reset_counters()
                if exceeded:
                    msg = "; ".join(
                        f"{e['field']} avg={e['avg']:.2%} thr={e['threshold']:.2%}" for e in exceeded
                    )
                    logger.error("DeltaGuard exceeded: %s", msg)
                    if self.jira_func:
                        try:
                            self.jira_func(title="Data Drift", description=msg)
                        except Exception:
                            logger.exception("jira_func failed")
                    if spider and hasattr(spider, "crawler"):
                        try:
                            spider.crawler.engine.close_spider(spider, reason=f"DeltaGuard: {msg}")
                        except Exception:
                            logger.exception("close_spider failed")
                    return False, {"exceeded": exceeded}
            return True, {}
