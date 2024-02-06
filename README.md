# OpticFlow-pano
This projects involves capturing panorama in real-time (similar to Iphone). Panoramas are made by stiching a list of images captured (Using perspective transform and blending). Since a lot of images in the list to-stich a panorama makes the stiching slower, the idea is to use optical flow to detect a shift in camera(camera movement) and only select images after a constant shift. 

### Results
<img width="290" alt="image" src="https://github.com/tusharparimi/OpticFlow-pano/assets/93556280/a027ada3-6a79-48e4-b642-57cbb9201140">

### UI
<img width="143" alt="image" src="https://github.com/tusharparimi/OpticFlow-pano/assets/93556280/0f8b341f-2c1c-4683-bc84-ff4127202f9a">

### What Stitching looks like behind the scenes...
SIFT features are extracted and matched for a pair of images. Then necessary perspective transformation is found from perspective of one image to another. One of the images is transformed using that transformation and then blended with the other images. This is done for all pairs.

Ofcourse, the opencv stitcher used for real-time implementation in camera-app is more complex and of production grade but the basics remain similar :eyes:. 

<img width="310" alt="image" src="https://github.com/tusharparimi/OpticFlow-pano/assets/93556280/f6d30f4c-690a-4c48-ae4b-5855e75097d6">


### Implementation notes
- Used the sparse Optical Flow technique (Lucas-Kanade technique) in opencv for detecting the movement of camera sideways to get sequential images for planar panorama after some shift in camera.
- This is better as we do not need to include every frame in real time video capture to be used for stitching the panorama making the execution faster.
- The technique finds some features using the shi-tomasi method (similar to Harris corners) in the current frame then tracks the optical flow or displacement of these features while the camera is being shifted for panorama capture. If the features are displaced by a certain amount then this new frame is added to the stitching list. Now again features are detected and optical flow is observed and frame is added to the list. This continues till we close the panorama capture. The stitching is done using the opencv Stitcher class.
- You can press “p” to start the panorama capture or use mouse clicks to toggle to “pano” mode and use the main button to start and stop panorama capture. The panoramas after capture are saved in the media folder.
- A display feature similar to the Iphone is also added while capturing the panorama. A horizontal line with a marker on it that shifts with camera movement.

### Note
- Used the DroidCam app in Iphone to use the Iphone camera as an IP camera for the camera app, as using the laptop camera for panorama is difficult.
App link- https://apps.apple.com/us/app/droidcam-webcam-obs-camera/id1510258102
Use is simple just initialize the VideoCapture object in opencv with the url provided by the DroidCam app in Iphone (Laptop and Iphone should be connected to the same WIFI network). 
“url=’http://wifi_IP:Port/video’”  
“cap = cv2.VideoCapture(url)“

- This optical flow based panorama capture was implemented on top of the [camera-app](https://github.com/tusharparimi/camera-app) project. So please use the comments in code to check the code for just Panorama implementation.

