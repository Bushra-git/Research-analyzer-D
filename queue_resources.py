"""Lightweight RQ/Redis wiring.

This module must not import the heavy Flask app, dataset, or ML model.
It exists so RQ workers can import queue/connection without re-running
app.py import-time side effects.
"""

import os

from redis import Redis
from rq import Queue


redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_connection = Redis.from_url(redis_url)

# Queue name used by app.py
analysis_queue = Queue("analysis", connection=redis_connection)

