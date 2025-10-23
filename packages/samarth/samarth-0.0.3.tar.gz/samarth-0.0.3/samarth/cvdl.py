def p1():
    print(r"""#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#ORIGINAL TO SMALL
import cv2
import numpy as np
from google.colab.patches import cv2_imshow
original_image = cv2.imread('/content/lena.png')
small_image = np.zeros((256, 256, 3), dtype=np.uint8)

for i in range(0, original_image.shape[0], 2):
  for j in range(0, original_image.shape[1], 2):
    for k in range(0, 3):
      small_image[i//2][j//2][k] = np.mean(original_image[i:i+2, j:j+2, k])

print("Original Image:")
cv2_imshow(original_image)

print("Small Image:")
cv2_imshow(small_image)


# In[ ]:


import cv2
import numpy as np
from google.colab.patches import cv2_imshow

original_image = cv2.imread('/content/lena.png')

height, width = original_image.shape[:2]

large_image = np.zeros((height*2, width*2, 3), dtype=np.uint8)

for i in range(height):
    for j in range(width):
        for k in range(3):
            pixel = original_image[i, j, k]
            large_image[2*i, 2*j, k] = pixel
            large_image[2*i+1, 2*j, k] = pixel
            large_image[2*i, 2*j+1, k] = pixel
            large_image[2*i+1, 2*j+1, k] = pixel

print("Original Image:")
cv2_imshow(original_image)

print("Large Image:")
cv2_imshow(large_image)


# In[ ]:


#ORIGINAL TO GRAYSCALE
import cv2
import numpy as np
from google.colab.patches import cv2_imshow
original_image = cv2.imread('/content/lena.png')
gray_image = np.zeros((512, 512), dtype=np.uint8)

for i in range(0, original_image.shape[0]):
  for j in range(0, original_image.shape[1]):
      gray_image[i][j] = np.mean(original_image[i, j, 0:3])
print("Original Image:")
cv2_imshow(original_image)

print("GrayScale Image:")
cv2_imshow(gray_image)


# In[ ]:


#ORIGINAL TO 1/3
import cv2
import numpy as np
from google.colab.patches import cv2_imshow
original_image = cv2.imread('/content/lena.png')
small_image = np.zeros((171, 171, 3), dtype=np.uint8)

for i in range(0, original_image.shape[0], 3):
  for j in range(0, original_image.shape[1], 3):
    for k in range(0, 3):
      small_image[i//3][j//3][k] = np.mean(original_image[i:i+3, j:j+3, k])

print("Original Image:")
cv2_imshow(original_image)

print("Small Image:")
cv2_imshow(small_image)

""")