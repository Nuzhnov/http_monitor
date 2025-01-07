import time
import logging
from threading import Thread, Event
from typing import List
from .models import ResultRecord
from .db import DatabaseManager, DatabaseManagerException
from .datautils import QueueConsumer, ConsumerClosedException, ConsumerEmptyException
from .utils import get_logger

logger = get_logger("exporter")


class BatchingStrategy:
    def __init__(self, batch_size: int = 100, batch_interval: int = 60):        
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.current_batch = []
        self.last_flush_time = time.time()

    def add(self, result: ResultRecord) -> bool:
        self.current_batch.append(result)
        
        if self.batch_size and len(self.current_batch) >= self.batch_size:
            return True
            
        if self.batch_interval and (time.time() - self.last_flush_time) >= self.batch_interval:
            return True
            
        return False
    
    def get_batch(self) -> List[ResultRecord]:
        batch = self.current_batch
        logger.info(f"Going to export {len(batch)} records")
        self.current_batch = []
        self.last_flush_time = time.time()
        return batch

class ResultsExporter(Thread):
    def __init__(
            self, 
            results_consumer: QueueConsumer, 
            db_manager: DatabaseManager, 
            batch_size: int = 100, 
            batch_interval: int = 60
        ):
        super(ResultsExporter, self).__init__()
        self.consumer = results_consumer
        self.db_manager = db_manager
        self.stop_event = Event()
        self.batching_strategy = BatchingStrategy(batch_size, batch_interval)

    def stop(self):
        if self.stop_event.is_set():
            return
        logger.info("Stopping exporter.")
        self.stop_event.set()
        self.consumer.close()

    def run(self):
        while not self.stop_event.is_set() and not self.consumer.closed:
            try:
                ready = self.batching_strategy.add(self.consumer.get(timeout=1))

                if ready:
                    batch = self.batching_strategy.get_batch()
                    self.db_manager.insert_records(batch)
            except ConsumerEmptyException:
                continue
            except ConsumerClosedException:
                logger.error("Consumer queue is closed.")
            except DatabaseManagerException as e:
                logger.error(f"An error occurred while exporting results to db {e}")
        
        self.db_manager.insert_records(
            self.batching_strategy.get_batch()
        )

