import numpy as np
import cv2
import os
import datetime
from statistics import mean
import math

url='http://192.168.1.234:4747/video' #DroidCam Ip camera address
cap = cv2.VideoCapture(url)
if not cap.isOpened():
        print("Cannot open IP camera. Trying laptop camera...")
        #starting video capture from laptop webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
                print("Cannot open laptop camera")
                exit()
        print("Using laptop camera") 


#initializing some useful variables
waitkey_time=25
recording=False
pano=False
zoom=0
max_zoom=50
mode="i"
l_click=0
click_x=None
click_y=None
main_button_clicked=False
pk=-1
global filterr
filterr="o"
angle=0
sigx=0
sigy=0
max_sigx=26
max_sigy=26
blur=False
button_color=(255,255,255)
x_ksize=0
y_ksize=0
max_x_ksize=26
max_y_ksize=26
sobx=False
soby=False
thresh1=0
thresh2=0
max_thresh1=5000
max_thresh2=5000
canny=False
global pano_list
pano_list=[]
global dsum
dsum=0


#function for taking picture
def take_picture(frame_copy):
        global main_button_clicked, click_x, click_y
        #saving the picture taken with current datetime
        if filterr=="c":
                frame_date=frame_copy
        else:
                current_datetime=datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
                frame_date=cv2.putText(frame_copy, text=current_datetime, 
                                org=(frame.shape[1]-160,frame.shape[0]-10), fontFace=1, 
                                fontScale=1,
                                color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)

        #file handling for saving the picture taken : saved in ./media/images/n.jpg (n=0,1,2..)
        if not os.path.exists(os.getcwd()+"/media/images"):
                os.makedirs(os.getcwd()+"/media/images", exist_ok=True)
        l=os.listdir(os.getcwd()+"/media/images")
        if len(l)==0:
                i=str(0)
        else:
                i=str(max([int(each.split(".")[0]) for each in l])+1)
        cv2.imwrite(os.getcwd()+"/media/images/" + i + ".jpg", frame_date)        

        print("Image captured.")
        main_button_clicked=False
        click_x=None
        click_y=None

#function for taking video 
def take_video():
        global recording
        global out
        global main_button_clicked, click_x, click_y
        #if starting video record mode
        if recording==False:
                recording=True    
                #file handling for saving the recorded video : saved in ./media/videos/n.mp4 (n=0,1,2..)
                if not os.path.exists(os.getcwd()+"/media/videos"):
                        os.makedirs(os.getcwd()+"/media/videos", exist_ok=True)
                l=os.listdir(os.getcwd()+"/media/videos")
                if len(l)==0:
                        i=str(0)
                else:
                        i=str(max([int(each.split(".")[0]) for each in l])+1)
                #"mp4v" codec for saving recorded video
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(os.getcwd()+"/media/videos/" + i + ".mp4",
                        fourcc, 1000//waitkey_time, (frame.shape[1], frame.shape[0]))
                print("Recording started...")
        #if stopping record mode
        else:
                recording=False
                #releasing the videoWriter object
                out.release()
                print("Recording stopped...")
        main_button_clicked=False
        click_x=None
        click_y=None

#function for taking panorama
def take_pano():
        global pano
        global main_button_clicked, click_x, click_y
        global p0
        global old_frame_gray
        global mask
        global color
        global pano_img
        tomasi_params=dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7, useHarrisDetector = False)
        color=np.random.randint(0, 255, (100,3))
        #if starting pano record mode
        if pano==False:
                pano=True
                old_frame_copy=frame_copy
                old_frame_gray=cv2.cvtColor(old_frame_copy, cv2.COLOR_BGR2GRAY)
                pano_img=old_frame_copy
                p0=cv2.goodFeaturesToTrack(old_frame_gray, mask=None, **tomasi_params)
                if p0 is not None:
                        print("p0 detected")
                #for i,each in enumerate(p0):
                #        frame=cv2.circle(frame_copy, (int(each[0][0]), int(each[0][1])), 5, color[i].tolist(), -1)
                pano_list.append(old_frame_copy)
        else:
                pano=False
                stitcher=cv2.Stitcher_create()
                status, panorama=stitcher.stitch(pano_list)
                if status==0:
                        if not os.path.exists(os.getcwd()+"/media/panoramas/"):
                                os.makedirs(os.getcwd()+"/media/panoramas/", exist_ok=True)
                        l=os.listdir(os.getcwd()+"/media/panoramas")
                        if len(l)==0:
                                i=str(0)
                        else:
                                i=str(max([int(each.split(".")[0]) for each in l])+1)
                        cv2.imwrite(os.getcwd()+"/media/panoramas/" + i + ".jpg", panorama)                
                        cv2.imshow("panorama", panorama)
                        cv2.waitKey(0)


#function for tracking mouse clicks positions
def mouse_click(event,x,y,flags,params):
        global click_x,click_y
        if event==cv2.EVENT_LBUTTONDOWN:
                click_x=x
                click_y=y

#function for the zoom trackbar feature
def zoom_func(val):
        global zoom
        zoom=val/10
        if 1+zoom<=1:
                return frame
        cy, cx=[i/2 for i in frame.shape[:-1]]
        rot_mat=cv2.getRotationMatrix2D((cx,cy), angle=0,scale=1+zoom)
        zoom_frame=cv2.warpAffine(frame, rot_mat, frame.shape[1::-1], flags=cv2.INTER_LINEAR)
        return zoom_frame

#function for rotating the camera stream
def rotate_frame_nocutoff():
        global angle
        if angle==360:
                angle=0
        (h,w)=frame.shape[:2]
        (cx,cy)= (w//2,h//2)
        M=cv2.getRotationMatrix2D((cx,cy), angle, 1.0)
        cos=np.abs(M[0,0])
        sin=np.abs(M[0,1])
        nw=int((h*sin)+(w*cos))
        nh=int((h*cos)+(w*sin))
        M[0,2]+=(nw/2)-cx
        M[1,2]+=(nh/2)-cy
        rot_frame=cv2.warpAffine(frame, M, (nw,nh))
        return rot_frame
        
#function for applying gaussian blur to camera stream
def gauss_blur(valx=0,valy=0):
        global sigx,sigy
        sigx=valx+4
        sigy=valy+4
        if sigx<5 and sigy<5:
                return frame
        blur_frame=cv2.GaussianBlur(frame, (0,0), sigx, sigy)
        return blur_frame

#cv2 Sobel X function
def SobelX(x_kval):
        global x_ksize
        if x_kval%2!=0:
                x_ksize=x_kval+4
                if x_ksize<5:
                        return frame
                gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sobelx_frame=cv2.Sobel(gray, ddepth=-1, dx=1, dy=0, ksize=x_ksize)
                sobelx_frame=np.dstack([sobelx_frame]*3)
                return sobelx_frame
        else: return frame

#cv2 Sobel Y function
def SobelY(y_kval):
        global y_ksize
        if y_kval%2!=0:
                y_ksize=y_kval+4
                if y_ksize<5:
                        return frame
                gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sobely_frame=cv2.Sobel(gray, ddepth=-1, dx=0, dy=1, ksize=y_ksize)
                sobely_frame=np.dstack([sobely_frame]*3)
                return sobely_frame
        else: return frame

#Canny Edge function
def canny_edge(val1=0, val2=0):
        global thresh1, thresh2
        thresh1=round((val1-1)*(255)/(5000-1))
        thresh2=round((val2-1)*(255)/(5000-1))
        if thresh1<1 or thresh2<1:
                return frame
        canny_frame=cv2.Canny(frame, thresh1, thresh2)
        canny_frame=np.dstack([canny_frame]*3)
        return canny_frame

#function for getting derivative kernels for custom Sobel and Laplace operations 
def get_sobel_kernels(dx, dy, ksize, normalize, ktype):
    ksizeX, ksizeY = ksize, ksize
    if ksizeX == 1 and dx > 0:
        ksizeX = 3
    if ksizeY == 1 and dy > 0:
        ksizeY = 3

    assert ktype == cv2.CV_32F or ktype == cv2.CV_64F, "Invalid ktype"

    kx = np.zeros((ksizeX, 1), dtype=np.float32)
    ky = np.zeros((ksizeY, 1), dtype=np.float32)

    if ksize % 2 == 0 or ksize > 31:
        raise ValueError("The kernel size must be odd and not larger than 31")

    kerI = np.zeros(max(ksizeX, ksizeY) + 1, dtype=np.int32)

    assert dx >= 0 and dy >= 0 and dx + dy > 0, "Invalid dx and dy values"

    for k in range(2):
        kernel = kx if k == 0 else ky
        order = dx if k == 0 else dy
        ksize = ksizeX if k == 0 else ksizeY

        assert ksize > order, "Invalid ksize and order"

        if ksize == 1:
            kerI[0] = 1
        elif ksize == 3:
            if order == 0:
                kerI[0] = 1
                kerI[1] = 2
                kerI[2] = 1
            elif order == 1:
                kerI[0] = -1
                kerI[1] = 0
                kerI[2] = 1
            else:
                kerI[0] = 1
                kerI[1] = -2
                kerI[2] = 1
        else:
            kerI[0] = 1
            for i in range(ksize):
                kerI[i + 1] = 0

            for i in range(ksize - order - 1):
                oldval = kerI[0]
                for j in range(1, ksize + 1):
                    newval = kerI[j] + kerI[j - 1]
                    kerI[j - 1] = oldval
                    oldval = newval

            for i in range(order):
                oldval = -kerI[0]
                for j in range(1, ksize + 1):
                    newval = kerI[j - 1] - kerI[j]
                    kerI[j - 1] = oldval
                    oldval = newval

        temp = np.array(kerI[:ksize], dtype=np.int32)
        scale = 1.0 if not normalize else 1. / (1 << (ksize - order - 1))
        kernel[:, 0] = temp * scale

    return kx, ky


#custom sobel operation
def custom_Sobel(frame, ktype="x", ksize=3):
        if ktype=="x":
                kx,ky=get_sobel_kernels(1,0,ksize,False, cv2.CV_64F)
                kernel=(ky)*np.transpose(kx)
                gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                res=cv2.filter2D(gray, -1, kernel)
                res=np.dstack([res]*3)
                return res
        elif ktype=="y":
                kx,ky=get_sobel_kernels(0,1,ksize,False, cv2.CV_64F)
                kernel=(ky)*np.transpose(kx)
                gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                res=cv2.filter2D(gray, -1, kernel)
                res=np.dstack([res]*3)
                return res
#custom laplace operation
def custom_Laplace(frame, ksize=3):
        kx,ky=get_sobel_kernels(2,0,ksize,False, cv2.CV_64F)
        kernelx=(ky)*np.transpose(kx)
        kx,ky=get_sobel_kernels(0,2,ksize,False, cv2.CV_64F)
        kernely=(ky)*np.transpose(kx)
        gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resx=cv2.filter2D(gray, -1, kernelx)
        resy=cv2.filter2D(gray, -1, kernely)
        res=resx+resy
        res=np.dstack([res]*3)
        return res

       
#initializing the app screen window "frame"
cv2.namedWindow("frame")
#initializing the zoom functionality trackbar
zoom_bar='Zoom'
cv2.createTrackbar(zoom_bar, "frame", zoom, max_zoom, zoom_func)
#initializing listening for mouse clicks on app screen
cv2.setMouseCallback('frame', mouse_click)
#SigmaX parameter trackbar for gaussian blur
sigx_bar="SigmaX (+4)"
cv2.createTrackbar(sigx_bar, "frame", sigx, max_sigx, gauss_blur)  
#SigmaY parameter trackbar for gaussian blur
sigy_bar="SigmaY (+4)"
cv2.createTrackbar(sigy_bar, "frame", sigy, max_sigy, gauss_blur)  
#kernal size parameter trackbar for Sobel X
sobx_ksize="SobX k-size (+4)"
cv2.createTrackbar(sobx_ksize, "frame", x_ksize, max_x_ksize, SobelX)
#kernal size parameter trackbar for Sobel Y
soby_ksize="SobY k-size (+4)"
cv2.createTrackbar(soby_ksize, "frame", y_ksize, max_y_ksize, SobelY)
#threshold1 parameter trackbar for Canny edge detector
canny_thresh1="Canny thresh-1"
cv2.createTrackbar(canny_thresh1, "frame", thresh1, max_thresh1, canny_edge)
#threshold2 parameter trackbar for Canny edge detector
canny_thresh2="Canny thresh-2"
cv2.createTrackbar(canny_thresh2, "frame", thresh2, max_thresh2, canny_edge)



#looping over the video capture from webcam
while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

        #getting the current position of trackbar needle and updating zoom accordingly
        val=cv2.getTrackbarPos(zoom_bar, 'frame')
        frame=zoom_func(val)

        #getting the current position of SigmaX and SigmaY (gaussian blur) trackbar needles
        valx=cv2.getTrackbarPos(sigx_bar, 'frame')
        valy=cv2.getTrackbarPos(sigy_bar, 'frame')
        #if "b" pressed then apply a gaussian blur to camera stream
        if blur==True:
                frame=gauss_blur(valx,valy)
        
        #getting current position of trackbar for Sobel kernel size
        x_kval=cv2.getTrackbarPos(sobx_ksize, 'frame')
        #if "s+x" pressed then apply a SobelX to camera stream
        if sobx==True:
                frame=SobelX(x_kval)

        #getting current position of trackbar for SobelY kernel size
        y_kval=cv2.getTrackbarPos(soby_ksize, 'frame')
        #if "s+y" pressed then apply a SobelY to camera stream
        if soby==True:
                frame=SobelY(y_kval)

        #geting current posiions of thresh1 and thresh2 for Canny edge detection
        val1=cv2.getTrackbarPos(canny_thresh1, "frame")
        val2=cv2.getTrackbarPos(canny_thresh2, "frame")
        #if "e" is pressed apply Canny edge detection
        if canny==True:
                frame=canny_edge(val1, val2)
        


        #rotating camera stream without cutting the edges of the frame
        frame=rotate_frame_nocutoff()

        #filters-------------------------------------------------------------------------------------------
        # original (no filter)
        if filterr=="o":
                pass
        # custom filter (lab2-part1-features added as filter for ease of use)
        elif filterr=="c":
                #adding datetime to app screen instead of just the captured pictures or videos
                current_datetime=datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
                frame=cv2.putText(frame, text=current_datetime, 
                        org=(frame.shape[1]-160,frame.shape[0]-10), fontFace=1, 
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                #copying datetime roi to top right of the app screen
                datetime_roi=frame[frame.shape[0]-40:frame.shape[0],frame.shape[1]-170:frame.shape[1]]
                frame[0:40,frame.shape[1]-170:frame.shape[1]]=datetime_roi
                #adding opencv logo to top left of app screen
                opencv_logo=cv2.imread("opencv_logo.png")
                opencv_logo=cv2.resize(opencv_logo, dsize=(60,60),interpolation=cv2.INTER_AREA)
                roi=frame[0:opencv_logo.shape[1],0:opencv_logo.shape[0]]
                blended_roi=cv2.addWeighted(roi, 0.7, opencv_logo, 0.3,0)
                frame[0:opencv_logo.shape[1],0:opencv_logo.shape[0]]=blended_roi
                #adding red border to the app screen
                frame=cv2.copyMakeBorder(frame,5,5,5,5,cv2.BORDER_CONSTANT, value=(0,0,255))
        # green color space filter
        elif filterr=="g":
                hsv=cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower_green=np.array([40, 40, 40])
                upper_green=np.array([70, 255, 255])
                mask=cv2.inRange(hsv, lower_green, upper_green)
                green_frame=cv2.bitwise_and(frame, frame, mask=mask)
                frame=green_frame
        # binary threshold filter (thresh=127, max_value=255)
        elif filterr=="t":
                gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                ret,thresh=cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                frame=np.dstack([thresh]*3)
        # 4-window filter (Original, SobelX, SobelY, Laplace)
        elif filterr=="4":
                #hardcoding kernel size=3 for this operations in this filter 
                img1=frame
                img2=custom_Sobel(frame, ktype="x", ksize=3)
                img3=custom_Sobel(frame, "y", 3)
                img4=custom_Laplace(frame, ksize=3)
                hort1=np.concatenate((img1, img2),axis=1)
                hort2=np.concatenate((img3,img4), axis=1)
                vert=np.concatenate((hort1,hort2), axis=0)
                frame=vert
        # surf feature object detection
        elif filterr=="d":
                img_object=cv2.imread("book.png")
                obj_gray=cv2.cvtColor(img_object, cv2.COLOR_BGR2GRAY)
                frame_gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                surf=cv2.xfeatures2d.SURF_create()
                #surf.setExtended(True)
                kp1, des1=surf.detectAndCompute(obj_gray,None)
                kp2, des2=surf.detectAndCompute(frame_gray,None)
                FLANN_INDEX_KDTREE = 1
                index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
                search_params = dict(checks=50)
                flann = cv2.FlannBasedMatcher(index_params,search_params)
                matches = flann.knnMatch(des1,des2,k=2)
                matchesMask = [[0,0] for i in range(len(matches))]
                good_matches=[]
                for i,(m,n) in enumerate(matches):
                        if m.distance < 0.7*n.distance:
                                matchesMask[i]=[1,0]
                                good_matches.append(m)
                draw_params = dict(matchColor = (0,255,0),
                                        singlePointColor = (0,0,255),
                                        matchesMask = matchesMask,
                                        flags = cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
                res = cv2.drawMatchesKnn(img_object,kp1,frame,kp2,matches,None,**draw_params)
                if len(good_matches)>3:
                        # get keypoints from good matches
                        obj=np.empty((len(good_matches),2), dtype=np.float32)
                        scene = np.empty((len(good_matches),2), dtype=np.float32)
                        for i in range(len(good_matches)):
                                obj[i,0] = kp1[good_matches[i].queryIdx].pt[0]
                                obj[i,1] = kp1[good_matches[i].queryIdx].pt[1]
                                scene[i,0] = kp2[good_matches[i].trainIdx].pt[0]
                                scene[i,1] = kp2[good_matches[i].trainIdx].pt[1]
                        # using Homography to draw a bounding box around detected object
                        H, _ = cv2.findHomography(obj, scene, cv2.RANSAC)
                        #-- Get the corners from the image_1 ( the object to be "detected" )
                        if H is not None:
                                obj_corners = np.empty((4,1,2), dtype=np.float32)
                                obj_corners[0,0,0] = 0
                                obj_corners[0,0,1] = 0
                                obj_corners[1,0,0] = img_object.shape[1]
                                obj_corners[1,0,1] = 0
                                obj_corners[2,0,0] = img_object.shape[1]
                                obj_corners[2,0,1] = img_object.shape[0]
                                obj_corners[3,0,0] = 0
                                obj_corners[3,0,1] = img_object.shape[0]
                                scene_corners = cv2.perspectiveTransform(obj_corners, H)
                                #-- Draw lines between the corners (the mapped object in the scene - image_2 )
                                cv2.line(res, (int(scene_corners[0,0,0] + img_object.shape[1]), int(scene_corners[0,0,1])), (int(scene_corners[1,0,0] + img_object.shape[1]), int(scene_corners[1,0,1])), (0,255,0), 4)
                                cv2.line(res, (int(scene_corners[1,0,0] + img_object.shape[1]), int(scene_corners[1,0,1])), (int(scene_corners[2,0,0] + img_object.shape[1]), int(scene_corners[2,0,1])), (0,255,0), 4)
                                cv2.line(res, (int(scene_corners[2,0,0] + img_object.shape[1]), int(scene_corners[2,0,1])), (int(scene_corners[3,0,0] + img_object.shape[1]), int(scene_corners[3,0,1])), (0,255,0), 4)
                                cv2.line(res, (int(scene_corners[3,0,0] + img_object.shape[1]), int(scene_corners[3,0,1])), (int(scene_corners[0,0,0] + img_object.shape[1]), int(scene_corners[0,0,1])), (0,255,0), 4)
                frame=res
                



        #---------------------------------------------------------------------------------------------------

        #frame copy
        frame_copy=frame.copy()

        #visual button features
        frame=cv2.rectangle(frame, (10, frame.shape[0]-40), (80,frame.shape[0]-10), button_color, -1)
        frame=cv2.putText(frame, text="mode",
                        org=(25, frame.shape[0]-50), fontFace=1,
                        fontScale=1,
                        color=button_color, thickness=1, lineType=cv2.LINE_AA)
        #slight modification on main button to account for the partition lines in "4-window" filter
        if filterr!="4":
                frame=cv2.circle(frame, (frame.shape[1]//2,frame.shape[0]-50), 30, button_color, 2)
                frame=cv2.circle(frame, (frame.shape[1]//2,frame.shape[0]-50), 25, button_color, -1)
        frame=cv2.putText(frame, text="filter:",
                        org=(10, frame.shape[0]-80), fontFace=1,
                        fontScale=1,
                        color=button_color, thickness=1, lineType=cv2.LINE_AA)
        
        #display feature for filter toggle (shows filter)--------------------------------------------
        #original
        if filterr=="o":
                frame=cv2.putText(frame, text="og",
                        org=(60, frame.shape[0]-80), fontFace=1,
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                button_color=(255,255,255)
        #lab-2 custom
        elif filterr=="c":
                frame=cv2.putText(frame, text="custom",
                        org=(60, frame.shape[0]-80), fontFace=1,
                        fontScale=1,
                        color=(0,0,255), thickness=1, lineType=cv2.LINE_AA)
                button_color=(255,255,255)
        #green-space
        elif filterr=="g":
                frame=cv2.putText(frame, text="green-space",
                        org=(60, frame.shape[0]-80), fontFace=1,
                        fontScale=1,
                        color=(0,255,0), thickness=1, lineType=cv2.LINE_AA)
                button_color=(255,255,255)
        #thresholding-binary
        elif filterr=="t":
                frame=cv2.putText(frame, text="thresh-binary",
                        org=(60, frame.shape[0]-80), fontFace=1,
                        fontScale=1,
                        color=(255,0,0), thickness=1, lineType=cv2.LINE_AA)
                button_color=(255,0,0)
        #4-window spatial gradients(Original, SobelX, SobelY, Laplacian)
        elif filterr=="4":
                frame=cv2.putText(frame, text="spatial-gradients",
                        org=(60, frame.shape[0]-80), fontFace=1,
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                frame=cv2.putText(frame, text="Original",
                        org=(20,20), fontFace=1,
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                frame=cv2.putText(frame, text="Sobel-X",
                        org=(frame.shape[1]//2+20,20), fontFace=1,
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                frame=cv2.putText(frame, text="Sobel-Y",
                        org=(20,frame.shape[0]//2+20), fontFace=1,
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                frame=cv2.putText(frame, text="Laplace",
                        org=(frame.shape[1]//2+20,frame.shape[0]//2+20), fontFace=1,
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                frame=cv2.line(frame, (0,frame.shape[0]//2), 
                        (frame.shape[1],frame.shape[0]//2), 
                        color=(0,0,255), thickness=3)
                frame=cv2.line(frame, (frame.shape[1]//2,0), 
                        (frame.shape[1]//2,frame.shape[0]), 
                        color=(0,0,255), thickness=3)
                frame=cv2.circle(frame, (frame.shape[1]//2,frame.shape[0]-50), 30, button_color, 2)
                frame=cv2.circle(frame, (frame.shape[1]//2,frame.shape[0]-50), 25, button_color, -1)
                button_color=(255,255,255)
        #surf feature object detection
        elif filterr=="d":
                frame=cv2.putText(frame, text="surf",
                        org=(60, frame.shape[0]-80), fontFace=1,
                        fontScale=1,
                        color=(255,255,255), thickness=1, lineType=cv2.LINE_AA) 
                button_color=(255,255,255)
  

        #--------------------------------------------------------------------------------------------
                
        #display feature for mode toggle (shows mode: image or video)--------------------------------
        if mode=="i":
                frame=cv2.putText(frame, text="IMG",
                        org=(20, frame.shape[0]-15), fontFace=1,
                        fontScale=2,
                        color=(0,0,0), thickness=2, lineType=cv2.LINE_AA)
        elif mode=="v":
                frame=cv2.putText(frame, text="VID",
                        org=(20, frame.shape[0]-15), fontFace=1,
                        fontScale=2,
                        color=(0,0,0), thickness=2, lineType=cv2.LINE_AA)
        elif mode=="p":
                frame=cv2.putText(frame, text="PAN",
                        org=(20, frame.shape[0]-15), fontFace=1,
                        fontScale=2,
                        color=(0,0,0), thickness=2, lineType=cv2.LINE_AA)

        #-------------------------------------------------------------------------------------------

        #processing if video record mode has started
        if recording==True:
                mode="v"
                if filterr=="c":
                        frame_date=frame_copy
                else:
                        #putting datetime in the video frame  being recorded
                        current_datetime=datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
                        frame_date=cv2.putText(frame_copy, text=current_datetime, 
                                org=(frame.shape[1]-160,frame.shape[0]-10), fontFace=1, 
                                fontScale=1,
                                color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)
                #writing the frame to the video being saved
                out.write(frame_date)
                #Just a visual feature on app screen showing it is recording video
                frame_rec=cv2.putText(frame, text="REC",
                        org=(frame.shape[1]-40, 20), fontFace=1,
                        fontScale=1,
                        color=button_color, thickness=1, lineType=cv2.LINE_AA)
                frame_rec=cv2.circle(frame_rec, (frame.shape[1]-50,15), 5, (0,0,255), thickness=-1)
                #main button becomes red when video is being recorded
                frame_rec=cv2.circle(frame_rec, (frame.shape[1]//2,frame.shape[0]-50), 25, (0,0,255), -1) 
                frame=frame_rec
        
        #processing if pano mode has started
        if pano==True:
                global pano_img
                cam_moved=False
                tomasi_params=dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7, useHarrisDetector = False)
                lk_params=dict(winSize=(15,15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT, 10, 0.03))
                mode="p"
                new_frame_copy=frame_copy        
                new_frame_gray=cv2.cvtColor(frame_copy, cv2.COLOR_BGR2GRAY)
                p1, st, err=cv2.calcOpticalFlowPyrLK(old_frame_gray, new_frame_gray, p0, None, **lk_params)
                if p1 is not None:
                        #print("p1 detected")
                        good_new=p1[st==1]
                        good_old=p0[st==1]
                        for i, (new, old) in enumerate(zip(good_new, good_old)):
                                a, b = new.ravel()
                                c, d = old.ravel()
                                #frame = cv2.circle(frame, (int(c), int(d)), 5, color[i].tolist(), -1)
                                d=math.sqrt((a-c)**2+(b-d)**2)
                                xd=abs(a-c)
                                if xd<5: xd=0
                                dsum+=xd
                                if d>=20:
                                        cam_moved=True        
                old_frame_gray=new_frame_gray.copy()
                if cam_moved:
                        print("camera moved")
                        p0=cv2.goodFeaturesToTrack(old_frame_gray, mask=None, **tomasi_params)
                        if p0 is not None:
                                print("new frame features detected")
                        #for i,each in enumerate(p0):
                        #        frame=cv2.circle(frame_copy, (int(each[0][0]), int(each[0][1])), 5, color[i].tolist(), -1) 
                        pano_list.append(new_frame_copy) 
                else:
                        p0=good_new.reshape(-1,1,2)
                frame=cv2.circle(frame, (frame.shape[1]//2,frame.shape[0]-50), 25, (0,0,255), -1)                 
                frame=cv2.line(frame, (0,frame.shape[0]//2), (frame.shape[1],frame.shape[0]//2), color=(0,255,255))
                frame=cv2.circle(frame, (5+int(0.01*dsum),frame.shape[0]//2), 10, (255,255,255), -1)

        #toggle mode(image-->video-->pano) when mode button is clicked
        if not (click_x==None or click_y==None):
                if  click_x>=10 and click_x<=80 and click_y>=frame.shape[0]-40 and click_y<=frame.shape[0]-10:
                        if mode=="i":
                                mode="v"
                        elif mode=="v": 
                                mode="p"
                        else:
                                mode="i"
                        click_x,click_y=None,None

        #recognize when main button is clicked
        if not (click_x==None or click_y==None):
                if (click_x-(frame.shape[1]//2))**2 + (click_y-(frame.shape[0]-50))**2 <=(30)**2:
                        main_button_clicked=True
                        click_x,click_y=None,None
                        

        #app screen displaying video capture (displaying frame every 25ms)
        cv2.imshow('frame', frame)
        k=cv2.waitKey(waitkey_time)
        
        #print("ord- ", k)                      #uncomment if want to print button press
        #if k!=-1: print("chr- ", chr(k))
        
        #main button clicked in image mode
        if mode=="i" and main_button_clicked:
                pk=ord("c")
                main_button_clicked=False
        #main button clicked in video mode
        if mode=="v" and main_button_clicked:
                pk=ord("v")
                main_button_clicked=False
        #main button clicked in pano mode
        if mode=="p" and main_button_clicked:
                pk=ord("p")
                main_button_clicked=False
        #app-features--------------------------------------------------------------------------------
        
        #feature:  press "Esc" for closing app
        if k==27:
                cap.release()
                cv2.destroyAllWindows()
        #feature: press "c" or main button in image mode for taking a picture
        elif k==ord("c") or pk==ord("c"):
                mode="i"
                take_picture(frame_copy)
                if filterr=="t":
                        frame[:,:]=255
                else:
                        #flashing app screen when picture is taken
                        frame[:,:]=[255,255,255]
                cv2.imshow("frame",frame)
                cv2.waitKey(1)
        #feature: press "v" or main button in video mode for taking a video (start and stop)
        elif k==ord("v") or pk==ord("v"):
                take_video()
        #feature: press "p" or main button in pano mode for taking a panorama (start and stop)
        elif k==ord("p") or pk==ord("p"):
                take_pano()
        #feature: press "g" to get green color space filter 
        elif k==ord("g"):
                if filterr=="g": filterr="o"
                else: filterr="g"
        #feature: press "t" to get binary threshold filter
        elif k==ord("t"):
                if filterr=="t": filterr="o"
                else: filterr="t"
        #feature: press "r" to rotate the camera stream by 10 degrees (anti-clockwise) 
        elif k==ord("r"):
                angle+=10
        #feature: press "b" to apply gaussian blur to camera stream (~trackbar adjustable)
        elif k==ord("b"):  
                blur= not blur
        #feature: press "s+x" for SobelX or "s+y" for SobelY
        elif k==ord("s"):
                s_clicked=True 
        elif k==-1:
                s_clicked=False
        elif k==ord("x") and s_clicked==True:
                sobx= not sobx
        elif k==ord("y") and s_clicked==True:
                soby=not soby
        #features: press "e" for Canny edge detection
        elif k==ord("e"):
                canny= not canny
        #feature: press "4" for 4-window spatial gradients
        elif k==ord("4"):
                if filterr=="4": filterr="o"
                else: filterr="4"
        #feature: press "d" for surf object detection
        elif k==ord("d"):
                if filterr=="d": filterr="o"
                else: filterr="d"        

        #feature: press "f" to toggle between original and different filters available
        if k==ord("f"):
                if filterr=="o":
                        filterr="c"
                elif filterr=="c":
                        filterr="g"
                elif filterr=="g":
                        filterr="t"
                elif filterr=="t":
                        filterr="4"
                elif filterr=="4":
                        filterr="d"
                elif filterr=="d":
                        filterr="o"
        #----------------------------------------------------------------------------------------

        #resetting pk=-1 once click functionality has finished
        pk=-1



