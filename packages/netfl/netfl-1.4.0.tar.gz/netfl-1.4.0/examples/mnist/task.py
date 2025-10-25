from typing import Any

import tensorflow as tf
from keras import models, optimizers
from flwr.server.strategy import Strategy, FedAvg

from netfl.core.task import Task, Dataset, DatasetInfo, DatasetPartitioner, TrainConfigs
from netfl.core.models import cnn3
from netfl.core.partitioners import IidPartitioner


class MNIST(Task):
    def dataset_info(self) -> DatasetInfo:
        return DatasetInfo(
            huggingface_path="ylecun/mnist",
            input_key="image",
            label_key="label",
            input_dtype=tf.float32,
            label_dtype=tf.int32,
        )

    def dataset_partitioner(self) -> DatasetPartitioner:
        return IidPartitioner()

    def preprocess_dataset(self, dataset: Dataset, training: bool) -> Dataset:
        return Dataset(x=tf.divide(dataset.x, 255.0), y=dataset.y)

    def model(self) -> models.Model:
        return cnn3(
            input_shape=(28, 28, 1),
            output_classes=10,
            optimizer=optimizers.SGD(learning_rate=0.01),
        )

    def aggregation_strategy(self) -> tuple[type[Strategy], dict[str, Any]]:
        return FedAvg, {}

    def train_configs(self) -> TrainConfigs:
        return TrainConfigs(
            batch_size=16,
            epochs=2,
            num_clients=4,
            num_partitions=4,
            num_rounds=10,
            seed_data=42,
            shuffle_data=True,
        )


class FLTask(MNIST):
    pass
