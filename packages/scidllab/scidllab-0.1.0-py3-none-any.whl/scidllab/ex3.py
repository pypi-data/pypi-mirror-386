from numpy import expand_dims
from tensorflow.keras.preprocessing.image import load_img,img_to_array,ImageDataGenerator
import matplotlib.pyplot as plt
# Horizontal 
img = load_img("bird.jpg")
arr = img_to_array(img)
samples = expand_dims(arr,0)
datagen = ImageDataGenerator(zoom_range = [1,2])
it = datagen.flow(samples,batch_size = 1)
for i in range(9):
    plt.subplot(330+1+i)
    batch = next(it)
    shifted_img = batch[0].astype('uint8')
    plt.imshow(shifted_img)
plt.show()
# In ImageDatagenerator
# Horizontal - width_shift_range
#Horizontal flip  - horizontal_flip = True
#random rotation - rotation_range = 90
#Brightness - brightness_range = [0.2,0.4]
#random zooming = zoom_range = [0.2,0.5]