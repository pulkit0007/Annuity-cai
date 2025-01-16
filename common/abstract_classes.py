from abc import abstractmethod , ABC

class QueueService(ABC):

    @abstractmethod
    def push_item(self , stream_name: str, message: dict) -> None:
        pass

    @abstractmethod
    def read_items(self , stream_name: str, count: int = 1):
        pass