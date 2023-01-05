from abc import ABC, abstractmethod

class AbstractModel(ABC):

    @abstractmethod
    def predict(self, X):
        pass

    @abstractmethod
    def _load_model(self):
        pass