from tensorflow.keras.models import load_model
import os
from functools import reduce

from model_interface import AbstractModel


class TFModel(AbstractModel):

    def __init__(self):
        """
        Loads the Tensorflow SavedModel and conputes variable
        for reshaping inuput from protobuf.
        """
        self.model = self._load_model()
        
        # Compute info for reshaping flat input
        config = self.model.get_config()
        self.input_dims = list(config["layers"][0]["config"]["batch_input_shape"])
        self.divisor = reduce(lambda x, y: x*y, self.input_dims[1:])

    def predict(self, X):
        return self.model.predict(X)

    def _load_model(self):
        return load_model(os.environ['MODEL_NAME'])

