import asyncio
from delta_guard.core import DeltaGuardCore

async def test_core():
    settings = {
        "DELTA_GUARD_ENABLED": True,
        "DELTA_GUARD_FIELDS_CONFIG": [
            {"name": "phone", "threshold": 0.1, "db_key": "__old_data.phone", "spider_key": "phone"},
            {"name": "email", "threshold": 0.5, "db_key": "__old_data.email", "spider_key": "email"}
        ],
        "DELTA_GUARD_BATCH_SIZE": 2,
        "DELTA_GUARD_DB_NONE_IGNORE": True,
        "DELTA_GUARD_SPIDER_NONE_IGNORE": False,
    }
    core = DeltaGuardCore(settings)
    class DummySpider:
        name = "demo"
        crawler = type('c', (), {'engine': type('e', (), {'close_spider': lambda s, reason: print('closed', reason)})()})
    spider = DummySpider()
    item1 = {"phone": "111", "email": "a@x.com", "__old_data": {"phone": "222", "email": "a@x.com"}}
    print(await core.process_item(item1, spider))
    item2 = {"phone": "333", "email": "b@x.com", "__old_data": {"phone": "222", "email": "a@x.com"}}
    print(await core.process_item(item2, spider))

asyncio.run(test_core())
