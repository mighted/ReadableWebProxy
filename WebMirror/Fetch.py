

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()

import WebMirror.rules
import WebMirror.LogBase as LogBase

import datetime


import WebMirror.processor.HtmlProcessor
import WebMirror.processor.GDriveDirProcessor
import WebMirror.processor.GDocProcessor
import WebMirror.processor.MarkdownProcessor
import WebMirror.processor.BinaryProcessor

import WebMirror.util.urlFuncs as url_util
import urllib.parse
import traceback
import WebMirror.util.webFunctions as webFunctions
import bs4

import WebMirror.processor.ProcessorBase



########################################################################################################################
#
#	##     ##    ###    #### ##    ##     ######  ##          ###     ######   ######
#	###   ###   ## ##    ##  ###   ##    ##    ## ##         ## ##   ##    ## ##    ##
#	#### ####  ##   ##   ##  ####  ##    ##       ##        ##   ##  ##       ##
#	## ### ## ##     ##  ##  ## ## ##    ##       ##       ##     ##  ######   ######
#	##     ## #########  ##  ##  ####    ##       ##       #########       ##       ##
#	##     ## ##     ##  ##  ##   ###    ##    ## ##       ##     ## ##    ## ##    ##
#	##     ## ##     ## #### ##    ##     ######  ######## ##     ##  ######   ######
#
########################################################################################################################


PLUGINS = [
	WebMirror.processor.HtmlProcessor.HtmlPageProcessor,
	WebMirror.processor.GDriveDirProcessor.GDriveDirProcessor,
	WebMirror.processor.GDocProcessor.GdocPageProcessor,
	WebMirror.processor.MarkdownProcessor.MarkdownProcessor,
	WebMirror.processor.BinaryProcessor.BinaryResourceProcessor,
]

class ItemFetcher(LogBase.LoggerMixin):


	loggerPath = "Main.SiteArchiver"



	# Fetch items up to 1,000,000 (1 million) links away from the root source
	# This (functionally) equates to no limit.
	# The db defaults to  (e.g. max signed integer value) anyways
	FETCH_DISTANCE = 1000 * 1000

	def __init__(self, rules, target_url, start_url, cookie_lock, wg_handle=None):
		# print("Fetcher init()")
		super().__init__()

		if wg_handle:
			self.wg = wg_handle
		else:
			self.wg = webFunctions.WebGetRobust(cookie_lock=cookie_lock)

		# Validate the plugins implement the proper interface
		for item in PLUGINS:
			assert issubclass(item, WebMirror.processor.ProcessorBase.PageProcessor), "Item '%s' does not inherit from '%s'" % (item, WebMirror.processor.ProcessorBase.PageProcessor)


		self.plugin_modules = {}
		for item in PLUGINS:
			key = item.want_priority
			if key in self.plugin_modules:
				self.plugin_modules[key].append(item)
			else:
				self.plugin_modules[key] = [item]

		baseRules = [ruleset for ruleset in rules if ruleset['netlocs'] == None].pop(0)

		rules = [ruleset for ruleset in rules if ruleset['netlocs'] != None]
		rules.sort(key=lambda x:x['netlocs'])

		self.ruleset = rules

		self.relinkable = set()
		for item in self.ruleset:
			[self.relinkable.add(url) for url in item['fileDomains']]         #pylint: disable=W0106
			[self.relinkable.add(url) for url in item['netlocs']]             #pylint: disable=W0106


		netloc = urllib.parse.urlsplit(target_url).netloc

		self.rules = None
		for ruleset in self.ruleset:
			if netloc in ruleset['netlocs']:
				# self.log.info("Found specific ruleset!")
				self.rules = ruleset

		if not self.rules:
			self.log.warn("Using base ruleset!")
			self.rules = baseRules


		assert self.rules

		self.target_url = target_url
		self.start_url = start_url

	########################################################################################################################



	########################################################################################################################
	#
	#	########  ####  ######  ########     ###    ########  ######  ##     ##      ##     ## ######## ######## ##     ##  #######  ########   ######
	#	##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ##      ###   ### ##          ##    ##     ## ##     ## ##     ## ##    ##
	#	##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ##      #### #### ##          ##    ##     ## ##     ## ##     ## ##
	#	##     ##  ##   ######  ########  ##     ##    ##    ##       #########      ## ### ## ######      ##    ######### ##     ## ##     ##  ######
	#	##     ##  ##        ## ##        #########    ##    ##       ##     ##      ##     ## ##          ##    ##     ## ##     ## ##     ##       ##
	#	##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ##      ##     ## ##          ##    ##     ## ##     ## ##     ## ##    ##
	#	########  ####  ######  ##        ##     ##    ##     ######  ##     ##      ##     ## ########    ##    ##     ##  #######  ########   ######
	#
	########################################################################################################################



	def getEmptyRet(self):
		return {
			'plainLinks' : [],
			'rsrcLinks'  : [],

			'title'      : "Error: Unknown dispatch type",
			'contents'   : "Error. Could not dispatch properly",
			'mimeType'   : "text/html",
			}



	def plugin_dispatch(self, plugin, url, content, fName, mimeType):
		self.log.info("Dispatching file '%s' with mime-type '%s'", fName, mimeType)



		params = {
									'pageUrl'         : url,
									'pgContent'       : content,
									'mimeType'        : mimeType,
									'baseUrls'        : self.start_url,
									'loggerPath'      : self.loggerPath,
									'badwords'        : self.rules['badwords'],
									'decompose'       : self.rules['decompose'],
									'decomposeBefore' : self.rules['decomposeBefore'],
									'fileDomains'     : self.rules['fileDomains'],
									'allImages'       : self.rules['allImages'],
									'ignoreBadLinks'  : self.rules['IGNORE_MALFORMED_URLS'],
									'stripTitle'      : self.rules['stripTitle'],
									'relinkable'      : self.relinkable,
									'destyle'         : self.rules['destyle'],
									'preserveAttrs'   : self.rules['preserveAttrs'],
		}

		ret = plugin.process(params)

		assert "mimeType" in ret or "file" in ret, "Neither mimetype or file in ret for url '%s', plugin '%s'" % (url, plugin)

		return ret





	def getItem(self, itemUrl):

		try:
			content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
		except:
			if self.rules['cloudflare']:
				if not self.wg.stepThroughCloudFlare(itemUrl, titleNotContains='Just a moment...'):
					raise ValueError("Could not step through cloudflare!")
				# Cloudflare cookie set, retrieve again
				content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
			else:
				raise



		if not content or not handle:
			raise ValueError("Failed to retreive file from page '%s'!" % itemUrl)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		mType = handle.info()['Content-Type']

		# If there is an encoding in the content-type (or any other info), strip it out.
		# We don't care about the encoding, since WebFunctions will already have handled that,
		# and returned a decoded unicode object.
		if mType and ";" in mType:
			mType = mType.split(";")[0].strip()

		# *sigh*. So minus.com is fucking up their http headers, and apparently urlencoding the
		# mime type, because apparently they're shit at things.
		# Anyways, fix that.
		if '%2F' in  mType:
			mType = mType.replace('%2F', '/')

		self.log.info("Retreived file of type '%s', name of '%s' with a size of %0.3f K", mType, fileN, len(content)/1000.0)
		return content, fileN, mType



	def dispatchContent(self, content, fName, mimeType):

		keys = list(self.plugin_modules.keys())
		keys.sort(reverse=True)

		for key in keys:
			for plugin in self.plugin_modules[key]:
				if mimeType.lower() in plugin.wanted_mimetypes and plugin.wantsUrl(self.target_url):
					# print("plugin", plugin, "wants", self.target_url)
					ret = self.plugin_dispatch(plugin, self.target_url, content, fName, mimeType)
					if not "file" in ret:
						ret['rawcontent'] = content
					return ret

		self.log.error("Did not know how to dispatch request for url: '%s', mimetype: '%s'!", self.target_url, mimeType)
		return self.getEmptyRet()

	########################################################################################################################
	#
	#	########    ###     ######  ##    ##    ########  ####  ######  ########     ###    ########  ######  ##     ## ######## ########
	#	   ##      ## ##   ##    ## ##   ##     ##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ## ##       ##     ##
	#	   ##     ##   ##  ##       ##  ##      ##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ## ##       ##     ##
	#	   ##    ##     ##  ######  #####       ##     ##  ##   ######  ########  ##     ##    ##    ##       ######### ######   ########
	#	   ##    #########       ## ##  ##      ##     ##  ##        ## ##        #########    ##    ##       ##     ## ##       ##   ##
	#	   ##    ##     ## ##    ## ##   ##     ##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ## ##       ##    ##
	#	   ##    ##     ##  ######  ##    ##    ########  ####  ######  ##        ##     ##    ##     ######  ##     ## ######## ##     ##
	#
	########################################################################################################################

	# This is the main function that's called by the task management system.
	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def fetch(self):
		self.target_url = url_util.urlClean(self.target_url)


		content, fName, mimeType = self.getItem(self.target_url)

		return self.dispatchContent(content, fName, mimeType)


		# self.upsertResponseLinks(job, response)
