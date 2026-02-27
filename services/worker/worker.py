import os

from redis import Redis
from rq import Connection, Queue, Worker


def main() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    conn = Redis.from_url(redis_url)
    with Connection(conn):
        worker = Worker([Queue("default")])
        worker.work()


if __name__ == "__main__":
    main()
