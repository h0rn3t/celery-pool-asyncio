Celery Pool AsyncIO
===============

* Free software: Apache Software License 2.0

Features
--------


```
import asyncio
from celery import Celery

app = Celery()


@app.task(
    bind=True,
    soft_time_limit=None,  # temporary unimplemented. You can help me
    time_limit=300,
)
async def my_task(self, *args, **kwargs):
    await asyncio.sleep(5)


@app.task
async def my_simple_task(*args, **kwargs):
    await asyncio.sleep(5)
```

