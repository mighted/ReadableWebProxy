#!flask/bin/python

import sys
import traceback
import datetime
import threading
import time
from pytz import reference
import pytz

import sqlalchemy.exc

from apscheduler.schedulers.blocking   import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool        import ProcessPoolExecutor
from apscheduler.executors.pool        import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy  import SQLAlchemyJobStore
from apscheduler.triggers.interval     import IntervalTrigger

import config
import common.database as db
import common.LogBase as LogBase

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
import settings

from common.db_engine import SQLALCHEMY_DATABASE_URI
import activeScheduledTasks

CALLABLE_LUT = {}
for sched_item, dummy_interval in activeScheduledTasks.scrapePlugins.values():
	print("Plugin: %s -> %s" % (sched_item.__name__, sched_item))
	assert sched_item.__name__ not in CALLABLE_LUT, "Plugin appears twice in call lookup table (%s)?" % sched_item.__name__
	CALLABLE_LUT[sched_item.__name__] = sched_item


class JobNameException(Exception):
	pass

class JobCaller(LogBase.LoggerMixin):

	loggerPath = "Main.PluginRunner"

	def __init__(self, job_name):

		if not job_name in CALLABLE_LUT:
			raise JobNameException("Callable '%s' is not in the class lookup table: '%s'!" % (job_name, CALLABLE_LUT))
		self.runModule = CALLABLE_LUT[job_name]
		self.job_name = job_name

		self.log.info("Invoking class %s as scheduled job", self.runModule)


		with db.session_context() as session:
			try:
				query = session.query(db.PluginStatus).filter(db.PluginStatus.plugin_name == job_name)
				have = query.scalar()
				if not have:
					new = db.PluginStatus(plugin_name=job_name)
					session.add(new)
					session.commit()
			except sqlalchemy.exc.OperationalError:
				session.rollback()
			except sqlalchemy.exc.InvalidRequestError:
				session.rollback()

			finally:
				db.delete_db_session()

	def doCall(self):

		self.log.info("Calling job %s", self.job_name)

		with db.session_context() as session:
			item = session.query(db.PluginStatus).filter(db.PluginStatus.plugin_name == self.job_name).scalar()

			if not item:
				self.log.error("Don't have instance for job %s? How did this happen?", self.job_name)
				raise RuntimeError

			if item.is_running:
				session.commit()
				self.log.error("Plugin %s is already running! Not doing re-entrant call!", self.job_name)
				return

			item.is_running = True
			item.last_run = datetime.datetime.now()
			session.commit()

		try:
			self._doCall()
		except Exception:

			with db.session_context() as session:
				item = session.query(db.PluginStatus).filter(db.PluginStatus.plugin_name == self.job_name).one()

				item.last_error      = datetime.datetime.now()
				item.last_error_msg  = traceback.format_exc()
			raise
		finally:

			with db.session_context() as session:
				item2 = session.query(db.PluginStatus).filter(db.PluginStatus.plugin_name == self.job_name).one()
				item2.is_running = False
				item2.last_run_end = datetime.datetime.now()
				session.commit()
				db.delete_db_session()
		self.log.info("Job %s complete.", self.job_name)

	# Should probably be a lambda? Laaaazy.
	def _doCall(self):
		instance = self.runModule()
		instance._go()

	@classmethod
	def callMod(cls, passMod):
		mod = cls(passMod)
		mod.doCall()

def do_call(job_name):
	caller = JobCaller(job_name)

	while 1:
		try:
			caller.doCall()
			break
		except JobNameException:
			print("Error! Invalid job name: '%s'!" % job_name)
			break
		except AttributeError:
			traceback.print_exc()
			print("Call error!")



def scheduleJobs(sched, timeToStart):

	jobs = []
	offset = 0
	for key, value in activeScheduledTasks.scrapePlugins.items():
		baseModule, interval = value
		jobs.append((key, baseModule, interval, timeToStart+datetime.timedelta(seconds=60*offset)))
		offset += 1

	activeJobs = []


	print("JobCaller: ", JobCaller)
	print("JobCaller.callMod: ", JobCaller.callMod)

	for jobId, callee, interval, startWhen in jobs:
		jId = str(jobId) + " " + callee.__name__
		activeJobs.append(jId)
		havejob = sched.get_job(jId)
		ok = True


		if not havejob:
			ok = False

		elif isinstance(havejob.trigger, IntervalTrigger):
			# If it's the right kind of trigger, but the interval is more
			# then 1 second away from the interval we want, reset the job
			j_interval = havejob.trigger.interval_length
			int_err = abs(j_interval - interval)
			if int_err > 1:
				print("Job trigger interval seems to mismatch. Recreating job: ", jId)
				sched.remove_job(jId)
				ok = False
		else:
			sched.remove_job(jId)
			ok = False


		if ok:
			print("JobID %s already scheduled." % jId)
		else:
			print("Need to add new job for ID: ", jId)
			sched.add_job(do_call,
						args               = (callee.__name__, ),
						trigger            = 'interval',
						# jobstore           = 'sqlalchemy',
						seconds            = interval,
						next_run_time      = startWhen,
						id                 = jId,
						replace_existing   = True,
						max_instances      = 5,
						coalesce           = True,
						misfire_grace_time = 2**30)


	for job in sched.get_jobs():
		if not job.id in activeJobs:
			print("Extra job in jobstore: %s. Removing." % job.id)
			sched.remove_job(job.id)


	# Do this last, because they're ephemeral
	for callable_f in activeScheduledTasks.autoscheduler_plugins:
		callable_f(sched)


def resetRunStates():
	print("JobSetup call resetting run-states!")
	with db.session_context() as session:
		session.query(db.PluginStatus).update({db.PluginStatus.is_running : False})
		session.commit()
	print("Run-states reset.")


def dump_scheduled_jobs(sched):
	print("Scheduled jobs:")
	existing = sched.get_jobs()
	if not existing:
		print("	No jobs in scheduler!")

	tznow = datetime.datetime.now(tz=pytz.utc)
	for job in existing:
		print("	", job, job.args, "running in:", job.next_run_time - tznow, (job.id, ))

	with db.session_context() as session:
		running = session.query(db.PluginStatus).filter(db.PluginStatus.is_running == True).all()
		print("Running jobs:")
		for jitem in running:
			print("	", jitem.plugin_name, jitem.is_running, jitem.last_run, jitem.last_error, jitem.last_error_msg)
		if not running:
			print("	<None!>")

		print("Running threads:")
		for thread in threading.enumerate():
			print("	", thread.getName(), thread)


	# with db.session_context() as session:
	# 	items = session.query(db.PluginStatus).all()
	# 	print("Jobs in DB:")
	# 	for item in items:
	# 		print("	", item)


def go_sched():
	resetRunStates()

	sched = BackgroundScheduler({
			'apscheduler.jobstores.default': {
				'type': 'sqlalchemy',
				'url': SQLALCHEMY_DATABASE_URI
			},
			'apscheduler.jobstores.memory': {
				'type': 'memory'
			},
			# 'apscheduler.executors.default': {
			# 	'class': 'apscheduler.executors.pool:ProcessPoolExecutor',
			# 	'max_workers': '10'
			# },
			'apscheduler.executors.default': {
				'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
				'max_workers': '10'
			},
			'apscheduler.job_defaults.coalesce': 'true',
			'apscheduler.job_defaults.max_instances': '5',
		})

	# Apparently the scheduler won't pull the jobs from the backend until you start it,
	# so if you're trying to validate the jobs already present, you have to start it
	# before iterating over jobs in the jobstore.
	sched.start()

	print("Jobs in scheduler:")
	dump_scheduled_jobs(sched)
	startTime = datetime.datetime.now(tz=pytz.utc)+datetime.timedelta(seconds=10)
	scheduleJobs(sched, startTime)
	dump_scheduled_jobs(sched)
	print("Starting scheduler.")
	while 1:
		try:
			dump_scheduled_jobs(sched)
			time.sleep(30)
		except KeyboardInterrupt:
			break
	sched.shutdown()


if __name__ == "__main__":

	print("Auxilliary modes: 'test', 'scheduler'.")


	largv = [tmp.lower() for tmp in sys.argv]


	settings.MAX_DB_SESSIONS = settings.NO_PROCESSES + 5
	settings.MAX_DB_SESSIONS = 4
	go_sched()
