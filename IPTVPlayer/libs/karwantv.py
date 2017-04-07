﻿# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getMPDLinksWithMeta
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import random
import string
try:    import json
except Exception: import simplejson as json
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
    
###################################################

class KarwanTvApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL         = 'http://karwan.tv/'
        self.DEFAULT_ICON_URL = self.getFullUrl('images/KARWAN_TV_LOGO/www.karwan.tv.png')
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('karwantv.cookie')
        
        self.http_params = {}
        self.http_params.update({'header':self.HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
    
    def getList(self, cItem):
        printDBG("KarwanTvApi.getChannelsList")
        channelsTab = []
        
        try:
            initList = cItem.get('init_list', True)
            if initList:
                for item in [{'title':'TV', 'priv_cat':'tv'}, {'url':self.getFullUrl('radio.html'), 'title':'Radio', 'priv_cat':'radio'}]:
                    params = dict(cItem)
                    params.update(item)
                    params['init_list'] = False
                    channelsTab.append(params)
            else:
                category = cItem.get('priv_cat', '')
                
                sts, data = self.cm.getPage(cItem['url'])
                if not sts: return []
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="bt-inner">', '</div>')
                for item in data:
                    icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0] )
                    url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                    title = self.cleanHtmlStr( item )                
                    params = {'name':'karwan.tv', 'title':title, 'url':url, 'icon':icon}
                    if category == 'radio': params['type'] = 'audio'
                    else: params['type'] = 'video'
                    channelsTab.append(params)
        except Exception:
            printExc()
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("KarwanTvApi.getVideoLink")
        urlsTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlsTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data,'<div class="art-article">', '<tbody>', False)[1]
        url  = self.getFullUrl(self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', ignoreCase=True)[0])
        if not self.cm.isValidUrl(url): return urlsTab
        
        sts, data = self.cm.getPage(url)
        if not sts: return urlsTab
        
        hlsUrl  = self.cm.ph.getSearchGroups(data, '''['"]?hls['"]?\s*:\s*['"]([^"^']+?)['"]''')[0]
        dashUrl = self.cm.ph.getSearchGroups(data, '''['"]?dash['"]?\s*:\s*['"]([^"^']+?)['"]''')[0]
        
        urlsTab.extend( getDirectM3U8Playlist(hlsUrl, checkContent=True) )
        if 0 == len(urlsTab): urlsTab.extend( getMPDLinksWithMeta(dashUrl, checkExt=True) )
        
        return urlsTab