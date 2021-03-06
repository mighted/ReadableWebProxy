def extractNyanovelsCom(item):
	'''
	Parser for 'nyanovels.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('Held in the Lonely Castle',                                       'Held in the Lonely Castle',                                                      'translated'),
		('why harem intrigue when you can just raise a dog instead?',       'why harem intrigue when you can just raise a dog instead?',                      'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False