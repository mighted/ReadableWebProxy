


import runStatus
runStatus.preloadDicts = False

import WebMirror.PreProcessors.PreProcessorBase
import urllib.parse
import bs4
import common.util.WebRequest



class JsRendererPreprocessor(WebMirror.PreProcessors.PreProcessorBase.ContentPreprocessor):

	loggerPath = "Main.Preprocessor.JsRenderer"

	def preprocessContent(self, url, mimetype, contentstr):
		soup = common.util.WebRequest.as_soup(contentstr)
		text = soup.get_text(strip=True)

		if len(text) < 100:
			self.log.info("Page has little or no body. Trying to refetch and render using chromium.")
			contentstr, dummy_fileN, dummy_mType = self.wg.chromiumGetRenderedItem(url)
		else:
			self.log.info("Page has body, no re-fetch & render needed.")

		return contentstr

	@staticmethod
	def wantsUrl(url):
		netloc = urllib.parse.urlsplit(url).netloc
		if netloc.lower().endswith("wixsite.com"):
			print("JsRendererPreprocessor wants URL: %s", url)
			return True
		if netloc.lower().endswith("catatopatch.com"):
			print("JsRendererPreprocessor wants URL: %s", url)
			return True

		return False
