

from keras.applications.vgg16 import VGG16, preprocess_input
from keras.preprocessing.image import load_img, img_to_array
from keras.models import Model, Sequential
from keras.layers import Dense
import matplotlib.pyplot as plt
from numpy import expand_dims
import numpy as np

# ==========================================================
# 1️⃣ Load and summarize VGG16 model
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
# 2️⃣ Visualize Filters from Second Layer
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
# 3️⃣ Feature Maps from the First Convolutional Layer
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
# 4️⃣ Feature Maps from Multiple Convolutional Blocks
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
# 5️⃣ Simple Sequential Dense Model Visualization (Manual)
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

print("\n✅ All visualizations completed using only Matplotlib!")
