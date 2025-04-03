# views.py

from django.shortcuts import render
from django.http import JsonResponse
import numpy as np
from tensorflow.keras.layers import Input, Dense, Flatten, Conv2D, MaxPooling2D, BatchNormalization, Dropout, Reshape, Concatenate, LeakyReLU
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import Model
import os
from .forms import ImageUploadForm
import io  # Import io module
import base64
import random
import time

image_dimensions = {'height': 256, 'width': 256, 'channels': 3}


class Classifier:
    def __init__(self):
        self.model = 0

    def predict(self, x):
        return self.model.predict(x)

    def fit(self, x, y):
        return self.model.train_on_batch(x, y)

    def get_accuracy(self, x, y):
        return self.model.test_on_batch(x, y)

    def load(self, path):
        self.model.load_weights(path)


class Meso4(Classifier):
    def __init__(self, learning_rate=0.001):
        self.model = self.init_model()
        optimizer = Adam(lr=learning_rate)
        self.model.compile(optimizer=optimizer,
                           loss='mean_squared_error',
                           metrics=['accuracy'])

    def init_model(self):
        x = Input(shape=(image_dimensions['height'],
                         image_dimensions['width'],
                         image_dimensions['channels']))

        x1 = Conv2D(8, (3, 3), padding='same', activation='relu')(x)
        x1 = BatchNormalization()(x1)
        x1 = MaxPooling2D(pool_size=(2, 2), padding='same')(x1)

        x2 = Conv2D(8, (5, 5), padding='same', activation='relu')(x1)
        x2 = BatchNormalization()(x2)
        x2 = MaxPooling2D(pool_size=(2, 2), padding='same')(x2)

        x3 = Conv2D(16, (5, 5), padding='same', activation='relu')(x2)
        x3 = BatchNormalization()(x3)
        x3 = MaxPooling2D(pool_size=(2, 2), padding='same')(x3)

        x4 = Conv2D(16, (5, 5), padding='same', activation='relu')(x3)
        x4 = BatchNormalization()(x4)
        x4 = MaxPooling2D(pool_size=(4, 4), padding='same')(x4)

        y = Flatten()(x4)
        y = Dropout(0.5)(y)
        y = Dense(16)(y)
        y = LeakyReLU(alpha=0.1)(y)
        y = Dropout(0.5)(y)
        y = Dense(1, activation='sigmoid')(y)

        return Model(inputs=x, outputs=y)


MesoNet_classifier = Meso4()
MesoNet_classifier.load('C:/Users/lohit/Downloads/Deepfake-detection/weights/Meso4_DF')


def classify_images(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            images = []
            image_data_list = []

            for image_field in form.cleaned_data.values():
                if isinstance(image_field, list):
                    for image in image_field:
                        image_content = image.read()
                        image_data = base64.b64encode(image_content).decode('utf-8')
                        images.append(img_to_array(load_img(io.BytesIO(image_content), target_size=(image_dimensions['height'], image_dimensions['width']))))
                        image_data_list.append(image_data)
                else:
                    image_content = image_field.read()
                    image_data = base64.b64encode(image_content).decode('utf-8')
                    images.append(img_to_array(load_img(io.BytesIO(image_content), target_size=(image_dimensions['height'], image_dimensions['width']))))
                    image_data_list.append(image_data)

            data_generator = np.array(images) / 255.0
            num_to_label = {1: "real", 0: "fake"}

            probabilistic_predictions = MesoNet_classifier.predict(data_generator)
            predictions = [num_to_label[round(x[0])] for x in probabilistic_predictions]

            true_labels = np.zeros(len(data_generator))

            accuracy = MesoNet_classifier.get_accuracy(data_generator, true_labels)
            time.sleep(3)
            result = {"accuracy": accuracy,"predictions": zip(image_data_list, predictions)}
            return render(request, 'classify_images.html', {'form': form, 'result': result})
    else:
        form = ImageUploadForm()

    return render(request, 'classify_images.html', {'form': form})
