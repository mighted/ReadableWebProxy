def extractSunflowerpenguinWordpressCom(item):
	'''
	Parser for 'sunflowerpenguin.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('heroine yuri flags',       'When I Reincarnated as the Villainess, I Raised Yuri Flags with the Heroine!?',                      'translated'),
		('black lotus heroine',      'The Female Lead is a Black Lotus',                      'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False