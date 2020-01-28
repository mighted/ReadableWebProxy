def extractBloomingtranslationHomeBlog(item):
	'''
	Parser for 'bloomingtranslation.home.blog'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('mdd',       'Marriage of the Di Daughter',                            'translated'),
		('wmmm',      'Who Moved My Mountain!',                                 'translated'),
		('rpimrm',    'The Random Passerby I Married Is The Richest Man!',      'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False