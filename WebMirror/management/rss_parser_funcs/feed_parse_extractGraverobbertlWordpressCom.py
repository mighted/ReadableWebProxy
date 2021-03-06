def extractGraverobbertlWordpressCom(item):
	'''
	Parser for 'graverobbertl.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('mge',       'Magical★Explorer',                                                                                                                                                                'translated'),
		('spt',       'The strongest dull prince secret battle for the throne.～I don’t care about the throne but since I don’t want to die, I think I will make my little brother the emperor～',       'translated'),
		('dah',       'Magical Devices Craftsman Dahlia Won’t Hang Her Head Down Anymore',                                                                                                               'translated'),
		('MM',        'I Told You I\'m Not 〇〇!! ~When I Helped Out the Most Beautiful Girl in My Class, My Identity Got Found Out~',                                                                   'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False