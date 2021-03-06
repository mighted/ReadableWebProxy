def extractLizonkanovelsWordpressCom(item):
	'''
	Parser for 'lizonkanovels.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('bestial blade by priest',                                     'bestial blade',                      'translated'),
		('creatures of habit by meat in the shell',                     'creatures of habit',                      'translated'),
		('seal cultivation for self-improvement by mo xiao xian',       'seal cultivation for self-improvement',                      'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False