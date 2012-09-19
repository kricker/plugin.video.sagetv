import urllib,urllib2,re,string
import xbmc,xbmcplugin,xbmcgui,xbmcaddon,CommonFunctions
import os
import simplejson as json
import unicodedata
import time
from xml.dom.minidom import parse
from time import strftime
from datetime import date

common = CommonFunctions

__settings__ = xbmcaddon.Addon(id='plugin.video.SageTV')
__language__ = __settings__.getLocalizedString
__cwd__      = __settings__.getAddonInfo('path')

# SageTV recording Directories for path replacement
sage_rec = __settings__.getSetting("sage_rec")
sage_unc = __settings__.getSetting("sage_unc")
sage_rec2 = __settings__.getSetting("sage_rec2")
sage_unc2 = __settings__.getSetting("sage_unc2")
sage_rec3 = __settings__.getSetting("sage_rec3")
sage_unc3 = __settings__.getSetting("sage_unc3")
sage_rec4 = __settings__.getSetting("sage_rec4")
sage_unc4 = __settings__.getSetting("sage_unc4")
sage_rec5 = __settings__.getSetting("sage_rec5")
sage_unc5 = __settings__.getSetting("sage_unc5")

sagemappings = [ (sage_rec, sage_unc) ]

if ( sage_unc2 != '' and sage_unc2 != None ):
    sagemappings.append( (sage_rec2, sage_unc2) )
if ( sage_unc3 != '' and sage_unc3 != None ):
    sagemappings.append( (sage_rec3, sage_unc3) )
if ( sage_unc4 != '' and sage_unc4 != None ):
    sagemappings.append( (sage_rec4, sage_unc4) )
if ( sage_unc5 != '' and sage_unc5 != None ):
    sagemappings.append( (sage_rec5, sage_unc5) )

# SageTV URL based on user settings
strUrl = 'http://' + __settings__.getSetting("sage_user") + ':' + __settings__.getSetting("sage_pass") + '@' + __settings__.getSetting("sage_ip") + ':' + __settings__.getSetting("sage_port")
IMAGE_POSTER = xbmc.translatePath(os.path.join(__cwd__,'resources','media','poster.jpg'))
IMAGE_THUMB = xbmc.translatePath(os.path.join(__cwd__,'resources','media','thumb.jpg'))
DEFAULT_CHARSET = 'utf-8'
MIN_VERSION_SAGEX_REQUIRED = "7.1.9.10"

# 500-THUMBNAIL 501/502/505/506/507/508-LIST 503-MINFO2 504-MINFO 515-MINFO3
confluence_views = [500,501,502,503,504,508]


def TOPLEVELCATEGORIES():

    url = strUrl + '/sagex/api?command=GetInstalledPlugins&encoder=json'
    plugins = executeSagexAPIJSONCall(url, "Result")
    sagexVersion = ""
    for plugin in plugins:
        if(plugin.get("PluginIdentifier") == "sagex-api-services"):
            sagexVersion = plugin.get("PluginVersion")
 
    print "TOPLEVELCATEGORIES STARTED; sagex-api-services version=" + sagexVersion
    if(sagexVersion == ""):
        xbmcgui.Dialog().ok("Dependency Missing","This addon requires sagex-api-services version " + MIN_VERSION_SAGEX_REQUIRED, "You do not have the sagex-api plugin installed","Please install sagex-api-services to enable this plugin.")
        return        
    if(comparePluginVersions(sagexVersion, MIN_VERSION_SAGEX_REQUIRED) < 0):
        xbmcgui.Dialog().ok("Dependency Missing","This addon requires sagex-api-services version " + MIN_VERSION_SAGEX_REQUIRED, "You have version " + sagexVersion,"Please install/upgrade your sagex-api-services version to " + MIN_VERSION_SAGEX_REQUIRED)
        return
#        xbmc.executebuiltin("Notification('test','test2')")
    # 

    addTopLevelDir('1. Watch Recordings', strUrl + '/sagex/api?c=xbmc:GetTVMediaFilesGroupedByTitle&size=500&encoder=json',1,IMAGE_POSTER,'Browse previously recorded and currently recording shows')
    addTopLevelDir('2. View Upcoming Recordings', strUrl + '/sagex/api?command=GetScheduledRecordings&encoder=json',2,IMAGE_POSTER,'View and manage your upcoming recording schedule')
    addTopLevelDir('3. Browse Channel Listings', strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByBoolMethod(GetAllChannels(), "IsChannelViewable", true)&size=1000&encoder=json',3,IMAGE_POSTER,'Browse channels and manage recordings')
    addTopLevelDir('4. Search for Recordings', strUrl + '/',4,IMAGE_POSTER,'Search for Recordings')
    addTopLevelDir('5. Search for Airings', strUrl + '/',5,IMAGE_POSTER,'Search for Upcoming Airings')

    xbmc.executebuiltin("Container.SetViewMode(535)")
    
def VIEWLISTOFRECORDEDSHOWS(url,name):
    #Get the list of Recorded shows
    addDir('[All Shows]',strUrl + '/sagex/api?c=xbmc:GetMediaFilesForShowWithSubsetOfProperties&1=&size=500&encoder=json',11,IMAGE_POSTER,IMAGE_THUMB,'')
    titleObjects = executeSagexAPIJSONCall(url, "Result")
    titles = titleObjects.keys()
    for title in titles:
        mfsForTitle = titleObjects.get(title)
        for mfSubset in mfsForTitle:
            strTitle = mfSubset.get("ShowTitle")
            strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
            strMediaFileID = mfSubset.get("MediaFileID")
            strExternalID = mfSubset.get("ShowExternalID")
            break
        urlToShowEpisodes = strUrl + '/sagex/api?c=xbmc:GetMediaFilesForShowWithSubsetOfProperties&1=' + urllib2.quote(strTitle.encode("utf8")) + '&size=500&encoder=json'
        #urlToShowEpisodes = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByMethod(GetMediaFiles("T"),"GetMediaTitle","' + urllib2.quote(strTitle.encode("utf8")) + '",true)&size=500&encoder=json'
        #urlToShowEpisodes = strUrl + '/sage/Search?searchType=TVFiles&SearchString=' + urllib2.quote(strTitle.encode("utf8")) + '&DVD=on&sort2=airdate_asc&partials=both&TimeRange=0&pagelen=100&sort1=title_asc&filename=&Video=on&search_fields=title&xml=yes'
        print "ADDING strTitle=" + strTitle + "; urlToShowEpisodes=" + urlToShowEpisodes
        imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
        #print "ADDING imageUrl=" + imageUrl
        addDir(strTitle, urlToShowEpisodes,11,imageUrl,'',strExternalID)

def VIEWLISTOFEPISODESFORSHOW(url,name):
    mfs = executeSagexAPIJSONCall(url, "Result")
    print "# of EPISODES for " + name + "=" + str(len(mfs))
    if(mfs == None or len(mfs) == 0):
        print "NO EPISODES FOUND FOR SHOW=" + name
        xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
        return

    for mfSubset in mfs:
        strTitle = mfSubset.get("ShowTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strMediaFileID = mfSubset.get("MediaFileID")

        strEpisode = mfSubset.get("EpisodeTitle")
        strDescription = mfSubset.get("EpisodeDescription")
        strGenre = mfSubset.get("ShowGenre")
        strAiringID = mfSubset.get("AiringID")
        seasonNum = int(mfSubset.get("SeasonNumber"))
        episodeNum = int(mfSubset.get("EpisodeNumber"))
        studio = mfSubset.get("AiringChannelName")
        isFavorite = mfSubset.get("IsFavorite")
        
        startTime = float(mfSubset.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(mfSubset.get("OriginalAiringDate") > 0):
            startTime = float(mfSubset.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            strDisplayText = strEpisode
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strDescription
            if(name == "[All Shows]"):
                strDisplayText = strTitle + " - " + strDisplayText
        else:
            strDisplayText = strTitle

        strFilepath = mfSubset.get("SegmentFiles")[0]
        
        imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
        addMediafileLink(strDisplayText,filemap(strFilepath),strDescription,imageUrl,strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID,seasonNum,episodeNum,studio,isFavorite)

    xbmc.executebuiltin("Container.SetViewMode(504)")


# Map file recording path to the first matching UNC path
def filemap(filepath):
    for (rec, unc) in sagemappings:
        if ( filepath.find(rec) != -1 ):
            return filepath.replace(rec, unc)

    return filepath

def VIEWUPCOMINGRECORDINGS(url,name):
    #req = urllib.urlopen(url)
    airings = executeSagexAPIJSONCall(url, "Result")
    for airing in airings:
        show = airing.get("Show")
        strTitle = airing.get("AiringTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strEpisode = show.get("ShowEpisode")
        if(strEpisode == None):
            strEpisode = ""        
        strDescription = show.get("ShowDescription")
        if(strDescription == None):
            strDescription = ""        
        strGenre = show.get("ShowCategoriesString")
        strAiringID = str(airing.get("AiringID"))
        seasonNum = int(show.get("ShowSeasonNumber"))
        episodeNum = int(show.get("ShowEpisodeNumber"))
        studio = airing.get("AiringChannelName")
        isFavorite = airing.get("IsFavorite")
        
        startTime = float(airing.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(airing.get("OriginalAiringDate")):
            startTime = float(airing.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strTitle + ' - ' + strDescription
            else:
                strDisplayText = strTitle + ' - ' + strEpisode
        strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
        addAiringLink(strDisplayText,'',strDescription,IMAGE_THUMB,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite)

    xbmc.executebuiltin("Container.SetViewMode(504)")

def VIEWCHANNELLISTING(url,name):
    channels = executeSagexAPIJSONCall(url, "Result")
    for channel in channels:
        channelNumber = channel.get("ChannelNumber")
        channelName = channel.get("ChannelName")
        channelDescription = channel.get("ChannelDescription")
        channelNetwork = channel.get("ChannelNetwork")
        channelStationID = channel.get("StationID")
        now = time.time()
        startRange = str(long(now * 1000))
        rangeSizeDays = 7
        rangeSizeSeconds = rangeSizeDays * 24 * 60 * 60
        endRange = str(long((now + rangeSizeSeconds) * 1000))

        urlToAiringsOnChannel = strUrl + '/sagex/api?command=EvaluateExpression&1=GetAiringsOnChannelAtTime(GetChannelForStationID("' + str(channelStationID) + '"),"' + startRange + '","' + endRange + '",false)&encoder=json'
        logoUrl = strUrl + "/sagex/media/logo/" + str(channelStationID)
        strDisplayText = channelNumber + "-" + channelName
        addChannelDir(strDisplayText, urlToAiringsOnChannel,31,logoUrl,channelDescription)

    xbmc.executebuiltin("Container.SetViewMode(535)")

def VIEWAIRINGSONCHANNEL(url,name):
    airings = executeSagexAPIJSONCall(url, "Result")
    for airing in airings:
        show = airing.get("Show")
        strTitle = airing.get("AiringTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strEpisode = show.get("ShowEpisode")
        if(strEpisode == None):
            strEpisode = ""        
        strDescription = show.get("ShowDescription")
        if(strDescription == None):
            strDescription = ""        
        strGenre = show.get("ShowCategoriesString")
        strAiringID = str(airing.get("AiringID"))
        seasonNum = int(show.get("ShowSeasonNumber"))
        episodeNum = int(show.get("ShowEpisodeNumber"))
        studio = airing.get("AiringChannelName")        
        isFavorite = airing.get("IsFavorite")
        
        startTime = float(airing.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(airing.get("OriginalAiringDate")):
            startTime = float(airing.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strTitle + ' - ' + strDescription
            else:
                strDisplayText = strTitle + ' - ' + strEpisode
        strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
        addAiringLink(strDisplayText,'',strDescription,IMAGE_THUMB,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite)

    xbmc.executebuiltin("Container.SetViewMode(504)")

def SEARCHFORRECORDINGS(url,name):
    titleToSearchFor = common.getUserInput("Search","")
    url = strUrl + '/sagex/api?c=xbmc:SearchForMediaFiles&1=%s&size=100&encoder=json' % urllib2.quote(titleToSearchFor.encode("utf8"))
    #url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByMethod(GetMediaFiles("T"), "GetMediaTitle", "' + urllib2.quote(titleToSearchFor.encode("utf8")) + '", true)&size=100&encoder=json'
    mfs = executeSagexAPIJSONCall(url, "Result")
    print "# of EPISODES for " + titleToSearchFor + "=" + str(len(mfs))
    if(mfs == None or len(mfs) == 0):
        print "NO EPISODES FOUND FOR SEARCH=" + titleToSearchFor
        xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
        return

    for mfSubset in mfs:
        strTitle = mfSubset.get("ShowTitle")
        print "showtitle=" + str(strTitle)
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strMediaFileID = mfSubset.get("MediaFileID")

        strEpisode = mfSubset.get("EpisodeTitle")
        strDescription = mfSubset.get("EpisodeDescription")
        strGenre = mfSubset.get("ShowGenre")
        strAiringID = mfSubset.get("AiringID")
        seasonNum = int(mfSubset.get("SeasonNumber"))
        episodeNum = int(mfSubset.get("EpisodeNumber"))
        studio = mfSubset.get("AiringChannelName")
        isFavorite = mfSubset.get("IsFavorite")
        
        startTime = float(mfSubset.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(mfSubset.get("OriginalAiringDate") > 0):
            startTime = float(mfSubset.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode != "" and strDescription != ""):
                strDisplayText = strTitle + ' - ' + strDescription
            elif(strEpisode != ""):
                strDisplayText = strTitle + ' - ' + strEpisode

        strFilepath = mfSubset.get("SegmentFiles")[0]
        
        imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
        addMediafileLink(strDisplayText,filemap(strFilepath),strDescription,imageUrl,strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID,seasonNum,episodeNum,studio,isFavorite)

    xbmc.executebuiltin("Container.SetViewMode(504)")

def SEARCHFORAIRINGS(url,name):
    titleToSearchFor = common.getUserInput("Search","")
    now = time.time()
    startRange = str(long(now * 1000))
    #url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchByTitle("%s","T"),"GetAiringStartTime","%s",java_lang_Long_MAX_VALUE,true)&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), startRange)
    #url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchByTitle("%s","T"),"GetAiringStartTime",java_lang_Long_parseLong("%d"),java_lang_Long_MAX_VALUE,true)&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), int(time.time()) * 1000)
    url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchSelectedFields("%s",false,true,true,true,false,false,false,false,false,false,"T"),"GetAiringStartTime",java_lang_Long_parseLong("%d"),java_lang_Long_MAX_VALUE,true)&size=100&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), int(time.time()) * 1000)
    airings = executeSagexAPIJSONCall(url, "Result")
    for airing in airings:
        show = airing.get("Show")
        strTitle = airing.get("AiringTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strEpisode = show.get("ShowEpisode")
        if(strEpisode == None):
            strEpisode = ""        
        strDescription = show.get("ShowDescription")
        if(strDescription == None):
            strDescription = ""        
        strGenre = show.get("ShowCategoriesString")
        strAiringID = str(airing.get("AiringID"))
        seasonNum = int(show.get("ShowSeasonNumber"))
        episodeNum = int(show.get("ShowEpisodeNumber"))
        studio = airing.get("AiringChannelName")        
        isFavorite = airing.get("IsFavorite")
        
        startTime = float(airing.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(airing.get("OriginalAiringDate")):
            startTime = float(airing.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strTitle + ' - ' + strDescription
            else:
                strDisplayText = strTitle + ' - ' + strEpisode
        strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
        addAiringLink(strDisplayText,'',strDescription,IMAGE_THUMB,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite)

    xbmc.executebuiltin("Container.SetViewMode(504)")

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def addMediafileLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,mediafileid,airingid,seasonnum,episodenum,studio,isfavorite):
        ok=True
        liz=xbmcgui.ListItem(name)
        scriptToRun = "special://home/addons/plugin.video.SageTV/contextmenuactions.py"
        actionDelete = "delete|" + strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + mediafileid
        actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=mediafile:' + mediafileid
        actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
        bisAiringRecording = isAiringRecording(airingid)

        if(bisAiringRecording):
          if(isfavorite):
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
          else:
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')')], True)
        else:
          if(isfavorite):
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
          liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')')], True)

        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum, "studio": studio } )
        liz.setIconImage(iconimage)
        liz.setThumbnailImage(iconimage)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok

def addAiringLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,airingid,seasonnum,episodenum,studio,isfavorite):
    ok=True
    liz=xbmcgui.ListItem(name)
    scriptToRun = "special://home/addons/plugin.video.SageTV/contextmenuactions.py"
    actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=airing:' + airingid
    actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
    actionRecord = "record|" + strUrl + '/sagex/api?command=Record&1=airing:' + airingid
    
    bisAiringScheduledToRecord = isAiringScheduledToRecord(airingid)
    
    if(bisAiringScheduledToRecord):
        if(isfavorite):
            liz.addContextMenuItems([('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
        else:
            liz.addContextMenuItems([('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')')], True)
    else:
        if(isfavorite):
            liz.addContextMenuItems([('Record', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRecord + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
        else:
            liz.addContextMenuItems([('Record', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRecord + ')')], True)

    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum, "studio": studio } )
    liz.setIconImage(iconimage)
    liz.setThumbnailImage(iconimage)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
    return ok

# Checks if an airing is currently recording
def isAiringScheduledToRecord(airingid):
    sageApiUrl = strUrl + '/sagex/api?command=EvaluateExpression&1=java_util_HashSet_contains(new_java_util_HashSet(java_util_Arrays_asList(GetScheduledRecordings())),GetAiringForID(' + airingid + '))&encoder=json'
    return executeSagexAPIJSONCall(sageApiUrl, "Result")
        
def isAiringRecording(airingid):
    sageApiUrl = strUrl + '/sagex/api?command=IsFileCurrentlyRecording&1=airing:' + airingid + '&encoder=json'
    return executeSagexAPIJSONCall(sageApiUrl, "Result")
        
# Checks if an airing has a favorite set up for it
def getShowSeriesDescription(showexternalid):
    sageApiUrl = strUrl + '/sagex/api?command=EvaluateExpression&1=GetSeriesDescription(GetShowSeriesInfo(GetShowForExternalID("' + showexternalid + '")))&encoder=json'
    return executeSagexAPIJSONCall(sageApiUrl, "Result")
        
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

def addTopLevelDir(name,url,mode,iconimage,dirdescription):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name)

    liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": dirdescription } )
    liz.setIconImage(iconimage)
    liz.setThumbnailImage(iconimage)
    #liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
    #liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

def addDir(name,url,mode,iconimage,thumbimage,showexternalid):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name)
    strSeriesDescription = ""
    strSeriesDescription = getShowSeriesDescription(showexternalid)

    liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": strSeriesDescription } )
    liz.setIconImage(iconimage)
    if(thumbimage != ""):
        liz.setThumbnailImage(thumbimage)
    else:
        liz.setThumbnailImage(iconimage)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

def addChannelDir(name,url,mode,iconimage,channeldescription):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name)

    liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": channeldescription } )
    liz.setIconImage(iconimage)
    liz.setThumbnailImage(iconimage)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok


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

def comparePluginVersions(s1, s2):

    # See if they are equal.
    if s1 == s2:
        return 0

    # Make sure they are the same length.
    str1 = normalizePluginString(s1, len(string.split(s2, '.')))
    str2 = normalizePluginString(s2, len(string.split(s1, '.')))

    # Split into parts separated by '.'
    p1 = string.split(str1, '.')
    p2 = string.split(str2, '.')

    for i in range(len(p1)):
        int1 = int(p1[i])
        int2 = int(p2[i])
        if int1 < int2:
            return -1
        elif int2 < int1:
            return 1

    return 0
        
def normalizePluginString(s, l):
    while len(string.split(s, '.')) < l:
        s += ".0"
    return s

params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
        print ""
        TOPLEVELCATEGORIES()
       
elif mode==1:
    print ""+url
    VIEWLISTOFRECORDEDSHOWS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
        
elif mode==11:
    print ""+url
    VIEWLISTOFEPISODESFORSHOW(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
        
elif mode==2:
    print ""+url
    VIEWUPCOMINGRECORDINGS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

elif mode==3:
    print ""+url
    VIEWCHANNELLISTING(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)

elif mode==31:
    print ""+url
    VIEWAIRINGSONCHANNEL(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

elif mode==4:
    print ""+url
    SEARCHFORRECORDINGS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

elif mode==5:
    print ""+url
    SEARCHFORAIRINGS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

xbmcplugin.setContent(int(sys.argv[1]),'episodes')
xbmcplugin.endOfDirectory(int(sys.argv[1]))
