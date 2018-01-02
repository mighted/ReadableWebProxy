

import time
import os
import multiprocessing
import signal
import logging
import logSetup
import cProfile
import traceback
import threading
import sys
import queue

import cachetools

# from pympler.tracker import SummaryTracker, summary, muppy
# import tracemalloc

import sqlalchemy.exc
from sqlalchemy.sql import text
from sqlalchemy.sql import func


if '__pypy__' in sys.builtin_module_names:
	import psycopg2cffi as psycopg2
else:
	import psycopg2


import config
import runStatus
import concurrent.futures

import WebMirror.Engine
import WebMirror.rules
import common.util.urlFuncs as urlFuncs
import common.database as db
import WebMirror.JobDispatcher as njq

import common.stuck

import common.get_rpyc

def initializeStartUrls(rules):
	print("Initializing all start URLs in the database")
	sess = db.get_db_session()
	for ruleset in [rset for rset in rules if rset['starturls']]:
		for starturl in ruleset['starturls']:
			have = sess.query(db.WebPages) \
				.filter(db.WebPages.url == starturl)   \
				.count()
			if not have:
				netloc = urlFuncs.getNetLoc(starturl)
				new = db.WebPages(
						url               = starturl,
						starturl          = starturl,
						netloc            = netloc,
						type              = ruleset['type'],
						priority          = db.DB_IDLE_PRIORITY,
						distance          = db.DB_DEFAULT_DIST,
						normal_fetch_mode = ruleset['normal_fetch_mode'],
					)
				print("Missing start-url for address: '{}'".format(starturl))
				sess.add(new)
			try:
				sess.commit()
			except sqlalchemy.SQLAlchemyError:
				print("Failure inserting start url for address: '{}'".format(starturl))

				sess.rollback()
	sess.close()
	db.delete_db_session()

# def resetInProgress():
# 	print("Resetting any stalled downloads from the previous session.")

# 	sess = db.get_db_session()
# 	sess.query(db.WebPages) \
# 		.filter(
# 				(db.WebPages.state == "fetching")           |
# 				(db.WebPages.state == "processing")         |
# 				(db.WebPages.state == "specialty_deferred") |
# 				(db.WebPages.state == "specialty_ready")
# 				)   \
# 		.update({db.WebPages.state : "new"})
# 	sess.commit()
# 	sess.close()
# 	db.delete_db_session()



def resetInProgress():

	sess = db.get_db_session()

	commit_interval =  50000
	step            = 250000

	with db.session_context() as sess:
		print("Getting minimum row in need or update..")
		start = sess.execute("""SELECT min(id) FROM web_pages WHERE state = 'fetching' OR state = 'processing' OR state = 'specialty_deferred' OR state = 'specialty_ready'""")
		start = list(start)[0][0]
		if start is None:
			print("No rows to reset!")
			return
		print("Minimum row ID: ", start, "getting maximum row...")
		stop = sess.execute("""SELECT max(id) FROM web_pages WHERE state = 'fetching' OR state = 'processing' OR state = 'specialty_deferred' OR state = 'specialty_ready'""")
		stop = list(stop)[0][0]
		print("Maximum row ID: ", stop)


		print("Need to fix rows from %s to %s" % (start, stop))
		start = start - (start % step)

		changed = 0
		tot_changed = 0
		for idx in range(start, stop, step):
			try:
				# SQL String munging! I'm a bad person!
				# Only done because I can't easily find how to make sqlalchemy
				# bind parameters ignore the postgres specific cast
				# The id range forces the query planner to use a much smarter approach which is much more performant for small numbers of updates
				have = sess.execute("""UPDATE
											web_pages
										SET
											state = 'new'
										WHERE
											(state = 'fetching' OR state = 'processing' OR state = 'specialty_deferred' OR state = 'specialty_ready')
										AND
											id > {}
										AND
											id <= {};""".format(idx, idx+step))
				# print()

				processed  = idx - start
				total_todo = stop - start
				print('\r%10i, %10i, %7.4f, %6i, %8i\r' % (idx, stop, processed/total_todo * 100, have.rowcount, tot_changed), end="", flush=True)
				changed += have.rowcount
				tot_changed += have.rowcount
				if changed > commit_interval:
					print("Committing (%s changed rows)...." % changed, end=' ')
					sess.commit()
					print("done")
					changed = 0

			except sqlalchemy.exc.OperationalError:
				sess.rollback()
			except sqlalchemy.exc.InvalidRequestError:
				sess.rollback()


		sess.commit()

	db.delete_db_session()


def do_link_batch_update(logger, link_batch):
	with db.session_context() as sess:
		do_link_batch_update_sess(logger, sess, link_batch)

def do_link_batch_update_sess(logger, interface, link_batch):
	if not link_batch:
		return

	logger.info("Inserting %s items into DB in batch.", len(link_batch))
	# This is kind of horrible.
	raw_cur = interface.connection().connection.cursor()



	bulk_cmd = """
		INSERT INTO
		    web_pages
		    (url, starturl, netloc, distance, is_text, priority, type, addtime, state)
		VALUES
		    (%(url_{cnt})s, %(starturl_{cnt})s, %(netloc_{cnt})s, %(distance_{cnt})s, %(is_text_{cnt})s, %(priority_{cnt})s, %(type_{cnt})s, %(addtime_{cnt})s, %(state_{cnt})s)
		ON CONFLICT (url) DO
		    UPDATE
		        SET
		            state           = EXCLUDED.state,
		            starturl        = EXCLUDED.starturl,
		            netloc          = EXCLUDED.netloc,
		            is_text         = EXCLUDED.is_text,
		            distance        = LEAST(EXCLUDED.distance, web_pages.distance),
		            priority        = GREATEST(EXCLUDED.priority, web_pages.priority, %(maximum_priority_{cnt})s),
		            addtime         = LEAST(EXCLUDED.addtime, web_pages.addtime)
		        WHERE
		        (
		                web_pages.ignoreuntiltime < %(ignoreuntiltime_{cnt})s
		            AND
		                web_pages.url = EXCLUDED.url
		            AND
		                (web_pages.state = 'complete' OR web_pages.state = 'error')
		        )
		    ;
			""".replace("	", " ").replace("\n", " ")

	bulk_cmd = """
		SELECT upsert_link(
			%(url_{cnt})s,
			%(starturl_{cnt})s,
			%(netloc_{cnt})s,
			%(distance_{cnt})s,
			%(is_text_{cnt})s,
			%(priority_{cnt})s,
			%(type_{cnt})s,
			%(addtime_{cnt})s,
			%(state_{cnt})s,
			%(ignoreuntiltime_{cnt})s,
			%(maximum_priority_{cnt})s
			)
	""".replace("	", " ").replace("\n", " ")

	per_cmd = """
		INSERT INTO
		    web_pages
		    (url, starturl, netloc, distance, is_text, priority, type, addtime, state)
		VALUES
		    (%(url)s, %(starturl)s, %(netloc)s, %(distance)s, %(is_text)s, %(priority)s, %(type)s, %(addtime)s, %(state)s)
		ON CONFLICT (url) DO
		    UPDATE
		        SET
		            state           = EXCLUDED.state,
		            starturl        = EXCLUDED.starturl,
		            netloc          = EXCLUDED.netloc,
		            is_text         = EXCLUDED.is_text,
		            distance        = LEAST(EXCLUDED.distance, web_pages.distance),
		            priority        = GREATEST(EXCLUDED.priority, web_pages.priority, %(maximum_priority)s),
		            addtime         = LEAST(EXCLUDED.addtime, web_pages.addtime)
		        WHERE
		        (
		                web_pages.ignoreuntiltime < %(ignoreuntiltime)s
		            AND
		                web_pages.url = EXCLUDED.url
		            AND
		                (web_pages.state = 'complete' OR web_pages.state = 'error')
		        )
		    ;
			""".replace("	", " ").replace("\n", " ")

	while "  " in per_cmd:
		per_cmd = per_cmd.replace("  ", " ")
	while "  " in bulk_cmd:
		bulk_cmd = bulk_cmd.replace("  ", " ")


	bulk_cmd_list = [bulk_cmd.format(cnt=cnt) for cnt in range(len(self.batched_links))]
	bulk_cmd_assembled = "; ".join(bulk_cmd_list)

	# Build the overall SQL string
	# bulk_cmds = [bulk_cmd.format(cnt=cnt) for cnt in range(len(self.batched_links))]
	# bulk_cmd_assembled = bulk_cmd_prefix + ", ".join(bulk_cmds) + bulk_cmd_postfix

	# Build a nested list of dicts
	bulk_dict = [ {key+"_{cnt}".format(cnt=cnt) : val for key, val in self.batched_links[cnt].items()} for cnt in range(len(self.batched_links)) ]

	# Then flatten it down to a single dict
	bulk_dict = {k: v for d in bulk_dict for k, v in d.items()}

	# We use a statement timeout context of 5000 ms, so we don't get wedged on a lock.
	raw_cur.execute("SET statement_timeout TO 5000;")
	raw_cur.execute("BEGIN;")

	try:
		# We try the bulk insert command first.
		raw_cur.execute(bulk_cmd_assembled, bulk_dict)
		raw_cur.execute("COMMIT;")
		raw_cur.execute("RESET statement_timeout;")
		self.batched_links = []
		return

	except psycopg2.Error:
		logger.error("psycopg2.Error - Failure on bulk insert.")
		for line in traceback.format_exc().split("\n"):
			logger.error(line)
		raw_cur.execute("ROLLBACK;")

	# If the bulk insert failed, we then try a per-URL upsert
	# We only commit per-URL if we're tried to do per-URL update in batch, and failed.
	commit_each = False
	while 1:
		try:
			raw_cur.execute("BEGIN;")
			for paramset in self.batched_links:
				assert isinstance(paramset['starturl'], str)
				if len(paramset['url']) > 2000:
					logger.error("URL Is too long to insert into the database!")
					logger.error("URL: '%s'", paramset['url'])

				else:
					# Forward-data the next walk, time, rather then using now-value for the thresh.
					raw_cur.execute(per_cmd, paramset)
					if commit_each:
						raw_cur.execute("COMMIT;")
						raw_cur.execute("BEGIN;")

			raw_cur.execute("COMMIT;")
			break

		except psycopg2.Error:
			if commit_each is False:
				logger.warning("psycopg2.Error - Retrying with commit each.")
			else:
				logger.warning("psycopg2.Error - Retrying.")
				traceback.print_exc()

			raw_cur.execute("ROLLBACK;")
			commit_each = True

	raw_cur.execute("RESET statement_timeout;")



class UpdateAggregator(object):
	def __init__(self, msg_queue, db_interface):
		self.response_queue = msg_queue
		self.log = logging.getLogger("Main.LinkAggregator")

		try:
			signal.signal(signal.SIGINT, signal.SIG_IGN)
		except ValueError:
			self.log.warning("Cannot configure job fetcher task to ignore SIGINT. May be an issue.")

		# LRU Cache with a maxsize of 1 million, and a TTL of 6 hours
		self.seen = cachetools.TTLCache(maxsize=1000 * 1000, ttl=60 * 60 * 6)

		self.queue_items = 0
		self.link_count = 0
		self.amqpUpdateCount = 0
		self.deathCounter = 0

		self.batched_links = []
		self.pending_upserts = []

		self.db_int = db_interface
		self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

		self.check_init_func()

	def check_init_func(self):
		raw_cur = self.db_int.connection().connection.cursor()

		cmd = """
			CREATE OR REPLACE FUNCTION upsert_link(
			        url_v text,
			        starturl_v text,
			        netloc_v text,
			        distance_v integer,
			        is_text_v boolean,
			        priority_v integer,
			        type_v itemtype_enum,
			        addtime_v timestamp without time zone,
			        state_v dlstate_enum,
			        ignoreuntiltime_v timestamp without time zone,
			        max_priority_v integer
			        )
			    RETURNS VOID AS $$

			    INSERT INTO
			        web_pages
			         (url, starturl, netloc, distance, is_text, priority, type, addtime, state)
			    VALUES
			        (url_v, starturl_v, netloc_v, distance_v, is_text_v, priority_v, type_v, addtime_v, state_v)
			    ON CONFLICT (url) DO
			        UPDATE
			            SET
			                state           = EXCLUDED.state,
			                starturl        = EXCLUDED.starturl,
			                netloc          = EXCLUDED.netloc,
			                is_text         = EXCLUDED.is_text,
			                distance        = LEAST(EXCLUDED.distance, web_pages.distance),
			                priority        = GREATEST(EXCLUDED.priority, web_pages.priority, max_priority_v),
			                addtime         = LEAST(EXCLUDED.addtime, web_pages.addtime)
			            WHERE
			            (
			                    web_pages.ignoreuntiltime < ignoreuntiltime_v
			                AND
			                    web_pages.url = EXCLUDED.url
			                AND
			                    (web_pages.state = 'complete' OR web_pages.state = 'error')
			            )
			        ;

			$$ LANGUAGE SQL;

		"""
		raw_cur.execute(cmd)
		raw_cur.execute("COMMIT;")

	def check_open_rpc_interface(self):
		try:
			if self.rpc_interface.check_ok():
				return

		except Exception:
			try:
				self.rpc_interface.close()
			except Exception:
				pass
			self.rpc_interface = common.get_rpyc.RemoteJobInterface("FeedUpdater")

	def do_amqp(self, pkt):
		self.amqpUpdateCount += 1

		if self.amqpUpdateCount % 50 == 0:
			self.log.info("Transmitted AMQP messages: %s", self.amqpUpdateCount)

		if config.C_DO_RABBIT:
			self.check_open_rpc_interface()
			self.rpc_interface.put_feed_job(pkt)

	def _clear_upserts(self):
		self.pending_upserts = [tmp for tmp in self.pending_upserts if not tmp.done()]

	def dispatch_update(self):
		self._clear_upserts()
		while len(self.pending_upserts) > 25:
			self.log.warning("Have %s pending upsert jobs. Waiting for them to complete", len(self.pending_upserts))
			time.sleep(1)
			self._clear_upserts()

		newupsert = self.executor.submit(do_link_batch_update, args=(self.log, self.batched_links))
		self.pending_upserts.append(newupsert)
		self.batched_links = []

	def do_link(self, linkdict):

		assert 'url'              in linkdict
		assert 'starturl'         in linkdict
		assert 'netloc'           in linkdict
		assert 'distance'         in linkdict
		assert 'is_text'          in linkdict
		assert 'priority'         in linkdict
		assert 'type'             in linkdict
		assert 'state'            in linkdict
		assert 'addtime'          in linkdict
		assert 'ignoreuntiltime'  in linkdict
		assert 'maximum_priority' in linkdict

		url = linkdict['url']

		# Only allow items through if they're not in the LRU cache, or have not been upserted
		# in the last 6 hours
		if url not in self.seen:
			self.link_count += 1

			# Fucking huzzah for ON CONFLICT!
			self.batched_links.append(linkdict)
			# Kick item up to the top of the LRU list
			self.seen[url] = True

			if len(self.batched_links) >= 500:
				self.dispatch_update()

	def do_task(self):

		target, value = self.response_queue.get_nowait()

		if (self.queue_items % 50) == 0:
			self.log.info("Aggregator active. Total cached URLs: %s, Items in processing queue: %s, transmitted release messages: %s, batchLink buf: %s (%s).",
				self.seen.currsize, self.response_queue.qsize(), self.amqpUpdateCount, len(self.batched_links), self.link_count)

		self.queue_items += 1

		if target == "amqp_msg":
			if config.C_DO_RABBIT:
				self.do_amqp(value)
		elif target == "new_link":
			self.do_link(value)
		else:
			print("Todo", target, value)

	def run(self):
		while 1:
			try:
				while 1:
					# print("Loopin!")
					self.do_task()
					self.deathCounter = 0
			except queue.Empty:
				if runStatus.agg_run_state.value != 1:

					self.deathCounter += 1
					time.sleep(0.1)
					if self.deathCounter > 5:
						self.log.info("Aggregator thread exiting.")
						break
			except Exception:
				self.log.error("Exception in aggregator!")
				for line in traceback.format_exc().split("\n"):
					self.log.error(line.rstrip())
			# Fffffuuuuu time.sleep barfs on KeyboardInterrupt
			try:
				time.sleep(1)
				self.dispatch_update()

			except KeyboardInterrupt:
				pass

		self.dispatch_update()

	def close(self):
		if config.C_DO_RABBIT:
			self.log.info("Aggregator thread closing interface.")
			# self._amqpint.close()

	@classmethod
	def launch_agg(cls, agg_queue):

		try:
			common.stuck.install_pystuck()
			agg_db = db.get_db_session()
			instance = cls(agg_queue, agg_db)
			instance.run()
			instance.close()
		except Exception as e:
			import traceback
			print()
			print()
			print()
			print()
			print()
			print()
			print("Aggregator exception!")
			traceback.print_exc()
