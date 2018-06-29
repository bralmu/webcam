# This program converts the local images to video.
# A video file is more practical and light than storing the images in tens of thousands of individual jpg files 
# for each day recorded.
# This program automatically explores all dated folders (older than today) and, if it has not been done yet,
# creates a mkv/xvid video file and deletes the jpg files.
# It also adds hardcoded timestamps on the video to keep that info that previously was implicit in the jpg file name.

import cv2
import glob, sys, os
import time, datetime
import re


IMAGESPATH = os.getcwd() + "/hq"


def createVideo(path):
    """Creates a mpeg4 video file using the jpg images."""
    yyyymmdd = path[-9:-1]
    print("Creating video for day " + yyyymmdd)
    sys.stdout.write("    Loading image list...  \r")
    sys.stdout.flush()
    imagefileslist = glob.glob(path + "*.jpg")
    previousprogress = -1
    currentframe = 0
    totalframes = len(imagefileslist)
    print("    Loading image list...  " + str(totalframes) + " images found.")
    print("    Sorting image list...")
    imagefileslist.sort()
    print("    Creating video file...")
    try:
        videofile = path + yyyymmdd + ".mkv"
        w = cv2.VideoWriter(videofile, cv2.VideoWriter_fourcc('X','V','I','D'), 50, (640,480), True)
        font = cv2.FONT_HERSHEY_SIMPLEX
        for imagefile in imagefileslist:
            img = cv2.imread(imagefile, 1)
            cv2.putText(img, imagefile[-22:-7], (10,440), font, 0.5,(255,255,255),2,cv2.LINE_AA)
            w.write(img)
            currentprogress = int(currentframe * 100 / totalframes)
            if  currentprogress > previousprogress:
                sys.stdout.write("        Adding frames to video...  " + str(currentprogress) + "%    \r")
                sys.stdout.flush()
                previousprogress = currentprogress
            currentframe += 1
        print("\n    Done.")
        
    except KeyboardInterrupt:
        print("KeyboardInterrupt. Deleting unfinished video file.")
        os.remove(videofile)
        sys.exit(0)           


def removeImages(path):
    print("Removing all images from path... " + path)
    itemlist = os.listdir(path)
    for item in itemlist:
        if item.endswith(".jpg"):
            os.remove(os.path.join(path, item))


def getFolderNamesList():
    print("Getting folders list...")
    return [ name for name in os.listdir(IMAGESPATH) if os.path.isdir(os.path.join(IMAGESPATH, name)) ]


def filterAndSort(foldernameslist):
    """Selects folders with name matching YYYYMMDD format and older than today. Sorts in increasing order."""
    print("Selecting and sorting folders...")    
    currenttime = time.time()
    currentday = datetime.datetime.fromtimestamp(currenttime).strftime('%Y%m%d')
    regex = re.compile(r'([0-9]){8}')
    filteredsortedlist = list(filter(regex.match, foldernameslist))
    filteredsortedlist.sort()
    currentdayindex = filteredsortedlist.index(currentday)
    filteredsortedlist = filteredsortedlist[0 : currentdayindex]
    return filteredsortedlist


def isProcessedFolder(foldername):
    """Checks if a video already exists on the folder."""
    return os.path.isfile(IMAGESPATH + "/" + foldername + "/" + foldername + ".mkv")


def main():  
    print("Searching for videos pending to be processed...")  
    folders = filterAndSort(getFolderNamesList())  
    for folder in folders:
        if not isProcessedFolder(folder):
            createVideo(IMAGESPATH + "/" + folder + "/")
            removeImages(IMAGESPATH + "/" + folder + "/")
    

if __name__ == '__main__':
    main()
