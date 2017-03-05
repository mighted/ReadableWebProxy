
import calendar
import datetime
import json
import os
import os.path
import shutil
import traceback
from concurrent.futures import ThreadPoolExecutor

import urllib.error
import urllib.parse

from sqlalchemy import and_
from sqlalchemy import or_
import sqlalchemy.exc
from sqlalchemy_continuum.utils import version_table

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()

import common.database as db


import flags
import pprint
import config

import WebMirror.OutputFilters.rss.FeedDataParser
import WebMirror.OutputFilters.util.feedNameLut
import astor

def add_name(sess, netloc, nametxt):
	check = sess.query(db.RssFeedEntry) \
		.filter(db.RssFeedEntry.feed_name == nametxt) \
		.scalar()

	if not check:
		print("Wat?", nametxt)
		return


	have = sess.query(db.RssFeedUrlMapper) \
		.filter(db.RssFeedUrlMapper.feed_netloc == netloc) \
		.scalar()
	if have:
		assert check.id == have.feed_id, "Wat: {}, {} ({}, {})".format(check.id, have.feed_id, netloc, nametxt)
	else:
		new = db.RssFeedUrlMapper(
				feed_netloc = netloc,
				feed_id     = check.id,
			)
		sess.add(new)
		sess.commit()

def update_func(sess, feed_name, fcont):
	res = sess.query(db.RssFeedEntry) \
		.filter(db.RssFeedEntry.feed_name == feed_name) \
		.scalar()

	if res:
		print("have:", feed_name)
		if not res.func == fcont:
			print("Contents mismatch!", feed_name)
			res.func = fcont
			sess.commit()

		print("	Func: ", res.get_func())
	else:
		new = db.RssFeedEntry(
				version   = 1,
				feed_name = feed_name,
				enabled   = False,
				func      = fcont,
			)
		print("Adding ", feed_name)
		sess.add(new)
		sess.commit()

def exposed_import_feed_parse_funcs():
	'''
	Import the feed parsing functions into the database.
	'''

	sess = db.get_db_session()

	parse_map = WebMirror.OutputFilters.rss.FeedDataParser.RSS_PARSE_FUNCTION_MAP
	for key, func in parse_map.items():
		func_str = astor.to_source(astor.code_to_ast(func), indent_with="	")
		update_func(sess, key, func_str)

	name_map = WebMirror.OutputFilters.util.feedNameLut.mapper

	for key, val in name_map.items():
		print(key, val)
		add_name(sess, key, val)

def ret_to_dict_list(keys, iterable):

	as_dict = [
			dict(
				zip(
					keys,
					(
						single.strftime('%s') if isinstance(single, datetime.datetime) else single
					for
						single in tmp
					)
				)
			)
		for
			tmp in iterable
		]
	return as_dict

def exposed_dump_raw_feed_data():
	'''
	Dump the raw feed data to a json file.
	'''
	import json

	sess = db.get_db_session()
	print("Selecting 1")
	feed_pages = sess.execute("SELECT * FROM feed_pages;")
	print("Selecting 2")
	nu_outbound_wrappers = sess.execute("SELECT * FROM nu_outbound_wrappers;")

	ret = {}
	print("processing ret 1")
	cols_feed = ('id', 'type', 'srcname', 'feedurl', 'contenturl', 'contentid', 'title', 'contents', 'updated', 'published', 'feed_id')
	ret['feed_pages'] = ret_to_dict_list(cols_feed, feed_pages)

	print("processing ret 2")
	nucols = ['id', 'actual_target', 'client_id', 'client_key', 'groupinfo', 'outbound_wrapper', 'referrer', 'releaseinfo', 'seriesname', 'validated', 'released_on']
	ret['nu_outbound_wrappers'] = ret_to_dict_list(nucols, nu_outbound_wrappers)

	print("Dumping ret")

	with open("db_bak_{}.json".format(str(datetime.datetime.now()).replace(":", "-").replace(" ", "_")), "w") as fp:
		json.dump(ret, fp, indent="	")


