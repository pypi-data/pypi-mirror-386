def get1():
    return """
from pycm import ConfusionMatrix
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

matrix = {
    "Class A": {
        "Class A": 82,
        "Class B": 0,
        "Class C": 2,
        "Class D": 10,
        "Class E": 0,
        "Class F": 3,
        "Class G": 3,
    },
    "Class B": {
        "Class A": 4,
        "Class B": 87,
        "Class C": 1,
        "Class D": 3,
        "Class E": 1,
        "Class F": 1,
        "Class G": 3,
    }
}

cm = ConfusionMatrix(matrix = matrix)

print(cm)

df = pd.DataFrame(matrix).T  # Transpose for correct orientation
plt.figure(figsize=(25, 25))
sns.heatmap(df, annot=True, fmt="d", cmap="YlGnBu")
plt.title("Confusion Matrix for based Classifier Model")
plt.ylabel("Predicted Disease")
plt.xlabel("Actual Disease")
plt.show()
"""


def get2():
    return """
# --- Code from layer_vis1.ipynb ---
from keras.applications.vgg16 import VGG16
from matplotlib import pyplot
from tensorflow.keras.utils import plot_model
from IPython.display import Image

# load the model
model = VGG16()

# summarize the model
model.summary()

# plot the model
plot_model(model, to_file='model_plot_1.png', show_shapes=True, show_layer_names=True)
Image(filename="model_plot_1.png")

# summarize filter shapes
for layer in model.layers:
	# check for convolutional layer
	if 'conv' not in layer.name:
		continue
	# get filter weights
	filters, biases = layer.get_weights()
	print(layer.name, filters.shape)

# visualize filters
filters, biases = model.layers[1].get_weights()

# normalize filter values to 0-1 so we can visualize them
f_min, f_max = filters.min(), filters.max()
filters = (filters - f_min) / (f_max - f_min)

# print the layers' kernels
print(model.layers[1].kernel)

# --- Code from layer_vis2.ipynb ---
from keras.applications.vgg16 import VGG16
from matplotlib import pyplot
from tensorflow.keras.utils import plot_model
from IPython.display import Image

# load the model
model = VGG16()

# retrieve weights from the second hidden layer
filters, biases = model.layers[1].get_weights()

# normalize filter values to 0-1 so we can visualize them
f_min, f_max = filters.min(), filters.max()
filters = (filters - f_min) / (f_max - f_min)

# plot first few filters
n_filters, ix = 6, 1
for i in range(n_filters):
	# get the filter
	f = filters[:, :, :, i]
	# plot each channel separately
	for j in range(3):
		# specify subplot and turn of axis
		ax = pyplot.subplot(n_filters, 3, ix)
		ax.set_xticks([])
		ax.set_yticks([])
		# plot filter channel in grayscale
		pyplot.imshow(f[:, :, j], cmap='gray')
		ix += 1
# show the figure
pyplot.show()

# --- Code from layer_vis3.ipynb ---
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.models import Model
from matplotlib import pyplot
from numpy import expand_dims
from tensorflow.keras.utils import plot_model
from IPython.display import Image

# load the model
model = VGG16()
# redefine model to output right after the first hidden layer
model = Model(inputs=model.inputs, outputs=model.layers[1].output)

plot_model(model, to_file="model_plot_3.png", show_shapes=True, show_layer_names=True)
Image(filename="model_plot_3.png")

# summarize the model
model.summary()

# load the image with the required shape
img = load_img('sample_image.jpg', target_size=(224, 224))
# convert the image to an array
img = img_to_array(img)
# expand dimensions to create a single sample as we process one image at a time
img = expand_dims(img, axis=0)
# preprocess the image to suit the model
img = preprocess_input(img)
# get the feature map for the first hidden layer
feature_maps = model.predict(img)

# plot all 64 maps in an 8x8 squares
square = 8
ix = 1
for _ in range(square):
	for _ in range(square):
		# specify subplot and turn of axis
		ax = pyplot.subplot(square, square, ix)
		ax.set_xticks([])
		ax.set_yticks([])
		# plot filter channel in grayscale
		pyplot.imshow(feature_maps[0, :, :, ix-1], cmap='gray')
		ix += 1
# show the figure
pyplot.show()

# --- Code from layer_vis4.ipynb ---
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.models import Model
from matplotlib import pyplot
from numpy import expand_dims
from tensorflow.keras.utils import plot_model
from IPython.display import Image

# load the model
model = VGG16()

# redefine model to output the results of all blocks
ixs = [2, 5, 9, 13, 17]
outputs = [model.layers[i].output for i in ixs]
model = Model(inputs=model.inputs, outputs=outputs)
plot_model(model, to_file="model_plot_4.png", show_shapes=True, show_layer_names=True)
Image(filename="model_plot_4.png")

# summarize the model
model.summary()

# load the image with the required shape
img = load_img('sample_image.jpg', target_size=(224, 224))
# convert the image to an array
img = img_to_array(img)
# expand dimensions to create a single sample as we process one image at a time
img = expand_dims(img, axis=0)
# preprocess the image to suit the model
img = preprocess_input(img)
# get the feature map for the first hidden layer
feature_maps = model.predict(img)

# plot the output from each block
square = 8
for fmap in feature_maps:
	# plot all 64 maps in an 8x8 squares
	ix = 1
	for _ in range(square):
		for _ in range(square):
			# specify subplot and turn of axis
			ax = pyplot.subplot(square, square, ix)
			ax.set_xticks([])
			ax.set_yticks([])
			# plot filter channel in grayscale
			pyplot.imshow(fmap[0, :, :, ix-1], cmap='gray')
			ix += 1
	# show the figure
	pyplot.show()

# --- Code from layer_vis5.ipynb ---
from keras.models import Sequential
from keras.layers import Dense
from tensorflow.keras.utils import plot_model

model = Sequential()
model.add(Dense(2, input_dim=1, activation='relu'))
model.add(Dense(1, activation='sigmoid'))

# summarize the model
model.summary()

# plot the model
plot_model(model, to_file='model_plot_5.png', show_shapes=True, show_layer_names=True)
Image(filename="model_plot_5.png")
"""


def get3():
    return """
from numpy import expand_dims
from keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from matplotlib import pyplot as plt

img = load_img(r'..\sample_images\sam4.png')
data = img_to_array(img)
samples = expand_dims(data, 0)  # Add batch dimension

augmentations = {
    "Horizontal Shift": {"width_shift_range": [-200, 200]},
    "Horizontal Flip": {"horizontal_flip": True},
    "Height Shift": {"height_shift_range": 0.5},
    "Vertical Flip": {"vertical_flip": True},
    "Random Rotation": {"rotation_range": 90},
    "Random Brightness": {"brightness_range": [0.2, 1.0]},
    "Random Zoom": {"zoom_range": [0.5, 1.0]},
}

for title, params in augmentations.items():
    datagen = ImageDataGenerator(**params)
    it = datagen.flow(samples, batch_size=1)
    
    plt.figure(figsize=(8, 8))
    plt.suptitle(title, fontsize=16)
    
    for i in range(9):
        plt.subplot(3, 3, i + 1)
        batch = next(it)
        image = batch[0].astype('uint8')
        plt.imshow(image)
        plt.axis('off')
    
    plt.show()
"""


def get4():
    return """
import argparse

# importing pretrained models
from tensorflow.keras.applications import (
    VGG16,
    VGG19,
    InceptionV3,
    Xception,
    ResNet50,
    imagenet_utils,
)
from tensorflow.keras.applications.inception_v3 import preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np


# Parsing the commandline arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="path to the input image")
ap.add_argument(
    "-model",
    "--model",
    type=str,
    default="vgg16",
    help="name of pre-trained network to use",
)
args = vars(ap.parse_args())

MODELS = {
    "vgg16": VGG16,
    "vgg19": VGG19,
    "inception": InceptionV3,
    "xception": Xception,
    "resnet": ResNet50,
}

if args["model"] not in MODELS:
    print("Available Models : ", list(MODELS))
    raise AssertionError(
        "The --model command line argument should be a key in MODELS dictionary"
    )

if args["model"] in ("inception", "xception"):
    inputshape = (299, 299)
    preprocess = preprocess_input
else:
    inputshape = (224, 224)
    preprocess = imagenet_utils.preprocess_input

print(f"[INFO] Loading {args['model']} ...")
Network = MODELS[args["model"]]
model = Network(weights="imagenet")

print("[INFO] Loading and Preprocessing the image ...")
image = load_img(args["image"], target_size=inputshape)
image = img_to_array(image)
image = np.expand_dims(image, axis=0)
image = preprocess(image)

print(f"[INFO] Classifying Image with {args['model']} ...")
preds = model.predict(image)
P = imagenet_utils.decode_predictions(preds)

for i, (imagenetID, label, prob) in enumerate(P[0]):
    print(f"{i+1} \t {label} \t {prob*100:.2f}%")

# Sample Image Path
# sample_images\sam1.jpeg
# sample_images\sam2.jpeg

# Sample Run
# python classify_image.py --image sample_images\sam1.jpeg --model vgg16
"""


def get5():
    return """
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
import numpy as np
import matplotlib.pyplot as plt
import os

model_path = r"model.hdf5"
test_dir = r"dataset\Test"

model = tf.keras.models.load_model(model_path)
print("Model loaded successfully")

class_names = [
    'a',
    'b',
]


datagen = ImageDataGenerator(rescale=1./255)
test_gen = datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),
    batch_size=1,
    class_mode='categorical',
    shuffle=False
)

predictions = model.predict(test_gen, verbose=1)
predicted_classes = np.argmax(predictions, axis=1)

from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns

true_classes = test_gen.classes
cm = confusion_matrix(true_classes, predicted_classes)

plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

print("\nClassification Report:\n")
print(classification_report(true_classes, predicted_classes, target_names=class_names))
"""


def get6():
    return """
import tensorflow as tf
from tensorflow.keras.applications.your_pretrained_cnn_model import your_pretrained_cnn_model, preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

model_path = r"Feature_Extraction_Trained_model_model.hdf5"
test_dir = r"dataset\Test"

model = tf.keras.models.load_model(model_path)
print("Model loaded successfully")

# Load your_pretrained_cnn_model base (used for feature extraction)
pretrained_cnn_base = your_pretrained_cnn_model(weights='imagenet', include_top=False, input_shape=(224,224,3))
print("your_pretrained_cnn_model Base model loaded for feature extraction!")

class_names = [
    'a',
    'b',
]

datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
test_gen = datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),
    batch_size=1,
    class_mode='categorical',
    shuffle=False
)

features = pretrained_cnn_base.predict(test_gen, verbose=1)
print("Feature extraction completed!")

predictions = model.predict(features, verbose=1)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = test_gen.classes

# Confusion Matrix
cm = confusion_matrix(true_classes, predicted_classes)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=class_names, yticklabels=class_names)
plt.title("Confusion Matrix - Feature Extraction Model")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.show()

# Classification Report
print("\nClassification Report:\n")
print(classification_report(true_classes, predicted_classes, target_names=class_names))
"""
