import time
import logging
import psycopg2
from threading import Event
from .utils import monitor_resource, get_logger
from .datautils import QueueProducer, ProducerClosedException
from .db import DatabaseManager, DatabaseManagerException

logger = get_logger("worker")

def worker(connection: psycopg2.extensions.connection, producer: QueueProducer, event: Event):
    logger.info("New worker started ...")

    db = DatabaseManager(connection)
    while not event.is_set() and connection.closed == 0:
        try:
            task_params = db.get_next_task()
            if task_params:
                producer.put(
                    monitor_resource(
                        task_params[0], 
                        task_params[1],
                    )
                )
            else:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Exception occured while worker execution {e}.")
    logger.info("Worker finished.")

