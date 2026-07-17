import os

from rq import Worker

from app import analysis_queue, redis_connection


if __name__ == "__main__":
    worker = Worker([analysis_queue], connection=redis_connection, name=os.getenv("RQ_WORKER_NAME", "analysis-worker"))
    worker.work()