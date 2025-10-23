def requirements():
    return """
# Core Python and Jupyter
ipykernel==6.30.1
ipython==8.37.0
jupyter==1.1.1
jupyterlab==4.4.6
ipywidgets==8.1.7
notebook==7.4.5

# Data processing
numpy==2.1.3
pandas==2.3.1
scipy==1.15.3

# Machine Learning / Deep Learning
scikit-learn==1.7.1
tensorflow==2.19.0
keras==3.11.1
tensorboard==2.19.0
opt_einsum==3.4.0
ml_dtypes==0.5.3
h5py==3.14.0

# Visualization
matplotlib==3.10.5
seaborn==0.13.2

# Utilities
requests==2.32.5
protobuf==5.29.5
typing_extensions==4.15.0
Werkzeug==3.1.3
"""


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

def get7():
    return """
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
from tensorflow.keras.layers import Input,Dense,Dropout,Embedding, LSTM , add
from tensorflow.keras.models import Model
from tensorflow.keras.utils import plot_model

import os
import numpy as np
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.Your_Pretrained_CNN import Your_Pretrained_CNN
from tensorflow.keras.applications.Your_Pretrained_CNN import preprocess_input

# define the captioning model
def define_model(vocab_size, max_length):
    # Feature extractor
    inputs1 = Input(shape=(2048,))
    fe1 = Dropout(0.5)(inputs1)
    fe2 = Dense(256, activation='relu')(fe1)

    # Sequence model
    inputs2 = Input(shape=(max_length,))
    se1 = Embedding(vocab_size, 256, mask_zero=True)(inputs2)
    se2 = Dropout(0.5)(se1)
    se3 = LSTM(256)(se2)

    # Decoder model
    decoder1 = add([fe2, se3])
    decoder2 = Dense(256, activation='relu')(decoder1)
    outputs = Dense(vocab_size, activation='softmax')(decoder2)

    model = Model(inputs=[inputs1, inputs2], outputs=outputs)
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    print(model.summary())
    plot_model(model, to_file='fish_caption_model.png', show_shapes=True)
    return model

with open(r'\tokenizer.pkl','rb') as f:
    tokenizer = pickle.load(f)
vocab_size = len(tokenizer.word_index) + 1
max_len = 2000

def extract_feature_from_image(image_path, conv_base):
    features = {}
    if os.path.isfile(image_path) and image_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        # Load image
        img = load_img(image_path, target_size=(224, 224))
        img = img_to_array(img)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)
        
        # Extract features
        feature_map = conv_base.predict(img, verbose=0)  # shape: (1, 7, 7, 2048)
        
        # Apply global average pooling to flatten
        feature_vector = np.mean(feature_map, axis=(1, 2))  # shape: (1, 2048)
        
        # Save with filename (without extension) as key
        key = os.path.splitext(os.path.basename(image_path))[0]
        features[key] = feature_vector
    else:
        raise ValueError("Invalid image path or unsupported file format.")
    
    return features

def generate_caption(model, tokenizer, photo, max_length):
    in_text = 'startseq'
    for _ in range(max_length):
        sequence = tokenizer.texts_to_sequences([in_text])[0]
        sequence = pad_sequences([sequence], maxlen=max_length, padding='post')
        yhat = model.predict([photo, sequence], verbose=0)
        yhat = np.argmax(yhat)
        word = word_for_id(yhat, tokenizer)
        if word is None:
            break
        in_text += ' ' + word
        if word == 'endseq':
            break
    return in_text


def word_for_id(integer, tokenizer):
    for word, index in tokenizer.word_index.items():
        if index == integer:
            return word
    return None


def to_references(descriptions):
    return [[desc.split()] for desc_list in descriptions.values() for desc in desc_list]


def to_hypotheses(model, descriptions, photos, tokenizer, max_length):
    lines = []
    for key in descriptions.keys():
        yhat = generate_caption(model, tokenizer, photos[key], max_length)
        lines.append(yhat.split())
    return lines


# Rebuild your model with the same structure
model = define_model(vocab_size, max_len)

# Load only the trained weights
model.load_weights(r"Your_Pretrained_CNN_Image_Captioning_.hdf5")

print("Model rebuilt and weights loaded successfully!")


tokenizer = tokenizer  # already created earlier
max_len = max_len      # same as training

# Path to your test image
image_path = r"imgpath"
conv_base = Your_Pretrained_CNN(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
# Extract features
photo_features = extract_feature_from_image(image_path,conv_base)

# Generate caption
caption = generate_caption(model, tokenizer, photo_features, max_len)

# Clean up caption
caption = caption.replace('startseq', '').replace('endseq', '').strip()

print("\n Image:", image_path)
print(caption)
"""

def get2_():
    return """
from keras.applications.vgg16 import VGG16, preprocess_input
from keras.preprocessing.image import load_img, img_to_array
from keras.models import Model, Sequential
from keras.layers import Dense
import matplotlib.pyplot as plt
from numpy import expand_dims
import numpy as np

# ==========================================================
# Load and summarize VGG16 model
# ==========================================================
print("\n=== LAYER VIS 1 ===\n")

model = VGG16()
model.summary()

# Simple text summary visualization
plt.figure(figsize=(10, 1))
plt.text(0.01, 0.5, "VGG16 Model Loaded Successfully", fontsize=16, ha='left', va='center')
plt.axis('off')
plt.show()

# ==========================================================
# Visualize Filters from Second Layer
# ==========================================================
print("\n=== LAYER VIS 2 — FILTER VISUALIZATION ===\n")

filters, biases = model.layers[1].get_weights()

# Normalize filter values to 0–1 for visualization
f_min, f_max = filters.min(), filters.max()
filters = (filters - f_min) / (f_max - f_min)

# Plot first few filters
n_filters, ix = 6, 1
plt.figure(figsize=(8, 8))
for i in range(n_filters):
    f = filters[:, :, :, i]
    for j in range(3):
        ax = plt.subplot(n_filters, 3, ix)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.imshow(f[:, :, j], cmap='gray')
        ix += 1
plt.suptitle("VGG16 First Conv Layer Filters", fontsize=14)
plt.show()

# ==========================================================
# Feature Maps from the First Convolutional Layer
# ==========================================================
print("\n=== LAYER VIS 3 — FEATURE MAPS FROM FIRST CONV LAYER ===\n")

layer_model = Model(inputs=model.inputs, outputs=model.layers[1].output)

# Load and preprocess image
img = load_img('bird.jpg', target_size=(224, 224))
img = img_to_array(img)
img = expand_dims(img, axis=0)
img = preprocess_input(img)

# Extract feature maps
feature_maps = layer_model.predict(img)

# Plot 8x8 feature maps
square = 8
ix = 1
plt.figure(figsize=(12, 12))
for _ in range(square):
    for _ in range(square):
        ax = plt.subplot(square, square, ix)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.imshow(feature_maps[0, :, :, ix-1], cmap='gray')
        ix += 1
plt.suptitle("Feature Maps from First Conv Layer", fontsize=14)
plt.show()

# ==========================================================
# Feature Maps from Multiple Convolutional Blocks
# ==========================================================
print("\n=== LAYER VIS 4 — MULTIPLE CONV BLOCKS FEATURE MAPS ===\n")

ixs = [2, 5, 9, 13, 17]
outputs = [model.layers[i].output for i in ixs]
multi_model = Model(inputs=model.inputs, outputs=outputs)

# Extract feature maps
feature_maps = multi_model.predict(img)

# Visualize maps from each block
square = 8
for layer_index, fmap in enumerate(feature_maps):
    ix = 1
    plt.figure(figsize=(12, 12))
    for _ in range(square):
        for _ in range(square):
            ax = plt.subplot(square, square, ix)
            ax.set_xticks([])
            ax.set_yticks([])
            plt.imshow(fmap[0, :, :, ix-1], cmap='gray')
            ix += 1
    plt.suptitle(f"Feature Maps — Conv Block {layer_index + 1}", fontsize=14)
    plt.show()

# ==========================================================
# Simple Sequential Dense Model Visualization (Manual)
# ==========================================================
print("\n=== LAYER VIS 5 — SIMPLE SEQUENTIAL MODEL (DRAWN) ===\n")

simple_model = Sequential()
simple_model.add(Dense(2, input_dim=1, activation='relu'))
simple_model.add(Dense(1, activation='sigmoid'))
simple_model.summary()

# Draw using Matplotlib
plt.figure(figsize=(8, 3))
plt.text(0.05, 0.6, 'Input Layer (1 neuron)', fontsize=12, bbox=dict(facecolor='lightblue', alpha=0.5))
plt.text(0.4, 0.6, 'Dense Layer (2, ReLU)', fontsize=12, bbox=dict(facecolor='lightgreen', alpha=0.5))
plt.text(0.75, 0.6, 'Output Layer (1, Sigmoid)', fontsize=12, bbox=dict(facecolor='lightcoral', alpha=0.5))
plt.arrow(0.22, 0.62, 0.12, 0, head_width=0.02, head_length=0.02, fc='k', ec='k')
plt.arrow(0.58, 0.62, 0.12, 0, head_width=0.02, head_length=0.02, fc='k', ec='k')
plt.axis('off')
plt.title("Simple Sequential Model Visualization", fontsize=14)
plt.show()
"""

def get7d():
    return """
# ==============================
# Imports
# ==============================
import pickle
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import os

# ==============================
# Paths & Image Directory
# ==============================
model_path = r"soybean_caption_model.keras"
tokenizer_path = r"./tokenizer.pkl"
img_dir = r"soyadatasets/test"  # folder containing your test images
img_size = (224, 224)
max_len = 12  # must match training

# ==============================
# Load Model & Tokenizer
# ==============================
model = load_model(model_path)
with open(tokenizer_path, 'rb') as f:
    tokenizer = pickle.load(f)

# ==============================
# Caption Utilities
# ==============================
def word_for_id(integer, tokenizer):
    for word, index in tokenizer.word_index.items():
        if index == integer:
            return word
    return None

def generate_caption(model, tokenizer, photo_feature, max_length_val):
    in_text = 'startseq'
    for _ in range(max_length_val):
        sequence = tokenizer.texts_to_sequences([in_text])[0]
        sequence = pad_sequences([sequence], maxlen=max_length_val, padding='post')
        yhat = model.predict([photo_feature, sequence], verbose=0)
        yhat = np.argmax(yhat)
        word = word_for_id(yhat, tokenizer)
        if word is None:
            break
        in_text += ' ' + word
        if word == 'endseq':
            break
    return in_text

# ==============================
# Feature Extraction for Single Image
# ==============================
conv_base = VGG16(weights='imagenet', include_top=False, pooling='avg')

def extract_single_image_feature(img_path):
    img = load_img(img_path, target_size=img_size)
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    feature = conv_base.predict(img_array, verbose=0)
    return feature

# ==============================
# Generate Captions for All Images in a Folder
# ==============================
image_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

for img_file in image_files:
    img_path = os.path.join(img_dir, img_file)
    feature = extract_single_image_feature(img_path)
    caption = generate_caption(model, tokenizer, feature, max_len)
    print(f"{img_file} -> {caption}")
"""