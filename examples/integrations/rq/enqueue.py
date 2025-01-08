from time import sleep

from redis import Redis
from rq import Queue
from tasks import hello_world

if __name__ == "__main__":
    connection = Redis()
    queue = Queue(
        name="default",
        connection=connection,
    )
    job = queue.enqueue(hello_world)

    res = job.result
    while not res:
        res = job.result
        sleep(1)
    print(res)
