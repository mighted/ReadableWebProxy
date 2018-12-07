

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()

import WebMirror.rules
import common.LogBase as LogBase

import datetime
import traceback
import sys

import common.util.urlFuncs as url_util
import urllib.parse
import WebRequest
import bs4

import WebMirror.rules
import WebMirror.SpecialCase
import WebMirror.processor.ProcessorBase

from activePlugins import PREPROCESSORS
from activePlugins import PLUGINS
from activePlugins import FILTERS

from common.Exceptions import DownloadException
import statsd
import settings
import time

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


class ItemFetcher(LogBase.LoggerMixin):


	loggerPath = "Main.SiteArchiver"



	# Fetch items up to 1,000,000 (1 million) links away from the root source
	# This (functionally) equates to no limit.
	# The db defaults to  (e.g. max signed integer value) anyways
	FETCH_DISTANCE = 1000 * 1000

	def sync_wg_proxy(self):
		if getattr(self, '__wg', None) is None:
			self.__wg = WebRequest.WebGetRobust()
		return self.__wg

	def __init__(self, rules, target_url, db_sess, start_url, job, cookie_lock=None, wg_proxy=None, response_queue=None):
		# print("Fetcher init()")
		super().__init__()

		self.response_queue = response_queue
		self.job            = job
		self.db_sess        = db_sess


		if wg_proxy:
			self.wg_proxy = wg_proxy
		else:
			self.wg_proxy = self.sync_wg_proxy

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


		self.filter_modules = []
		for item in FILTERS:
			self.filter_modules.append(item)


		self.preprocessor_modules = []
		for item in PREPROCESSORS:
			self.preprocessor_modules.append(item)

		baseRules = [ruleset for ruleset in rules if ruleset['netlocs'] is None].pop(0)

		rules = [ruleset for ruleset in rules if ruleset['netlocs'] != None]
		rules.sort(key=lambda x:x['netlocs'])

		self.ruleset = rules

		self.relinkable = set()
		for item in self.ruleset:
			if item['fileDomains']:
				self.relinkable.update(item['fileDomains'])
			if item['netlocs']:
				self.relinkable.update(item['netlocs'])

		netloc = urllib.parse.urlsplit(target_url).netloc

		self.rules = None
		for ruleset in self.ruleset:
			if netloc in ruleset['netlocs']:
				# self.log.info("Found specific ruleset for netloc: %s -> %s", netloc, ruleset['netlocs'])
				self.rules = ruleset

		if not self.rules:
			self.log.warn("Using base ruleset for URL: '%s'!", target_url)
			self.rules = baseRules


		assert self.rules

		self.target_url = target_url
		self.start_url = start_url


		self.mon_con = statsd.StatsClient(
				host = settings.GRAPHITE_DB_IP,
				port = 8125,
				prefix = 'ReadableWebProxy.Processing',
				)

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



	def plugin_dispatch(self, plugin, url, content, fName, mimeType, no_ret=False):
		self.log.info("Dispatching file '%s' with mime-type '%s' to plugin: '%s'", fName, mimeType, plugin)
		assert isinstance(content, (str, bytes)) , "Content must be a string/bytes. It's currently type: '%s'" % type(content)


		params = {
									'pageUrl'         : url,
									'pgContent'       : content,
									'mimeType'        : mimeType,
									'db_sess'         : self.db_sess,
									'baseUrls'        : self.start_url,
									'loggerPath'      : self.loggerPath,
									'badwords'        : self.rules['badwords'],
									'decompose'       : self.rules['decompose'],
									'decomposeBefore' : self.rules['decomposeBefore'],
									'fileDomains'     : self.rules['fileDomains'],
									'allImages'       : self.rules['allImages'],
									'decompose_svg'   : self.rules['decompose_svg'],
									'ignoreBadLinks'  : self.rules['IGNORE_MALFORMED_URLS'],
									'stripTitle'      : self.rules['stripTitle'],
									'relinkable'      : self.relinkable,
									'destyle'         : self.rules['destyle'],
									'preserveAttrs'   : self.rules['preserveAttrs'],
									'type'            : self.rules['type'],
									'message_q'       : self.response_queue,
									'job'             : self.job,
									'wg_proxy'        : self.wg_proxy,
		}

		ret = plugin.process(params)

		if no_ret:
			return

		assert ret != None, "Return from %s was None!" % plugin
		assert "mimeType" in ret or "file" in ret, "Neither mimetype or file in ret for url '%s', plugin '%s'" % (url, plugin)

		return ret


	def cr_fetch(self, itemUrl):
		wg = self.wg_proxy()
		self.log.info("Synchronous rendered chromium fetch!")
		content = None
		with wg.chromiumContext(itemUrl) as cr:
			try:
				content = cr.blocking_navigate_and_get_source(itemUrl)
				if content:
					if content['binary'] is False:
						# If the content isn't binary, retreive the rendered version.
						content = cr.get_rendered_page_source()
					else:
						self.log.error("Binary content!")

			except Exception:
				pass

			if not content:
				for x in range(99):
					try:
						content = cr.get_rendered_page_source()
					except Exception as e:
						self.log.error("Failure extracting source (%s)! Retrying %s..." % (e, x))
						if x > 3:
							raise


			if itemUrl.endswith("/feed/"):
				mType = "application/rss+xml"
			else:
				mType = 'text/html'

			raw_url = cr.get_current_url()
			fileN = urllib.parse.unquote(urllib.parse.urlparse(raw_url)[2].split("/")[-1])
			fileN = bs4.UnicodeDammit(fileN).unicode_markup

			title, cur_url = cr.get_page_url_title()

		if "debug" in sys.argv:
			self.log.info("Title: %s", title)
			self.log.info("Mime: %s", mType)
			self.log.info("Fname: %s", fileN)
			self.log.info("Content: ")
			self.log.info("%s", content)

		return content, fileN, mType

	def getItem(self, itemUrl):

		spc = WebMirror.rules.load_special_case_sites()
		casehandler = WebMirror.SpecialCase.getSpecialCaseHandler(specialcase=spc, joburl=itemUrl)

		if casehandler == ["chrome_render_fetch"]:
			self.log.info("Synchronous rendered chromium fetch!")
			content, fileN, mType = self.cr_fetch(itemUrl)
			return content, fileN, mType
		else:
			return self.__plain_local_fetch(itemUrl)

	def __plain_local_fetch(self, itemUrl):
		error = None
		try:
			itemUrl = itemUrl.strip()
			itemUrl = itemUrl.replace(" ", "%20")
			content, handle = self.wg_proxy().getpage(itemUrl, returnMultiple=True)
		except WebRequest.FetchFailureError:
			self.log.error("Failed to fetch page!")
			for line in traceback.format_exc().split("\n"):
				self.log.error(line)

			error = traceback.format_exc()
			content, handle = None, None
		except:
			print("Failure?")
			if self.rules['cloudflare']:
				if not self.wg_proxy().stepThroughCloudFlare(itemUrl, titleNotContains='Just a moment...'):
					raise ValueError("Could not step through cloudflare!")
				# Cloudflare cookie set, retrieve again
				content, handle = self.wg_proxy().getpage(itemUrl, returnMultiple=True)
			else:
				raise



		if not content or not handle:
			if error:
				raise DownloadException("Failed to retreive file from page '%s'!\n\nFetch traceback:\n%s\n\nEnd fetch traceback." % (itemUrl, error))
			raise DownloadException("Failed to retreive file from page '%s'!" % itemUrl)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		mType = handle.info()['Content-Type']

		# If there is an encoding in the content-type (or any other info), strip it out.
		# We don't care about the encoding, since WebRequest will already have handled that,
		# and returned a decoded unicode object.
		if mType and ";" in mType:
			mType = mType.split(";")[0].strip()

		# *sigh*. So minus.com is fucking up their http headers, and apparently urlencoding the
		# mime type, because apparently they're shit at things.
		# Anyways, fix that.
		if '%2F' in  mType:
			mType = mType.replace('%2F', '/')

		self.wg_proxy().cj.save()

		self.log.info("Retreived file of type '%s', name of '%s' with a size of %0.3f K", mType, fileN, len(content)/1000.0)
		return content, fileN, mType



	def dispatchContent(self, content, fName, mimeType):
		assert bool(content)


		assert mimeType, "Mimetype must not be none. URL: '%s'" % (self.target_url)

		# Do preprocessing:
		preprocess_counts = 0
		for filter_plg in self.preprocessor_modules:
			if filter_plg.wantsUrl(self.target_url):
				content = filter_plg.preprocess(self.target_url, mimeType, content, wg_proxy=self.wg_proxy)
				preprocess_counts += 1

		if preprocess_counts > 1:
			raise ValueError("Multiple preprocess executions for the same content (%s, %s, %s). Wat?" % (self.target_url, fName, mimeType))

		# Feed content through filters that want it (if any):
		for filter_plg in self.filter_modules:
			if (mimeType.lower() in filter_plg.wanted_mimetypes or filter_plg.mimetype_catchall) and \
					filter_plg.wantsUrl(self.target_url)       and \
					filter_plg.wantsFromContent(content):
				self.plugin_dispatch(filter_plg, self.target_url, content, fName, mimeType, no_ret=True)


		# Then actually process it.
		keys = list(self.plugin_modules.keys())
		keys.sort(reverse=True)

		for key in keys:
			for plugin in self.plugin_modules[key]:
				if mimeType.lower() in plugin.wanted_mimetypes and \
						plugin.wantsUrl(self.target_url)       and \
						plugin.wantsFromContent(content):
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
	def fetch(self, preretrieved):


		if not preretrieved:
			# self.target_url = url_util.urlClean(self.target_url)
			content, fName, mimeType = self.getItem(self.target_url)
		else:
			content, fName, mimeType = preretrieved

		if content and not mimeType:
			mimeType = 'application/octet-stream'

		started_at = time.time()
		try:
			ret = self.dispatchContent(content, fName, mimeType)
		except Exception:
			self.log.error("Failure processing content from url '%s', mimetype '%s', filename: '%s'" % (self.target_url, mimeType, fName))
			raise

		fetchtime = (time.time() - started_at) * 1000

		cleaned_mime = mimeType
		for replace in ['/', '\\', ':', '.']:
			cleaned_mime = cleaned_mime.replace(replace, "-")

		self.mon_con.timing("{}".format(cleaned_mime), fetchtime)

		return ret
