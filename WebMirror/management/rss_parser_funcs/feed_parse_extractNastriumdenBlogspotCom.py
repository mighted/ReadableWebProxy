def extractNastriumdenBlogspotCom(item):
	'''
	Parser for 'nastriumden.blogspot.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('The Jade Emperor Heaven Imperial Court Kindergarten',       'The Jade Emperor Heaven Imperial Court Kindergarten',                      'translated'),
		('Rebirth of The Golden Marriage',                            'Rebirth of The Golden Marriage',                                           'translated'),
		('Banished to Another World',                                 'Banished to Another World',                                                'translated'),
		('You\'re In Love With An Idiot',                             'You\'re In Love With An Idiot',                                            'translated'),
		('Years of Intoxication.',                                    'Years of Intoxication.',                                                   'translated'),
		('Blood Contract',                                            'Blood Contract',                                                           'translated'),
		('Number One Zombie Wife',                                    'Number One Zombie Wife',                                                   'translated'),
		('True Star',                                                 'True Star',                                                                'translated'),
		('s.c.i mystery',                                             'S.C.I Mystery Series',                                                     'translated'),
		('tharntype the series',                                      'tharntype the series',                                                     'translated'),
		('Dragon Flies Phoenix Dances',                               'Dragon Flies Phoenix Dances',                                              'translated'),
		('2gether the series',                                        '2gether the series',                                                       'translated'),
		('the sleuth of the ming dynasty',                            'the sleuth of the ming dynasty',                                           'translated'),
		('The Paternity Guard',                                       'The Paternity Guard',                                                      'translated'),
		('Love is More Than a Word',                                  'Love is More Than a Word',                                                 'translated'),
		('the en of love',                                            'the en of love',                                                           'translated'),
		('i’ll still love you even if you’re a man 2',                'i’ll still love you even if you’re a man 2',                               'translated'),
		('how to change: the love tactics of an innocence senior',    'how to change: the love tactics of an innocence senior',                   'translated'),
		('Winter Begonia',                                            'Winter Begonia',                                                           'translated'),
		('my accidental love is you',                                 'my accidental love is you',                                                'translated'),
		('the tales of thousands stars',                              'the tales of thousands stars',                                             'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)

	titlemap = [
		('The Ugly Empress vol ',       'The Ugly Empress',      'translated'),
		('The Ugly Empress, Chapter ',  'The Ugly Empress',      'translated'),
		('Blood Contract, Chapter ',    'Blood Contract',        'translated'),
		('Tensei Shoujo no Rirekisho',  'Tensei Shoujo no Rirekisho',      'translated'),
		('Master of Dungeon',           'Master of Dungeon',               'oel'),
	]

	for titlecomponent, name, tl_type in titlemap:
		if titlecomponent.lower() in item['title'].lower():
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False