from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
import os


def extract_color_histogram(image, bins=(8, 8, 8)):
    # extract a 3D color histogram from the HSV color space using
    # the supplied number of `bins` per channel
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], None, bins,
                        [0, 180, 0, 256, 0, 256])

    # handle normalizing the histogram if we are using OpenCV 2.4.X
    if imutils.is_cv2():
        hist = cv2.normalize(hist)

    # otherwise, perform "in place" normalization in OpenCV 3 (I
    # personally hate the way this is done
    else:
        cv2.normalize(hist, hist)

    # return the flattened histogram as the feature vector
    return hist.flatten()


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dataset", required=True,
                help="path to input dataset")
args = vars(ap.parse_args())

# grab the list of images that we'll be describing
print("[INFO] describing images...")
imagePaths = list(paths.list_images(args["dataset"]))

# initialize the data matrix and labels list
data = []
labels = []

# loop over the input images
for (i, imagePath) in enumerate(imagePaths):
    # load the image and extract the class label (assuming that our
    # path as the format: /path/to/dataset/{class}.{image_num}.jpg
    image = cv2.imread(imagePath)
    label = imagePath.split(os.path.sep)[-1].split(".")[0]

    # extract a color histogram from the image, then update the
    # data matrix and labels list
    hist = extract_color_histogram(image)
    data.append(hist)
    labels.append(label)

    # show an update every 1,000 images
    if i > 0 and i % 1000 == 0:
        print("[INFO] processed {}/{}".format(i, len(imagePaths)))

# encode the labels, converting them from strings to integers
le = LabelEncoder()
labels = le.fit_transform(labels)

# partition the data into training and testing splits, using 75%
# of the data for training and the remaining 25% for testing
print("[INFO] constructing training/testing split...")
(trainData, testData, trainLabels, testLabels) = train_test_split(
    np.array(data), labels, test_size=0.25, random_state=42)

# train a Stochastic Gradient Descent classifier using a softmax
# loss function and 10 epochs
model = SGDClassifier(loss="log", random_state=967)
model.fit(trainData, trainLabels)

# evaluate the classifier
print("[INFO] evaluating classifier...")
predictions = model.predict(testData)
print(classification_report(testLabels, predictions,
                            target_names=le.classes_))

# to demonstrate that our classifier actually "learned" from
# our training data, randomly sample a few training images
idxs = np.random.choice(np.arange(0, len(trainData)), size=(5,))

labels_back = le.inverse_transform(trainLabels)
print(labels_back)

# loop over the training indexes
for i in idxs:
    # predict class probabilities based on the extracted color
    # histogram
    hist = trainData[i].reshape(1, -1)
    (catProb, dogProb) = model.predict_proba(hist)[0]
    #print(trainLabels[i])

    # show the predicted probabilities along with the actual
    # class label
    print("cat={:.1f}%, dog={:.1f}%, actual={}".format(catProb * 100,
                                                       dogProb * 100, labels_back[i]))
