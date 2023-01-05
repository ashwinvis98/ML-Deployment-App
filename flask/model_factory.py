from tensorflow.saved_model import contains_saved_model
import os

from tf_model import TFModel
from model_interface import AbstractModel

class ModelFactory:

    def __init__(self):
        pass


    def create_model(self) -> AbstractModel:
        """
        Figures out what type of model is saved (eg. TF SavedModel, etc)
        and returns a wrapper for that object. The model should be saved
        in the same directory as this file with the name "saved_model".
        """
        if contains_saved_model(os.environ['MODEL_NAME']):
            return TFModel()
        else:
            return "Tensorflow model loaded unsuccessfully."
        