# This program uses the webcam to capture color images at 960x720x3fps and uses a simple motion detector to save
# every new image that is different enough from the previous one. It also saves one every 5 seconds unconditionally.
# 
# Local storing:  saves high quality 640x480 images on local machine.
# Remote storing: sends very compressed images to a remote server. It also removes old images to save space, keeping
# the last 3 days online: today, yesterday and before yesterday. Estimated server disk usage per day: 0,35GB - 5GB
# Estimated Internet bandwidth usage with current parameters goes from 32kbps to 480kbps (when maximum movement).

import cv2, time, datetime, os, threading

previousimage = None
consecutiveErrorsDeletingOld = 0  # Useful to stop uploading images if we can't delete the old ones.
THRESHOLD = 2.985  # Change this parameter to adjust the motion sensibility. Maximum sensibility is 3.0

def playSound():
    """Plays a sound. Duration in seconds. Frecuency in Hz. Requires sudo apt install sox."""
    duration = .05
    freq = 660
    os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % (duration, freq))

def printDiff(diff, green):
    """Prints text on the console with default color or green color."""
    if green:
        print('\033[92m', diff, '\033[0m')
    else:
        print(diff)

def deleteOld():
    """Checks on the remote server path for files older than before yesterday and deletes them to save space."""
    global consecutiveErrorsDeletingOld
    print('Checking for old images to delete')
    #ssh user@remotehost "cd /home/user/lq && find -type f -printf '%T+ %p\n' | sort | head -n 1 | cut -d ' ' -f 2"
    oldestfiledate = os.popen('ssh user@remotehost \"cd /home/user/lq && '
                              'find -type f -printf \'%T+ %p\n\' | sort | head -n 1 | cut -d \' \' -f 2\"').read()
    print('  oldest file on remote folder is ' + oldestfiledate + ' (date \'' + oldestfiledate[2:10] + '\')')
    try:
        oldestfiledatetime = datetime.datetime.strptime(oldestfiledate[2:10], '%Y%m%d')
        
    except ValueError as exception:
        consecutiveErrorsDeletingOld += 1
        print("There was an error retrieving the date of the oldest file on server.")
        print("This has happened the last " + consecutiveErrorsDeletingOld + " times we have tried.") 
    else:
        consecutiveErrorsDeletingOld = 0
        print('  oldestfiledatetime: ', oldestfiledatetime)
        currenttime = datetime.datetime.fromtimestamp(time.time())
        print('  currenttime       : ', currenttime)
        deltatime = currenttime - oldestfiledatetime
        print('  delta days        : ', deltatime.days)
        if  deltatime.days > 2:
            print('  deleting all images dated ' + oldestfiledate[2:10])
            os.popen('ssh user@remotehost \"cd /home/user/lq && rm ' + oldestfiledate[2:10] + '*\"')
        

def saveImage(img):
    """Saves hq image on local folder and sends lq image to server. Folders are created if they don't exist."""
    currenttime = time.time()
    filename = datetime.datetime.fromtimestamp(currenttime).strftime('%Y%m%d-%H%M%S.%f')[:-4]
    foldername = filename[:8]
    #Creates local folder if it doesn't exist
    os.system('mkdir hq >/dev/null 2>&1')
    os.system('cd hq && mkdir ' + foldername + '>/dev/null 2>&1')
    #Saves high quality image locally
    cv2.imwrite('hq/' + foldername + '/' + filename + '.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    #Creates temp folder if it doesn't exist
    os.system('mkdir temp >/dev/null 2>&1')
    #Saves low quality image to temp folder
    cv2.imwrite('temp/' + filename + '.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
    #Sends low quality image to server
    if consecutiveErrorsDeletingOld < 4:  #Condition to prevent overflowing the server storage space
        thread = UploaderThread(filename)
        thread.daemon = True
        thread.start() 

class UploaderThread(threading.Thread):
    """Uploads local file to server and then deletes the local file."""
    def __init__(self, filename):
        super(UploaderThread, self).__init__()
        self.filename = filename

    def run(self):
        os.system('scp temp/'+self.filename+'.jpg user@remotehost:/home/user/lq/' + self.filename
                  + '.jpg && rm temp/' + self.filename + '.jpg')

def calculateDiffhistg(image1, image2):
    """Compares image1 and image2 histograms on RGB channels. Returns value between 0 and 3 (meaning they are equal)."""
    diffhistg = 0
    for i in range(0,3):
        prevhistg = cv2.calcHist([image1],[i],None,[256],[0,256])
        currhistg = cv2.calcHist([image2],[i],None,[256],[0,256])
        diffhistg += cv2.compareHist(prevhistg,currhistg,cv2.HISTCMP_CORREL)
    return diffhistg

def getMyWebcamIdx():
    """Returns device index for the specific webcam that we want to use (e.g. ID_MODEL_ID=4095). 
       Because several webcams could be connected to the computer."""
    webcamfound = False
    for i in range (0, 5):
        msg = os.popen('udevadm info --query=all /dev/video' + str(i) + ' | grep \'MODEL_ID\'').read()
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
