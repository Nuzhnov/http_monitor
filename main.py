import logging.config
import os
import logging
import signal

import psycopg2
from threading import Event
from multiprocessing import Queue
from concurrent.futures import ThreadPoolExecutor
from src.utils import get_logger
from src.datautils import QueueProducer, QueueConsumer
from src.db import DatabaseManager
from src.worker import worker
from src.exporter import ResultsExporter

logger = get_logger("main")

def main():
    db_host = os.getenv("DB_HOST") 
    db_port = os.getenv("DB_PORT", 5432)
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PWD")
    db_name = os.getenv("DB_NAME")
    batch_interval = os.getenv("BATCH_INTERVAL", 60)
    batch_size = os.getenv("BATCH_SIZE", 100)
    num_workers = os.getenv("NUM_WORKERS", 10)

    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        sslmode="require"
    )

    results_queue = Queue()
    thread_pool = ThreadPoolExecutor(max_workers=num_workers)
    exporter = ResultsExporter(
        results_consumer=QueueConsumer(results_queue),
        db_manager=DatabaseManager(conn),
        batch_size=batch_size,
        batch_interval=batch_interval
    )
    event = Event()

    def stop(signum, frame):
        event.set()
        thread_pool.shutdown()
        logger.info("Thread pool stopped.")
        exporter.stop()
        exporter.join()
        logger.info("Metrics exporter stopped.")
        results_queue.close()
        logger.info("Results queue closed.")
        conn.close()
        logger.info("Database connection closed.")
        logger.info("Monitoring finished.")
    
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    for _ in range(num_workers):
        thread_pool.submit(worker, conn, QueueProducer(results_queue), event)
    exporter.start()
    logger.info("Monitoring started.")


if __name__ == "__main__":
    main()
