# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Copyright (c) 2021.  Mohamed Reda Bouadjenek, Deakin University                       +
#               Email:  reda.bouadjenek@deakin.edu.au                                    +
#                                                                                        +
#       Licensed under the Apache License, Version 2.0 (the "License");                  +
#       you may not use this file except in compliance with the License.                 +
#       You may obtain a copy of the License at:                                         +
#                                                                                        +
#       http://www.apache.org/licenses/LICENSE-2.0                                       +
#                                                                                        +
#       Unless required by applicable law or agreed to in writing, software              +
#       distributed under the License is distributed on an "AS IS" BASIS,                +
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.         +
#       See the License for the specific language governing permissions and              +
#       limitations under the License.                                                   +
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from tensorflow import keras
from tensorflow.keras.layers import Input, Dropout, Flatten, Dense, Activation, Lambda, Conv2D, MaxPool2D, \
    GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.applications import VGG19
from deakin.edu.au.data import Cifar100
import deakin.edu.au.metrics as metrics
import numpy as np


class performance_callback(keras.callbacks.Callback):
    def __init__(self, X, y, taxo):
        self.X = X
        self.y = y
        self.taxo = taxo

    def on_epoch_end(self, epoch, logs=None):
        y_pred = self.model.predict(self.X)
        y_pred = get_pred_indexes(y_pred)
        accuracy = metrics.get_accuracy(y_pred, self.y)
        exact_match = metrics.get_exact_match(y_pred, self.y)
        consistency = metrics.get_consistency(y_pred, self.taxo)
        print('-' * 100)
        print(f"epoch={epoch + 1}, ", end='')
        print(f"Exact Match = {exact_match:.4f}, ", end='')
        for i in range(len(accuracy)):
            print(f"accuracy level_{i} = {accuracy[i]:.4f}, ", end='')
        print(f"Consistency = {consistency:.4f}")
        print('-' * 100)
        print('')


def get_pred_indexes(y_pred):
    y_pred_indexes = []
    for pred in y_pred:
        y_pred_indexes.append(np.argmax(pred, axis=1))
    return y_pred_indexes


def get_MLPH_model(num_classes: list, image_size, conv_base=VGG19(include_top=False, weights="imagenet"),
                   learning_rate=1e-5, loss_weights=[]):
    # Conv base
    in_layer = Input(shape=image_size, name='main_input')
    conv_base = conv_base(in_layer)
    conv_base = Flatten()(conv_base)
    # create output layers
    out_layers = []
    for idx, v in enumerate(num_classes):
        out_layers.append(Dense(v, activation="softmax", name='out_level_' + str(idx))(conv_base))

    # Build the model
    model = Model(name='MLPH_model',
                  inputs=in_layer,
                  outputs=out_layers)
    loss = [keras.losses.SparseCategoricalCrossentropy() for x in num_classes]
    if len(loss_weights) == 0:
        loss_weights = [1 / len(num_classes) for x in num_classes]
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer,
                  loss=loss,
                  loss_weights=loss_weights,
                  metrics=['accuracy'])
    return model


def get_BCNN1(num_classes: list, image_size, reverse=False, conv_base=VGG19(include_top=False, weights="imagenet"),
              learning_rate=1e-5, loss_weights=[]):
    # Conv base
    in_layer = Input(shape=image_size, name='main_input')
    conv_base = conv_base(in_layer)
    conv_base = Flatten()(conv_base)
    # create output layers
    out_layers = []
    if reverse:
        num_classes = list(reversed(num_classes))
    for idx, v in enumerate(num_classes):
        if reverse:
            idx = len(num_classes) - idx - 1
        if len(out_layers) == 0:
            out_layers.append(Dense(v, activation="softmax", name='out_level_' + str(idx))(conv_base))
        else:
            out_layers.append(Dense(v, activation="softmax", name='out_level_' + str(idx))(out_layers[-1]))
    if reverse:
        out_layers = list(reversed(out_layers))
    # Build the model
    model = Model(name='Model_BCNN1',
                  inputs=in_layer,
                  outputs=out_layers)
    loss = [keras.losses.SparseCategoricalCrossentropy() for x in num_classes]
    if len(loss_weights) == 0:
        loss_weights = [1 / len(num_classes) for x in num_classes]
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer,
                  loss=loss,
                  loss_weights=loss_weights,
                  metrics=['accuracy'])
    return model


def get_BCNN2(num_classes: list, image_size, reverse=False, conv_base=VGG19(include_top=False, weights="imagenet"),
              learning_rate=1e-5, loss_weights=[]):
    # Conv base
    in_layer = Input(shape=image_size, name='main_input')
    conv_base = conv_base(in_layer)
    conv_base = Flatten()(conv_base)
    # create output layers
    logits_layers = []
    out_layers = []
    if reverse:
        num_classes = list(reversed(num_classes))
    for idx, v in enumerate(num_classes):
        if reverse:
            idx = len(num_classes) - idx - 1
        if len(logits_layers) == 0:
            logits = Dense(v, name='logits_level_' + str(idx))(conv_base)
            logits_layers.append(logits)
            out_layers.append(Activation(keras.activations.softmax, name='out_level_' + str(idx))(logits))
        else:
            logits = Dense(v, name='logits_level_' + str(idx))(logits_layers[-1])
            logits_layers.append(logits)
            out_layers.append(Activation(keras.activations.softmax, name='out_level_' + str(idx))(logits))
    if reverse:
        out_layers = list(reversed(out_layers))
    # Build the model
    model = Model(name='BCNN2',
                  inputs=in_layer,
                  outputs=out_layers)
    loss = [keras.losses.SparseCategoricalCrossentropy() for x in num_classes]
    if len(loss_weights) == 0:
        loss_weights = [1 / len(num_classes) for x in num_classes]
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer,
                  loss=loss,
                  loss_weights=loss_weights,
                  metrics=['accuracy'])
    return model


def get_mnets(num_classes: list, image_size, reverse=False, conv_base=[],
              learning_rate=1e-5, loss_weights=[]):
    in_layer = Input(shape=image_size, name='main_input')
    # Conv base
    if len(conv_base) == 0 or len(num_classes) != len(conv_base):
        conv_base = [VGG19(include_top=False, weights="imagenet") for x in num_classes]
    out_layers = []
    for i in range(len(conv_base)):
        conv_base[i]._name = 'conv_base' + str(i)
        conv_base[i] = conv_base[i](in_layer)
        conv_base[i] = Flatten()(conv_base[i])
        out_layers.append(Dense(num_classes[i], activation="softmax", name='out_level_' + str(i))(conv_base[i]))

    # Build the model
    model = Model(name='mnets',
                  inputs=in_layer,
                  outputs=out_layers)
    loss = [keras.losses.SparseCategoricalCrossentropy() for x in num_classes]
    if len(loss_weights) == 0:
        loss_weights = [1 / len(num_classes) for x in num_classes]
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer,
                  loss=loss,
                  loss_weights=loss_weights,
                  metrics=['accuracy'])
    return model


if __name__ == '__main__':
    dataset = Cifar100()
    num_classes = [dataset.num_classes_l0, dataset.num_classes_l1, dataset.num_classes_l2]
    model = get_mnets(num_classes, dataset.image_size)
    model.summary()
