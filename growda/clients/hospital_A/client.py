"""
Federated learning client for Hospital A.
"""
import os
import sys
import flwr as fl
import tensorflow as tf
import numpy as np

# Add the parent directory to the path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.model import create_pneumonia_model

# Data paths
DATA_DIR = "../../data/hospital_A"  # For hospital_B: change to "hospital_B"

class PneumoniaClient(fl.client.NumPyClient):
    def __init__(self):
        self.model = create_pneumonia_model()
        print("Building data pipeline...")
        self.train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            rescale=1./255, rotation_range=20, width_shift_range=0.2, height_shift_range=0.2,
            shear_range=0.2, zoom_range=0.2, horizontal_flip=True, fill_mode="nearest"
        )
        self.val_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)
        self.train_generator = self.train_datagen.flow_from_directory(
            os.path.join(DATA_DIR, "train"), target_size=(150, 150), batch_size=32, class_mode="binary"
        )
        self.val_generator = self.val_datagen.flow_from_directory(
            os.path.join(DATA_DIR, "val"), target_size=(150, 150), batch_size=32, class_mode="binary"
        )

    def get_parameters(self, config):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        history = self.model.fit(
            self.train_generator, epochs=1, validation_data=self.val_generator, verbose=1
        )
        parameters_updated = self.model.get_weights()
        results = {
            "loss": history.history["loss"][0],
            "accuracy": history.history["accuracy"][0],
            "val_loss": history.history["val_loss"][0],
            "val_accuracy": history.history["val_accuracy"][0],
        }
        num_examples = self.train_generator.samples
        print("[Client-Fit] Returning tuple with types:", type(parameters_updated), type(num_examples), type(results))
        print(f"[Client-Fit] Shapes: weights len={len(parameters_updated)}, num_examples={num_examples}, results keys={list(results.keys())}")
        return parameters_updated, num_examples, results

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        try:
            loss, accuracy = self.model.evaluate(self.val_generator)
            print("[Client-Evaluate] Tuple:", type(loss), type(self.val_generator.samples), type(accuracy))
            return loss, self.val_generator.samples, {"accuracy": accuracy}
        except Exception as e:
            print("[Eval Error] Possibly empty validation set!", e)
            return 0.0, 0, {"accuracy": 0.0}

def main():
    client = PneumoniaClient()
    fl.client.start_numpy_client(server_address="127.0.0.1:8080", client=client)

if __name__ == "__main__":
    main()