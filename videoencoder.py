# This program encodes the videos again using a more efficient video codec (VP9) to save storage space.

import os, sys
import time, datetime
import re


VIDEOSPATH = os.getcwd() + "/hq"


def getFolderNamesList():
    print("Getting folders list...")
    return [ name for name in os.listdir(VIDEOSPATH) if os.path.isdir(os.path.join(VIDEOSPATH, name)) ]


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


def containsNewVideoFolder(foldername):
    """Checks if a new video already exists on the folder."""
    return os.path.isfile(VIDEOSPATH + "/" + foldername + ".mkv")


def containsOldVideoFolder(foldername):
    """Checks if an old video exists on the folder."""
    return os.path.isfile(VIDEOSPATH + "/" + foldername + "/" + foldername + ".mkv")


def createNewVideo(path):
    """Creates a new VP9 mkv video from the old mkv video."""
    yyyymmdd = path[-9:-1]
    print("Creating video for day " + yyyymmdd + ". [\033[92mPRESS Ctrl+C TO ABORT\033[0m].")
    command = "ffmpeg -loglevel panic -i " + path + yyyymmdd + ".mkv -c:v libvpx-vp9 -crf 30 -b:v 0 " \
              "-threads 4 -speed 0 " + VIDEOSPATH + "/" + yyyymmdd + ".mkv"
    print(command)
    returnValue = os.system(command)
    if returnValue != 0:
        print("ffmpeg didn't finish the encoding task completely. Deleting temp file and aborting.")
        os.remove(VIDEOSPATH + "/" + yyyymmdd + ".mkv")
        sys.exit(1)


def removeOldVideoAndFolder(path):
    print("Removing old video and folder.")
    yyyymmdd = path[-9:-1]
    os.remove(path + yyyymmdd + ".mkv")
    try:
        os.rmdir(path)
    except OSError as ex:
        if ex.errno == errno.ENOTEMPTY:
            print("  Error. The folder wasn't empty after removing the old video. Aborting.")
            sys.exit(1)


def main():  
    print("Searching for videos pending to be processed...")  
    folders = filterAndSort(getFolderNamesList())  
    for folder in folders:
        if containsOldVideoFolder(folder) and not containsNewVideoFolder(folder):
            createNewVideo(VIDEOSPATH + "/" + folder + "/")
            removeOldVideoAndFolder(VIDEOSPATH + "/" + folder + "/")
    print("All done.")

if __name__ == '__main__':
    main()
