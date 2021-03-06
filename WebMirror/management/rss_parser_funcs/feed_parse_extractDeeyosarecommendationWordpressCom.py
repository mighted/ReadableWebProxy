def extractDeeyosarecommendationWordpressCom(item):
	'''
	Parser for 'deeyosarecommendation.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('demonssweetheart',          'demon\'s sweetheart',                      'translated'),
		('demon\'s sweetheart',       'demon\'s sweetheart',                      'translated'),
		('fylmt',                              'fortunately, you like me too',                      'translated'),
		('fortunately, you like me too',       'fortunately, you like me too',                      'translated'),
		('bnddsb',       'brother next door, don\'t sleep on my bed',                      'translated'),
		('brother next door, don\'t sleep on my bed',       'brother next door, don\'t sleep on my bed',                      'translated'),
		('sdwz',       'splendid dream of wanzhou',                      'translated'),
		('splendid dream of wanzhou',       'splendid dream of wanzhou',                      'translated'),
		('wife became a minor before divorce',       'wife became a minor before divorce',                      'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False