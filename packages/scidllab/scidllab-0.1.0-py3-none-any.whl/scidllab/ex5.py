#Ex-5

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


test_dir = r"dataset-1\val"
test_datagen = ImageDataGenerator(rescale=1./255)

test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),
    batch_size=32,
    class_mode="binary" ,#Depends on ur class 
    shuffle=False  
)


model = load_model("densenet169_cdd_coffee.hdf5")


loss, accuracy = model.evaluate(test_generator, steps=len(test_generator))
print(f"Test Loss: {loss:.4f}")
print(f"Test Accuracy: {accuracy*100:.2f}%")


preds = model.predict(test_generator, steps=len(test_generator), verbose=1)


y_pred = np.round(preds).astype(int).flatten()

y_true = test_generator.classes


cm = confusion_matrix(y_true, y_pred)
print("Confusion Matrix:")
print(cm)

plt.figure(figsize=(6,5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=list(test_generator.class_indices.keys()), 
            yticklabels=list(test_generator.class_indices.keys()))
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()

cr = classification_report(y_true, y_pred, target_names=list(test_generator.class_indices.keys()))
print("Classification Report:")
print(cr)


#EX6
#Ex-6
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.your_model import your_model, preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

model_path = r"your_model"     
test_dir = r"dataset-1\val"

model = load_model(model_path)
print("Model loaded successfully")

# Load your_pretrained_cnn_model base (used for feature extraction)
pretrained_cnn_base = yor_model(weights='imagenet', include_top=False, input_shape=(224,224,3))
print("your_pretrained_cnn_model Base model loaded for feature extraction!")

class_names = [
    'a',
    'b'
]

datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
test_gen = datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),
    batch_size=1,
    class_mode='binary',
    shuffle=False
)

features = pretrained_cnn_base.predict(test_gen, verbose=1)     
print("Feature extraction completed!")

predictions = model.predict(features, verbose=1)
predicted_classes = (predictions>0.5).astype(int).flatten()
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
print("Classification Report:")
print(classification_report(true_classes, predicted_classes, target_names=class_names))


#Ex7
#Ex-7
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.densenet import DenseNet201, preprocess_input
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
from pickle import load

# ------------------------------
# Load trained captioning model and tokenizer
# ------------------------------
model = load_model("model_captions_Ex7.hdf5")
model.summary()

with open('tokenizer_Ex7.pkl', 'rb') as handle:
    tokenizer = load(handle)

# ------------------------------
# Load DenseNet201 for feature extraction
# ------------------------------
base_model = DenseNet201(weights='imagenet', include_top=False, pooling='avg')

def extract_features(image_path):
    """Extract DenseNet201 features for a given image."""
    image = load_img(image_path, target_size=(224, 224))
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)
    feature = base_model.predict(image, verbose=0)
    return feature

# ------------------------------
# Caption generation helpers
# ------------------------------
max_length = 10  # same as training

def word_for_id(integer, tokenizer):
    """Map an integer to a word using the tokenizer."""
    for word, index in tokenizer.word_index.items():
        if index == integer:
            return word
    return None

def generate_caption(model, tokenizer, photo, max_length):
    """Generate a caption for an image feature."""
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

    caption = in_text.replace('startseq ', '').replace(' endseq', '')
    return caption

# ------------------------------
# Predict caption for a new image
# ------------------------------
image_path = "your path"  # Replace with your image path
photo_feature = extract_features(image_path)
caption = generate_caption(model, tokenizer, photo_feature, max_length)
print("Generated Caption:", caption)