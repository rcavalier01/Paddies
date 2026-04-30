import cv2
import numpy as np
import serial
import time
import math

#thoughts
#add pseudo tracking so it has to be sure no green multiple times in a row

FRAME_SKIP = 5
HFOV = 60
#PORT = 'COM5'
#ser = serial.Serial(PORT, 9600, timeout = 1)
time.sleep(2)

#hsv thresholds
LOWER_THRESH = np.array([40,70,120])
UPPER_THRESH = np.array([90,255,255])

#get video stream from camera
capture = cv2.VideoCapture(1)

#Run Dalal Triggs HOG (pedestrian detection)
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

frame_count = 0
#x y w h for rectangle of interest (the image we search for green)
#x y is the location of the top left corner
current_roi = None
fired = False

def detect_human(frame):
    regions, weights = hog.detectMultiScale(frame, winStride=(8,8), padding=(0,0), scale=1.05)
    if len(regions) == 0:
        return None
    #filter small boxes and low confidence
    filtered = [(r, w) for r, w in zip(regions, weights) if w > 0.5 and r[2] * r[3] > 3000]
    if len(filtered) == 0:
        return None
    #return largest detection from multiplicative comp
    return max(filtered, key=lambda rw: rw[0][2] * rw[0][3])[0] 

def green_check(roi):
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_THRESH, UPPER_THRESH)
    green_pixels = cv2.countNonZero(mask)
    total_pixels = roi.shape[0] * roi.shape[1]
    ratio = green_pixels / total_pixels
    print("green ratio: ", ratio)
    #set ratio (right now 5% green is ok? lets test)
    return ratio > 0.05

while True:
    ret, frame = capture.read() 
    status = "init"
    color = (255,255,255)
    if not ret:
        break

    if fired:
        #draw everything on the last known frame before freezing
        if current_roi is not None:
            x, y, w, h = current_roi
            cx = x + w // 2
            cy = y + h // 2
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
        cv2.putText(frame, "FIRED - STOPPING CV",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Turret Vision", frame)
        cv2.waitKey(0)
        break

    frame_count += 1

    #dont get every frame to lessen throughput
    if frame_count % FRAME_SKIP == 0 or current_roi is None:
        roi_box = detect_human(frame)
        if roi_box is not None:
            current_roi = roi_box

        #once you have a target do green detection
        if current_roi is not None:
            x, y, w, h = current_roi
            cx = x + w // 2  # 
            cy = y + h // 2
            roi = frame[y:y+h, x:x+w]

            has_green = green_check(roi)

            if has_green:
                status = "SAFE (Green)"
                fire = False
                color = (0, 255, 0)
            else:
                status = "TARGET (no green)"
                fire = True
                color = (0, 0, 255)

            if fire:
                fired = True
                frame_width = frame.shape[1]
                #negative left, positive right (from cent)
                offset_px = cx - frame_width // 2
                #use fov to get offset to angle
                angle = (offset_px / frame_width) * HFOV
                round(angle, 1)
                message = f"F:{angle:.1f}\n"
                #once we expand to track vs fire rotation, use
                #char type = string.charAt(0); or substring(0,1)
                #ser.write(message.encode())
                print("Sent:", message.strip())
                #print("Sent fire command, status: ", status, "center: (", cx, ", ", cy, ")\n")
    #end of detect human / green loop
    if current_roi is not None:
        x, y, w, h = current_roi
        cx = x + w // 2
        cy = y + h // 2
        #draw box and center point for turret rotation calculation
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
    
    #print("status: ", status,"\n")
    cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Turret Vision", frame)
    #wait 1 ms and allow for exit or processing
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print(status)
#ser.close()
capture.release()
cv2.destroyAllWindows()
