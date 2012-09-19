import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
from time import sleep
import simplejson as json

DEFAULT_CHARSET = 'utf-8'

def executeSagexAPIJSONCall(url, resultToGet):
    print "*** sagex request URL:" + url
    try:
        input = urllib.urlopen(url)
    except IOError, i:
        print "ERROR in executeSagexAPIJSONCall: Unable to connect to SageTV server"
        return None
    fileData = input.read()
    resp = unicodeToStr(json.JSONDecoder().decode(fileData))

    objKeys = resp.keys()
    numKeys = len(objKeys)
    if(numKeys == 1):
        return resp.get(resultToGet)
    else:
        return None

def unicodeToStr(obj):
    t = obj
    if(t is unicode):
        return obj.encode(DEFAULT_CHARSET)
    elif(t is list):
        for i in range(0, len(obj)):
            obj[i] = unicodeToStr(obj[i])
        return obj
    elif(t is dict):
        for k in obj.keys():
            v = obj[k]
            del obj[k]
            obj[k.encode(DEFAULT_CHARSET)] = unicodeToStr(v)
        return obj
    else:
        return obj # leave numbers and booleans alone


        
#Get the passed in argument from the addContextMenuItems() call in default.py
args = sys.argv[1].split("|")
if(args[0] in ["delete","cancelrecording","removefavorite","record"]):
    sageApiUrl = args[1]
    urllib.urlopen(sageApiUrl)
    if(args[0] == "delete"):
        xbmc.executebuiltin("Notification('SageTV addon','Delete successful')")
    elif(args[0] == "record"):
        xbmc.executebuiltin("Notification('SageTV addon','Scheduled recording successful')")
    xbmc.executebuiltin("Container.Refresh")
elif(args[0] == "watchnow"):
    xbmc.executebuiltin("Notification('SageTV addon','Attemping to playback live TV')")
    strUrl = args[1]
    airingID = args[2]    
    sageApiUrl = strUrl + '/sagex/api?command=Record&1=airing:' + airingID
    isRecording = False
    minWait = 1
    maxWait = 8

    #Schedule the show to be recorded
    urllib.urlopen(sageApiUrl)

    #Wait until a mediafile is created (and if one isn't after a period of time, consider it a failure)
    sageApiUrl = strUrl + '/sagex/api?command=GetCurrentlyRecordingMediaFiles&1=&encoder=json'
    wait = minWait
    while not isRecording and wait <= maxWait:
        print "Checking if recording has started for airingid=" + airingID
        sleep(wait)
        wait *= 2
        mfs = executeSagexAPIJSONCall(sageApiUrl, "Result")
        for mf in mfs:
            airing = mf.get("Airing")
            recordingAiringID = str(airing.get("AiringID"))
            print "recordingAiringID=" + recordingAiringID
            if (recordingAiringID == airingID):
                isRecording = True
                print "Recording for airingid=%s has started" % airingID
                break

    #If a mediafile is found, play it
    if isRecording:
        sageApiUrl = strUrl + '/sagex/api?command=GetMediaFileForAiring&1=airing:%s&encoder=json' % airingID
        mf = executeSagexAPIJSONCall(sageApiUrl, "MediaFile")
        mediaFileID = str(mf.get("MediaFileID"))
        currentSize = 0
        tries = 0
        maxTries = 10
        sageApiUrl = strUrl + '/sagex/api?command=GetSize&1=mediafile:%s&encoder=json' % mediaFileID
        while(currentSize == 0 and tries <= maxTries):
            currentSize = executeSagexAPIJSONCall(sageApiUrl, "Result")
            print "Current playback size=" + str(currentSize)
            if(currentSize > 0):
                break
            sleep(1)
            tries = tries+1
        strFilepath = mf.get("SegmentFiles")[0]
        print "Attempting to playback mediafileid=%s at filepath=%s" % (mediaFileID, strFilepath)
        xbmc.executebuiltin("PlayMedia('%s')" % strFilepath)
    else:
        xbmc.executebuiltin("Notification('SageTV addon','Unable to playback live TV')")
        print "NOTHING IS RECORDING"
        #return None
else:
	print "INVALID ARG PASSED IN TO CONTEXTMENUACTIONS.PY (sys.argv[1]=" + sys.argv[1]


