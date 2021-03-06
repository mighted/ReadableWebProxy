def extractRandomnoveltranslateWordpressCom(item):
	'''
	Parser for 'randomnoveltranslate.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('pen down a marriage',                       'pen down a marriage',                                      'translated'),
		('transmigrating into a cannon fodder',       'transmigrating into a cannon fodder',                      'translated'),
		('rebirth of a virtuous wife',                'rebirth of a virtuous wife',                               'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False