def extractIsotlsCom(item):
	'''
	Parser for 'isotls.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	if item['tags'] == []:
		titlemap = [
			('Quick Transmigration Female Lead: Male God, Never Stopping Chapter',       'Quick Transmigration Female Lead: Male God, Never Stopping',                      'translated'),
			('The Lover\'s Prattle',                                                      'The Lover\'s Prattle',                                                                      'translated'),
			('Rescuing the Blackened Male Lead',                                         'Rescuing the Blackened Male Lead',                                               'translated'),
			('I Swear I Won\'t Bother You Again Chapter',                                'I Swear I Won\'t Bother You Again',                           'translated'),
			('My Husband With Scholar Syndrome Chapter ',                                'My Husband With Scholar Syndrome',                           'translated'),
			('Pampering My Husband Every Day Chapter ',                                  'Pampering My Husband Every Day',                             'translated'),
			('You Look Like You\'re Made of Money Chapter ',                             'You Look Like You\'re Made of Money',                        'translated'),
			('This Way of Transmigration is Definitely Wrong! Chapter ',                 'This Way of Transmigration is Definitely Wrong! ',           'translated'),
			('the villainess wants to marry a commoner',                                 'the villainess wants to marry a commoner!',                   'translated'),
			('The Transmigration Routine of Always Being Captured by ML Chapter ',       'the transmigration routine of always being captured by the male lead',                      'translated'),
			('The Villain Has Blackened Again Chapter ',                                 'the villain has blackened again',                                                           'translated'),
			('Believe It Or Not, I Already Caught You Chapter ',                         'Believe It Or Not, I Already Caught You',                                        'translated'),
			('Need to Propose to Seven Men What to Do Chapter ',                         'need to propose to seven men, what to do!',                                                 'translated'),
			('Daily Life of a Wealthy Woof chapter ',                                    'Daily Life of a Wealthy Woof',                                                              'translated'),
			('There\'s A Beauty Chapter ',                                               'There\'s A Beauty',               'translated'),
			('How Much for a Pound of Cuteness Chapter ',                                'How Much for a Pound of Cuteness',               'translated'),
			('Return of the Goddess Chapter ',                                           'Return of the Goddess',           'translated'),
			('Rebirth To Become The President’s Omega Wife Chapter ',                    'Rebirth To Become The President’s Omega Wife',               'translated'),
			('Tensei Shoujo no Rirekisho',                                               'Tensei Shoujo no Rirekisho',               'translated'),
			('Master of Dungeon',                                                        'Master of Dungeon',                        'oel'),
			
			
			
		]

		for titlecomponent, name, tl_type in titlemap:
			if titlecomponent.lower() in item['title'].lower():
				return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	tagmap = [
		('quick transmigration female lead: male god never stopping',                  'Quick Transmigration Female Lead: Male God, Never Stopping',                                'translated'),
		('Rescuing the Blackened Male Lead',                                           'Rescuing the Blackened Male Lead',                                                          'translated'),
		('the transmigration routine of always being captured by the male lead',       'the transmigration routine of always being captured by the male lead',                      'translated'),
		('The Lover\'s Prattle',                                                       'The Lover\'s Prattle',                                                                      'translated'),
		('i swear i won\'t bother you again',                                          'i swear i won\'t bother you again',                                                         'translated'),
		('pampering my husband every day',                                             'pampering my husband every day',                                                            'translated'),
		('the villainess wants to marry a commoner!',                                  'the villainess wants to marry a commoner!',                                                 'translated'),
		('husband with scholar syndrome',                                              'My Husband With Scholar Syndrome',                                                          'translated'),
		('you look like you’re made of money',                                         'You Look Like You\'re Made of Money',                                                       'translated'),
		('this way of transmigration is definitely wrong',                             'This Way of Transmigration is Definitely Wrong! ',                                          'translated'),
		('need to propose to seven men, what to do!',                                  'need to propose to seven men, what to do!',                                                 'translated'),
		('poisonous peasant concubine',                                                'poisonous peasant concubine',                                                               'translated'),
		('Daily Life of a Wealthy Woof',                                               'Daily Life of a Wealthy Woof',                                                              'translated'),
		('The Life After MArrying My Sworn Enemy',                                     'The Life After Marrying My Sworn Enemy',                                                    'translated'),
		('end of world\'s businessman',                                                'end of world\'s businessman',                                                               'translated'),
		('the villain has blackened again',                                            'the villain has blackened again',                                                           'translated'),
		('believe it or not',                                                          'Believe It Or Not, I Already Caught You',                                                   'translated'),
		('There\'s A Beauty',                                                          'There\'s A Beauty',                                                                         'translated'),
		('rebirth to become the president’s omega wife',                               'rebirth to become the president’s omega wife',                                              'translated'),
		('pampered fei: brimming with cuteness',                                       'pampered fei: brimming with cuteness',                                                      'translated'),
		('Sinister Ex-Girlfriend',                                                     'Sinister Ex-Girlfriend',                                                                    'translated'),
		('the traveling hero won’t let the innkeeper’s son escape',                    'the traveling hero won’t let the innkeeper’s son escape',                                   'translated'),
		('how to die as heavy as mt tai',                                              'how to die as heavy as mt tai',                                                             'translated'),
		('the villainess, cecilia silvy doesn\'t want to die so she decided to crossdress',       'the villainess, cecilia silvy doesn\'t want to die so she decided to crossdress',                      'translated'),
		('Return of the Goddess',                                                                 'Return of the Goddess',                                                                                'translated'),
		('the cannon fodder won\'t meddle',                                                       'the cannon fodder won\'t meddle',                                                                      'translated'),
		('novel wars',                                                                            'novel wars',                                                                                           'translated'),
		('how much for a pound of cuteness',                                                      'how much for a pound of cuteness',                                                                     'translated'),
		('high energy qr code',                                                                   'high energy qr code',                                                                                  'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False