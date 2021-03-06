def extractMerebear474765851WordpressCom(item):
	'''
	Parser for 'merebear474765851.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(str(item['tags']) + " " + item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None
	
	
	tagmap = [
		('Daomu Biji',                                              'Daomu Biji',                      'translated'),
		('daomu biji, grave robbers\' chronicles, lost tomb',       'Daomu Biji',                      'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False