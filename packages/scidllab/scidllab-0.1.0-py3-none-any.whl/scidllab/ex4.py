#Ex-4
from tensorflow.keras.applications import VGG16,VGG19,ResNet50,InceptionV3,Xception,imagenet_utils
from tensorflow.keras.applications.inception_v3 import preprocess_input
from tensorflow.keras.preprocessing.image import load_img,img_to_array
import numpy as np

model_name = "ResNet50"
path = "bird.jpg"

models = {
    "VGG16":(VGG16,(224,224),imagenet_utils.preprocess_input),
    "VGG19":(VGG19,(224,224),imagenet_utils.preprocess_input),
    "ResNet50":(ResNet50,(224,224),imagenet_utils.preprocess_input),
    "InceptionV3":(InceptionV3,(299,299),preprocess_input),
    "xception":(Xception,(299,299),preprocess_input)
}

model,size,preprocess = models[model_name]
Model = model(weights = "imagenet")
img = load_img(path,target_size = size)
arr = img_to_array(img)
img = np.expand_dims(arr,0)
img = preprocess(img)

preds = Model.predict(img)
decoded = imagenet_utils.decode_predictions(preds,top= 3)[0]

for (i,(id,label,prob)) in enumerate(decoded):
    print(f"{i+1} {label} : {prob*100:.2f}%")
    
