from numpy import expand_dims
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
import matplotlib.pyplot as plt

# Load and preprocess the image
img = load_img("bird.jpg")
arr = img_to_array(img)
samples = expand_dims(arr, 0)

# ---- 1️⃣ Horizontal Shift ----
datagen = ImageDataGenerator(width_shift_range=0.3)
it = datagen.flow(samples, batch_size=1)
plt.figure(figsize=(8, 8))
for i in range(9):
    plt.subplot(3, 3, i+1)
    batch = next(it)
    plt.imshow(batch[0].astype('uint8'))
    plt.axis('off')
plt.suptitle("Horizontal Shift")
plt.show()

# ---- 2️⃣ Horizontal Flip ----
datagen = ImageDataGenerator(horizontal_flip=True)
it = datagen.flow(samples, batch_size=1)
plt.figure(figsize=(8, 8))
for i in range(9):
    plt.subplot(3, 3, i+1)
    batch = next(it)
    plt.imshow(batch[0].astype('uint8'))
    plt.axis('off')
plt.suptitle("Horizontal Flip")
plt.show()

# ---- 3️⃣ Random Rotation ----
datagen = ImageDataGenerator(rotation_range=90)
it = datagen.flow(samples, batch_size=1)
plt.figure(figsize=(8, 8))
for i in range(9):
    plt.subplot(3, 3, i+1)
    batch = next(it)
    plt.imshow(batch[0].astype('uint8'))
    plt.axis('off')
plt.suptitle("Random Rotation")
plt.show()

# ---- 4️⃣ Brightness Variation ----
datagen = ImageDataGenerator(brightness_range=[0.2, 0.4])
it = datagen.flow(samples, batch_size=1)
plt.figure(figsize=(8, 8))
for i in range(9):
    plt.subplot(3, 3, i+1)
    batch = next(it)
    plt.imshow(batch[0].astype('uint8'))
    plt.axis('off')
plt.suptitle("Brightness Variation")
plt.show()

# ---- 5️⃣ Random Zoom ----
datagen = ImageDataGenerator(zoom_range=[0.2, 0.5])
it = datagen.flow(samples, batch_size=1)
plt.figure(figsize=(8, 8))
for i in range(9):
    plt.subplot(3, 3, i+1)
    batch = next(it)
    plt.imshow(batch[0].astype('uint8'))
    plt.axis('off')
plt.suptitle("Random Zoom")
plt.show()
