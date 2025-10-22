from scrapy.exceptions import CloseSpider
import asyncio
import logging
from .core import DeltaGuardCore

logger = logging.getLogger("delta_guard.pipeline")

class DeltaGuardAdapterPipeline:
    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        obj.crawler = crawler
        obj.settings = crawler.settings
        obj.core = DeltaGuardCore(crawler.settings)
        obj._loop = None
        obj.user_pipelines = []
        pipelines = crawler.settings.getdict("ITEM_PIPELINES", {})
        for path, order in sorted(pipelines.items(), key=lambda x: x[1]):
            if path.startswith("delta_guard"):
                continue
            try:
                parts = path.split(".")
                module = __import__(".".join(parts[:-1]), fromlist=[parts[-1]])
                clsobj = getattr(module, parts[-1])
                inst = clsobj.from_crawler(crawler) if hasattr(clsobj, "from_crawler") else clsobj()
                obj.user_pipelines.append(inst)
            except Exception:
                logger.exception("Failed to instantiate pipeline %s", path)
        return obj

    def _ensure_loop(self):
        if self._loop:
            return self._loop
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def process_item(self, item, spider):
        for up in self.user_pipelines:
            try:
                item = up.process_item(item, spider)
            except Exception:
                logger.exception("User pipeline error: %s", up.__class__.__name__)
        loop = self._ensure_loop()
        coro = self.core.process_item(item, spider)
        if loop.is_running():
            ok, info = asyncio.run_coroutine_threadsafe(coro, loop).result()
        else:
            ok, info = loop.run_until_complete(coro)
        if not ok:
            raise CloseSpider(info)
        return item
