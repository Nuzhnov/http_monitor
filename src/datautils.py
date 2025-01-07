from multiprocessing import Queue
from queue import Empty
from .models import ResultRecord


class ProducerClosedException(Exception):
    pass

class ConsumerClosedException(Exception):
    pass

class ConsumerEmptyException(Exception):
    pass


class QueueProducer:
    def __init__(self, queue: Queue):
        self.queue = queue
        self.closed = False
        
    def put(self, item: ResultRecord):
        if self.closed:
            raise ProducerClosedException("Producer is closed!")
        try:
            self.queue.put(item)
        except ValueError or ShutDown:
            raise ProducerClosedException("Queue is closed!")

    def close(self):
        self.closed = True
        if not self.queue._closed:
            self.queue.close()


class QueueConsumer:
    def __init__(self, queue):
        self.queue = queue
        self.closed = False
        
    def get(self, timeout=None) -> ResultRecord:
        if self.closed:
            raise ConsumerClosedException("Consumer is closed!")
        try:
            return self.queue.get(timeout=timeout)
        except Empty or ValueError:
            raise ConsumerEmptyException("Queue is empty!")
        
    def close(self):
        self.closed = True
