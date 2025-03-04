#! /usr/bin/python

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
from pathlib import Path

# import the necessary packages
from imutils import paths
import os

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "Unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())

# initialize the video stream and allow the camera sensor to warm up
# Set the ser to the followng
# src = 0 : for the build in single web cam, could be your laptop webcam
# src = 2 : I had to set it to 2 inorder to use the USB webcam attached to my laptop
#vs = VideoStream(src=0,framerate=10).start()
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

# loop over frames from the video file stream
unknowns = 1
img_counter = 0
recognizing = False
while True:
    # grab the frame from the threaded video stream and resize it
    # to 500px (to speedup processing)
    frame = vs.read()
    image = frame
    frame = imutils.resize(frame, width=500)
    # Detect the fce boxes
    boxes = face_recognition.face_locations(frame)
    # compute the facial embeddings for each face bounding box
    encodings = face_recognition.face_encodings(frame, boxes)
    names = []

    # loop over the facial embeddings
    for encoding in encodings:
        # attempt to match each face in the input image to our known
        # encodings
        matches = face_recognition.compare_faces(data["encodings"],
            encoding)
        name = "Unknown" #if face is not recognized, then print Unknown

        # check to see if we have found a match
        if True in matches:
            # find the indexes of all matched faces then initialize a
            # dictionary to count the total number of times each face
            # was matched
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            # loop over the matched indexes and maintain a count for
            # each recognized face face
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1

            # determine the recognized face with the largest number
            # of votes (note: in the event of an unlikely tie Python
            # will select first entry in the dictionary)
            name = max(counts, key=counts.get)

            #If someone in your dataset is identified, print their name on the screen
            if currentname != name:
                # if currentname == "Unknown":
                currentname = name
                print(currentname)
                os.system('echo %s | festival --tts & ' % "Hello, friend number {}".format(currentname))


        if name == "Unknown":
            Path("dataset/{}".format(unknowns)).mkdir(exist_ok=True)
            if not recognizing:
                recognizing = True
                os.system('echo %s | festival --tts & ' % 'hi. my name is towtwo. I am recognizing you')
            if True: #img_counter %2 == 1:
                img_name = "dataset/{}/image_{}.jpg".format(unknowns,img_counter)
                cv2.imwrite(img_name, image)
                print("{} written!".format(img_name))
                if img_counter >= 10:
                    # *********************** train the model
                    # our images are located in the dataset folder
                    os.system('echo %s | festival --tts & ' % "Facial recognition complete. You are now friend number {}".format(unknowns))
                    recognizing = False
                    unknowns += 1
                    print("[INFO] start processing faces...")
                    imagePaths = list(paths.list_images("dataset"))

                    # initialize the list of known encodings and known names
                    knownEncodings = []
                    knownNames = []

                    # loop over the image paths
                    for (i, imagePath) in enumerate(imagePaths):
                        # extract the person name from the image path
                        print("[INFO] processing image {}/{}".format(i + 1,
                            len(imagePaths)))
                        name = imagePath.split(os.path.sep)[-2]

                        # load the input image and convert it from RGB (OpenCV ordering)
                        # to dlib ordering (RGB)
                        image = cv2.imread(imagePath)
                        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                        # detect the (x, y)-coordinates of the bounding boxes
                        # corresponding to each face in the input image
                        boxes = face_recognition.face_locations(rgb,
                            model="hog")

                        # compute the facial embedding for the face
                        encodings = face_recognition.face_encodings(rgb, boxes)

                        # loop over the encodings
                        for encoding in encodings:
                            # add each encoding + name to our set of known names and
                            # encodings
                            knownEncodings.append(encoding)
                            knownNames.append(name)

                    # dump the facial encodings + names to disk
                    print("[INFO] serializing encodings...")
                    data = {"encodings": knownEncodings, "names": knownNames}
                    f = open("encodings.pickle", "wb")
                    f.write(pickle.dumps(data))
                    f.close()
                    img_counter = 0
            img_counter += 1

        # update the list of names
        names.append(name)

    # loop over the recognized faces
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # draw the predicted face name on the image - color is in BGR
        cv2.rectangle(frame, (left, top), (right, bottom),
            (0, 255, 225), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
            .8, (0, 255, 255), 2)

    # display the image to our screen
    cv2.imshow("Facial Recognition is Running", frame)
    key = cv2.waitKey(1) & 0xFF

    # quit when 'q' key is pressed
    if key == ord("q"):
        break

    # update the FPS counter
    fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
