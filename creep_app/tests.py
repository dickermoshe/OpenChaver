from time import time
from django.test import TestCase
import django
import os

# Create your tests here.
from creep_app.brain import OpenNsfw, skin_pixels ,splice_images
import cv2 as cv



# Define a test case
class TestOpenNsfw(TestCase):
    def test_open_nsfw(self):
        # Open a.png and b.png
        a = cv.imread("a.png")
        # Scale down the image
        a = cv.resize(a, (0,0), fx=0.5, fy=0.5)

        t = time()
        spliced_images = splice_images(a)
        print(len(spliced_images))
        print("Splice time: ", time() - t)

        t = time()
        print(skin_pixels(spliced_images))
        print("Skin time: ", time() - t)

        t = time()
        o = OpenNsfw()
        print('time to load model: ', time() - t)

        t = time()
        print(list(o.classify(spliced_images)))
        print("Predict time: ", time() - t)


