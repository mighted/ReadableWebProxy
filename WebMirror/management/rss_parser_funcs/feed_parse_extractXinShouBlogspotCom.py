def extractXinShouBlogspotCom(item):
	'''
	Parser for 'xin-shou.blogspot.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('A Match Made in Heaven',       'A Match Made in Heaven',                      'translated'),
		('The Rebirth of Han Yuxi',      'The Rebirth of Han Yuxi',                     'translated'),
		('Black Belly Wife',             'Black Belly Wife',                            'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False