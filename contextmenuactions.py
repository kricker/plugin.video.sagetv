import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon

#Get the passed in argument from the addContextMenuItems() call in default.py
args = sys.argv[1].split("|")
print "sys.argv[1]=" + sys.argv[1]
if(args[0]== "delete" or args[0]== "cancelrecording" or args[0]== "removefavorite"):
	sageApiUrl = args[1]
	urllib.urlopen(sageApiUrl)
	xbmc.executebuiltin("Container.Refresh")
else:
	print "INVALID ARG PASSED IN TO CONTEXTMENUACTIONS.PY (sys.argv[1]=" + sys.argv[1]

