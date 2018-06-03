# This program uses the webcam to process color images at 960x720x3fps.
# Uses a simple detector to determine and save every image that is different enough from the previous one.
# It also saves an image every 5 seconds with no condition.
# Saves an high quality 640x480 copy on local machine and a very compressed copy on local and a remote machine.
# Estimated local<->server bandwidth usage with current parameters is 32kbps when no movement and 480kbps when maximum movement.
# Estimated server disk usage per day stored: 0,35GB - 5GB
# It also deletes images older than 2 days on the remote server to keep free space.
import cv2, time, datetime, os, threading

previousimage = None
THRESHOLD = 2.985       #set this parameter to adjust detector sensibility 

def playSound():
    # requires sudo apt install sox
    duration = .05
    freq = 660
    os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % (duration, freq))

def printDiff(diff, green): 
    if green:
        print('\033[92m', diff, '\033[0m')
    else:
        print(diff)

def deleteOld():
    print('Checking for old images to delete')
    #ssh user@remotehost "cd /home/user/lq && find -type f -printf '%T+ %p\n' | sort | head -n 1 | cut -d ' ' -f 2"
    oldestfiledate = os.popen('ssh user@remotehost \"cd /home/user/lq && find -type f -printf \'%T+ %p\n\' | sort | head -n 1 | cut -d \' \' -f 2\"').read()
    print('  oldest file on remote folder is ' + oldestfiledate + ' (date \'' + oldestfiledate[2:10] + '\')')
    oldestfiledatetime = datetime.datetime.strptime(oldestfiledate[2:10], '%Y%m%d')
    print('  oldestfiledatetime: ', oldestfiledatetime)
    currenttime = datetime.datetime.fromtimestamp(time.time())
    print('  currenttime       : ', currenttime)
    deltatime = currenttime - oldestfiledatetime
    print('  delta days        : ', deltatime.days)
    if  deltatime.days > 2:
        print('  deleting all images dated ' + oldestfiledate[2:10])
        os.popen('ssh user@remotehost \"cd /home/user/lq && rm '+oldestfiledate[2:10]+'*\"')

def saveImage(img):
    #print('Saving image')
    currenttime = time.time()
    filename = datetime.datetime.fromtimestamp(currenttime).strftime('%Y%m%d-%H%M%S.%f')[:-4]
    #print('  saving local high quality file...')
    cv2.imwrite('hq/'+filename+'.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    #print('  saving local low quality file...')
    cv2.imwrite('lq/'+filename+'.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
    #print('  saving remote low quality file...')
    thread = UploaderThread(filename)
    thread.daemon = True
    thread.start() 

class UploaderThread(threading.Thread):
    #using threads so the main loop doesnt wait the file to be uploaded
    def __init__(self, filename):
        super(UploaderThread, self).__init__()
        self.filename = filename

    def run(self):
        os.system('scp lq/'+self.filename+'.jpg user@remotehost:/home/user/lq/'+self.filename+'.jpg')

def calculateDiffhistg(image1, image2):
    prevhistg = cv2.calcHist([image1],[0],None,[256],[0,256])
    currhistg = cv2.calcHist([image2],[0],None,[256],[0,256])
    diffhistg = cv2.compareHist(prevhistg,currhistg,cv2.HISTCMP_CORREL) 
    prevhistg = cv2.calcHist([image1],[1],None,[256],[0,256])
    currhistg = cv2.calcHist([image2],[1],None,[256],[0,256])
    diffhistg += cv2.compareHist(prevhistg,currhistg,cv2.HISTCMP_CORREL)
    prevhistg = cv2.calcHist([image1],[2],None,[256],[0,256])
    currhistg = cv2.calcHist([image2],[2],None,[256],[0,256])
    diffhistg += cv2.compareHist(prevhistg,currhistg,cv2.HISTCMP_CORREL)
    return diffhistg

def getMyWebcamIdx():
    webcamfound = False
    for i in range (0, 5):
        msg = os.popen('udevadm info --query=all /dev/video'+str(i)+' | grep \'MODEL_ID\'').read()
        if  'ID_MODEL_ID=4095' in msg:
            webcamfound = True
            break
    if  webcamfound:
        return i
    else:
        return -1

def main():
    global previousimage
    counter = 0
    counterCheckDeleteOld = 0
    cam = cv2.VideoCapture(getMyWebcamIdx())
    cam.set(3,960)
    cam.set(4,720)
    while True:
        ret_val, img = cam.read()
        img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LANCZOS4)
        cv2.imshow('my webcam', img)
        if  previousimage is not None:
            diffhistg = calculateDiffhistg(previousimage, img)
            if  diffhistg < THRESHOLD:
                printDiff(diffhistg, True)
                #playSound()   
            else:
                printDiff(diffhistg, False)
            if  diffhistg < THRESHOLD or counter == 14:
                saveImage(img)
        previousimage = img
        if  counter == 14:
            #print('Counter reset. An image has been saved.')
            counter = 0
        else:
            counter += 1
        if  counterCheckDeleteOld == 9999:
            deleteOld()
            counterCheckDeleteOld = 0
        else:
            counterCheckDeleteOld += 1
        if  cv2.waitKey(1) == 27: 
            break  # esc to quit
        time.sleep(.33)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
