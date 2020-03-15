def extractCyborgTlCom(item):
	'''
	Parser for 'cyborg-tl.com'
	'''
	
	
	badwords = [
			'Penjelajahan',
		]
	if any([bad in item['title'] for bad in badwords]):
		return None


	badwords = [
			'bleach: we do knot always love you',
			'kochugunshikan boukensha ni naru',
			'badword',
		]
	if any([bad in item['tags'] for bad in badwords]):
		return None




	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False