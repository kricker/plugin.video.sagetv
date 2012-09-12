import urllib,urllib2,re
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

# SageTV URL based on user settings
strUrl = 'http://' + __settings__.getSetting("sage_user") + ':' + __settings__.getSetting("sage_pass") + '@' + __settings__.getSetting("sage_ip") + ':' + __settings__.getSetting("sage_port")
iconImage = xbmc.translatePath(os.path.join(__cwd__,'resources','media','icon.png'))
DEFAULT_CHARSET = 'utf-8'

# 500-THUMBNAIL 501/502/505/506/507/508-LIST 503-MINFO2 504-MINFO 515-MINFO3
confluence_views = [500,501,502,503,504,508]

def TOPLEVELCATEGORIES():
 
	addTopLevelDir('1. Watch Recordings', strUrl + '/sagex/api?command=EvaluateExpression&1=GroupByMethod(GetMediaFiles("T"),"GetMediaTitle")&size=500&encoder=json',1,iconImage,'Browse previously recorded and currently recording shows')
	addTopLevelDir('2. View Upcoming Recordings', strUrl + '/sagex/api?command=GetScheduledRecordings&encoder=json',2,iconImage,'View and manage your upcoming recording schedule')
	addTopLevelDir('3. Browse Channel Listings', strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByBoolMethod(GetAllChannels(), "IsChannelViewable", true)&size=1000&encoder=json',3,iconImage,'Browse channels and manage recordings')
	addTopLevelDir('4. Search for Recordings', strUrl + '/',4,iconImage,'Search for Recordings')
	addTopLevelDir('5. Search for Airings', strUrl + '/',5,iconImage,'Search for Upcoming Airings')

	xbmc.executebuiltin("Container.SetViewMode(515)")
	
def VIEWLISTOFRECORDEDSHOWS(url,name):
	#Get the list of Recorded shows
	addDir('[All Shows]',strUrl + '/sagex/api?command=GetMediaFiles&1="T"&size=500&encoder=json',11,iconImage,'')
	titleObjects = executeSagexAPIJSONCall(url, "Result")
	titles = titleObjects.keys()
	for title in titles:
		mfsForTitle = titleObjects.get(title)
		for mf in mfsForTitle:
			airing = mf.get("Airing")
			show = airing.get("Show")
			strTitle = airing.get("AiringTitle")
			strMediaFileId = str(mf.get("MediaFileID"))
			strExternalId = str(show.get("ShowExternalID"))
			#strTitle = strTitle.replace('&amp;','&')
			#strTitle = strTitle.replace('&quot;','"')
			#strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
			break
		urlToShowEpisodes = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByMethod(GetMediaFiles("T"),"GetMediaTitle","' + urllib2.quote(strTitle.encode("utf8")) + '",true)&size=500&encoder=json'
		#urlToShowEpisodes = strUrl + '/sage/Search?searchType=TVFiles&SearchString=' + urllib2.quote(strTitle.encode("utf8")) + '&DVD=on&sort2=airdate_asc&partials=both&TimeRange=0&pagelen=100&sort1=title_asc&filename=&Video=on&search_fields=title&xml=yes'
		print "ADDING strTitle=" + strTitle + "; urlToShowEpisodes=" + urlToShowEpisodes
		imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileId
		#print "ADDING imageUrl=" + imageUrl
		addDir(strTitle, urlToShowEpisodes,11,imageUrl,strExternalId)

def VIEWLISTOFEPISODESFORSHOW(url,name):
	mfs = executeSagexAPIJSONCall(url, "Result")
	print "# of EPISODES for " + name + "=" + str(len(mfs))
	if(mfs == None or len(mfs) == 0):
		print "NO EPISODES FOUND FOR SHOW=" + name
		xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
		return

	for mf in mfs:
		airing = mf.get("Airing")
		show = airing.get("Show")
		strMediaFileID = str(mf.get("MediaFileID"))
		strTitle = airing.get("AiringTitle")
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
		strDisplayText = strEpisode
		if(strEpisode == ""):
			strDisplayText = strDescription
		# else if there is an episode use that
		if(name == "[All Shows]"):
			strDisplayText = strTitle + ' - ' + strDisplayText

		strFilepath = mf.get("SegmentFiles")[0]
		
		imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
		print "strOriginalAirdate=" + strOriginalAirdate + ";strAiringdate" + strAiringdate
		addMediafileLink(strDisplayText,strFilepath.replace(sage_rec, sage_unc),strDescription,imageUrl,strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID,seasonNum,episodeNum,studio,isFavorite)

	xbmc.executebuiltin("Container.SetViewMode(503)")

def VIEWUPCOMINGRECORDINGS(url,name):
	#req = urllib.urlopen(url)
	airings = executeSagexAPIJSONCall(url, "Result")
	for airing in airings:
		show = airing.get("Show")
		strTitle = airing.get("AiringTitle")
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
		if(strEpisode == "" and strDescription == ""):
			strDisplayText = strTitle
		elif(strEpisode == ""):
			strDisplayText = strTitle + ' - ' + strDescription
		# else if there is an episode use that
		else:
			strDisplayText = strTitle + ' - ' + strEpisode
		strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
		addAiringLink(strDisplayText,'',strDescription,iconImage,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite)

	xbmc.executebuiltin("Container.SetViewMode(503)")

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

	xbmc.executebuiltin("Container.SetViewMode(515)")

def VIEWAIRINGSONCHANNEL(url,name):
	airings = executeSagexAPIJSONCall(url, "Result")
	for airing in airings:
		show = airing.get("Show")
		strTitle = airing.get("AiringTitle")
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
		if(strEpisode == "" and strDescription == ""):
			strDisplayText = strTitle
		elif(strEpisode == ""):
			strDisplayText = strTitle + ' - ' + strDescription
		# else if there is an episode use that
		else:
			strDisplayText = strTitle + ' - ' + strEpisode
		strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
		addAiringLink(strDisplayText,'',strDescription,iconImage,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite)

	xbmc.executebuiltin("Container.SetViewMode(503)")

def SEARCHFORRECORDINGS(url,name):
	titleToSearchFor = common.getUserInput("Search","")
	url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByMethod(GetMediaFiles("T"), "GetMediaTitle", "' + urllib2.quote(titleToSearchFor.encode("utf8")) + '", true)&encoder=json'
	mfs = executeSagexAPIJSONCall(url, "Result")
	print "# of EPISODES for " + titleToSearchFor + "=" + str(len(mfs))
	if(mfs == None or len(mfs) == 0):
		print "NO EPISODES FOUND FOR SHOW=" + name
		xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
		return

	for mf in mfs:
		airing = mf.get("Airing")
		show = airing.get("Show")
		strMediaFileID = str(mf.get("MediaFileID"))
		strTitle = airing.get("AiringTitle")
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
		strDisplayText = strTitle + ' - ' + strEpisode
		if(strEpisode == ""):
			strDisplayText = strTitle + ' - ' + strDescription

		strFilepath = mf.get("SegmentFiles")[0]
		
		imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
		addMediafileLink(strDisplayText,strFilepath.replace(sage_rec, sage_unc),strDescription,imageUrl,strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID,seasonNum,episodeNum,studio,isFavorite)

	xbmc.executebuiltin("Container.SetViewMode(503)")

def SEARCHFORAIRINGS(url,name):
	titleToSearchFor = common.getUserInput("Search","")
	now = time.time()
	startRange = str(long(now * 1000))
	#url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchByTitle("%s","T"),"GetAiringStartTime","%s",java_lang_Long_MAX_VALUE,true)&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), startRange)
	url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchByTitle("%s","T"),"GetAiringStartTime",java_lang_Long_parseLong("%d"),java_lang_Long_MAX_VALUE,true)&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), int(time.time()) * 1000)
	airings = executeSagexAPIJSONCall(url, "Result")
	for airing in airings:
		show = airing.get("Show")
		strTitle = airing.get("AiringTitle")
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
		if(strEpisode == "" and strDescription == ""):
			strDisplayText = strTitle
		elif(strEpisode == ""):
			strDisplayText = strTitle + ' - ' + strDescription
		# else if there is an episode use that
		else:
			strDisplayText = strTitle + ' - ' + strEpisode
		strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
		addAiringLink(strDisplayText,'',strDescription,iconImage,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite)

	xbmc.executebuiltin("Container.SetViewMode(503)")

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

def addDir(name,url,mode,iconimage,showexternalid):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name)
	strSeriesDescription = ""
	strSeriesDescription = getShowSeriesDescription(showexternalid)

	liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": strSeriesDescription } )
	liz.setIconImage(iconimage)
	liz.setThumbnailImage(iconimage)
	#liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	#liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
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