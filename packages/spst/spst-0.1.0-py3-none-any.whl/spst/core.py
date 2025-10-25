def get1():
    return '''from pycm import ConfusionMatrix
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
plt.show()'''



def get2():

    return '''
filter-1
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.utils import plot_model
import matplotlib.pyplot as plt

model = VGG16()

plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

print(model.layers)
for layer in model.layers:
    if 'conv' not in layer.name:
        continue
    filters, biases = layer.get_weights()
    print(layer.name, filters.shape)

filter-2

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.utils import plot_model
import matplotlib.pyplot as plt

model = VGG16()

plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

filters, biases = model.layers[1].get_weights()

f_min, f_max = filters.min(), filters.max()
filters = (filters - f_min) / (f_max - f_min)

n_filters, ix = 6, 1
for i in range(n_filters):
    f = filters[:, :, :, i]
    for j in range(3):
        ax = plt.subplot(n_filters, 3, ix)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.imshow(f[:, :, j], cmap='gray')
        ix += 1

plt.show()

filter-3
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Model
from tensorflow.keras.utils import plot_model
import matplotlib.pyplot as plt
from numpy import expand_dims

model = VGG16()

model = Model(inputs=model.inputs, outputs=model.layers[1].output)

plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

model.summary()

img = load_img('bird.jpeg', target_size=(224, 224))

img = img_to_array(img)

img = expand_dims(img, axis=0)
img = preprocess_input(img)
feature_maps = model.predict(img)
square = 8
ix = 1
for _ in range(square):
    for _ in range(square):
        ax = plt.subplot(square, square, ix)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.imshow(feature_maps[0, :, :, ix-1], cmap='gray')
        ix += 1
plt.show()

filter-4
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.models import Model
from matplotlib import pyplot
from numpy import expand_dims
from tensorflow.keras.utils import plot_model

model = VGG16()
plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)
ixs = [2, 5, 9, 13, 17]
outputs = [model.layers[i].output for i in ixs]
model = Model(inputs=model.inputs, outputs=outputs)
img = load_img('bird.jpeg', target_size=(224, 224))
img = img_to_array(img)
img = expand_dims(img, axis=0)
img = preprocess_input(img)
feature_maps = model.predict(img)
square = 8
for fmap in feature_maps:
	ix = 1
	for _ in range(square):
		for _ in range(square):
			ax = pyplot.subplot(square, square, ix)
			ax.set_xticks([])
			ax.set_yticks([])
			pyplot.imshow(fmap[0, :, :, ix-1], cmap='gray')
			ix += 1
	pyplot.show()

filter-5
from keras.models import Sequential
from keras.layers import Dense
from tensorflow.keras.utils import plot_model

model = Sequential()
model.add(Dense(2, input_dim=1, activation='relu'))
model.add(Dense(1, activation='sigmoid'))
plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)
    '''



def get3():
    return '''

Horizontal

from numpy import expand_dims
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot as plt

img = load_img('bird.jpg')
data = img_to_array(img)
samples = expand_dims(data, 0)

datagen = ImageDataGenerator(width_shift_range=[-200, 200])

it = datagen.flow(samples, batch_size=1)

for i in range(9):
    plt.subplot(330 + 1 + i)
    batch = next(it)
    image = batch[0].astype('uint8')
    plt.imshow(image)

plt.show()



Horizontal_Flip



from numpy import expand_dims
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot
img = load_img('bird.jpg')
data = img_to_array(img)
samples = expand_dims(data, 0)
datagen = ImageDataGenerator(horizontal_flip=True)
it = datagen.flow(samples, batch_size=1)
for i in range(9):
	pyplot.subplot(330 + 1 + i)
	batch = next(it)
	image = batch[0].astype('uint8')
	pyplot.imshow(image)
pyplot.show()


Vertical 

from numpy import expand_dims
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot
img = load_img('bird.jpg')
data = img_to_array(img)
samples = expand_dims(data, 0)
datagen = ImageDataGenerator(height_shift_range=0.5)
it = datagen.flow(samples, batch_size=1)
for i in range(9):
	pyplot.subplot(330 + 1 + i)
	batch = next(it)
	image = batch[0].astype('uint8')
	pyplot.imshow(image)
pyplot.show()



Random Brightness



from numpy import expand_dims
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot
img = load_img('bird.jpg')
data = img_to_array(img)
samples = expand_dims(data, 0)
datagen = ImageDataGenerator(brightness_range=[0.2,1.0])
it = datagen.flow(samples, batch_size=1)
for i in range(9):
	pyplot.subplot(330 + 1 + i)
	batch = next(it)
	image = batch[0].astype('uint8')
	pyplot.imshow(image)
pyplot.show()


Random Rotation

from numpy import expand_dims
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot
img = load_img('bird.jpg')
data = img_to_array(img)
samples = expand_dims(data, 0)
datagen = ImageDataGenerator(rotation_range=90)
it = datagen.flow(samples, batch_size=1)
for i in range(9):
	pyplot.subplot(330 + 1 + i)
	batch = next(it)
	image = batch[0].astype('uint8')
	pyplot.imshow(image)
pyplot.show()


Random Zooming

from numpy import expand_dims
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot
img = load_img('bird.jpg')
data = img_to_array(img)
samples = expand_dims(data, 0)
datagen = ImageDataGenerator(zoom_range=[0.5,1.0])
it = datagen.flow(samples, batch_size=1)
for i in range(9):
	pyplot.subplot(330 + 1 + i)
	batch = next(it)
	image = batch[0].astype('uint8')
	pyplot.imshow(image)
pyplot.show()

'''




def get4():
    return '''
    
import cv2
import numpy as np
import sys
from tensorflow.keras.applications import (
    VGG16, VGG19, InceptionV3, Xception, ResNet50
)
from tensorflow.keras.applications import imagenet_utils
from tensorflow.keras.applications.inception_v3 import preprocess_input as inception_preprocess
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import matplotlib.pyplot as plt

image_path = "image.png"
model_name = "vgg16"

models = {
    "vgg16": VGG16,
    "vgg19": VGG19,
    "inception": InceptionV3,
    "xception": Xception,
    "resnet": ResNet50
}

if model_name not in models:
    raise ValueError(f"Choose one of {list(models.keys())}")

if model_name in ("inception", "xception"):
    input_shape = (299, 299)
    preprocess = inception_preprocess
else:
    input_shape = (224, 224)
    preprocess = imagenet_utils.preprocess_input

print(f"[INFO] Loading {model_name} model...")
model = models[model_name](weights="imagenet")

# load + preprocess image
print("[INFO] Preparing image...")
image = load_img(image_path, target_size=input_shape)
image = img_to_array(image)
image = np.expand_dims(image, axis=0)
image = preprocess(image)

# predict
print(f"[INFO] Classifying image with '{model_name}'...")
preds = model.predict(image)
results = imagenet_utils.decode_predictions(preds)[0]

print("\n=== Top Predictions ===")
for i, (_, label, prob) in enumerate(results, 1):
    print(f"{i}. {label}: {prob * 100:.2f}%")

# show result on image
top_label, top_prob = results[0][1], results[0][2]
orig = cv2.imread(image_path)
cv2.putText(orig, f"Label: {top_label}, {top_prob * 100:.2f}%",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
try:
    cv2.imshow("Classification", orig)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
except Exception as e:
    print("[INFO] cv2.imshow not available, showing with matplotlib...")
    plt.imshow(cv2.cvtColor(orig, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.show()


'''