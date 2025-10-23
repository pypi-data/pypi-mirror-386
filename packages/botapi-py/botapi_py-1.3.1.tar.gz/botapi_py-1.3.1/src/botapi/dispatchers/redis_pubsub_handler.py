import asyncio
import json
import logging
import signal
from typing import Any, Callable, Coroutine, TypeAlias

import pydantic
from botapi.types import Update

try:
	import redis.asyncio as redis
	from redis.asyncio.client import PubSub
	_has_redis = True
except ImportError:
	_has_redis = False
	
logger = logging.getLogger(__name__)

UpdateHandler: TypeAlias = Callable[[Update], Coroutine[Any, Any, None]]


class RedisPubSubAsyncDispatcher:
	update_handler: UpdateHandler
	tasks_shutdown_timeout: float
	tasks: set[asyncio.Task] # prevent gc from collecting tasks before they finish
	redis_client: redis.Redis
	redis_reconnect_delay: float
	pubsub: PubSub
	pubsub_channel: str
	
	def __init__(
		self,
		update_handler: UpdateHandler,
		pubsub_channel: str,
		redis_client: redis.Redis,
		redis_reconnect_delay: float = 5,
		shutdown_wait_timeout: float = 3
	) -> None:
		'''
		Dispatcher that receives updates from a Redis PUB/SUB
		and dispatches them to a registered async handler.
		
		Args:
			update_handler (UpdateHandler):
				Async function to handle received messages.
			redis_client (redis.Redis):
				Redis client instance.
			pubsub_channel (str):
				Name of the Redis PUB/SUB channel to subscribe to.
			redis_reconnect_delay (float, optional):
				Delay in seconds before retrying connection on failure.
			shutdown_wait_timeout (float, optional):
				Timeout in seconds to wait for pending tasks to complete on shutdown.
		'''
		if not _has_redis:
			raise ImportError('redis-py is not installed. Install `botapi-py[redis]` to use this dispatcher.')
			
		self.redis_client = redis_client
		self.update_handler = update_handler
		self.pubsub_channel = pubsub_channel
		self.redis_reconnect_delay = redis_reconnect_delay
		self.shutdown_wait_timeout = shutdown_wait_timeout
		self.tasks = set()
		self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
		
	def _task_done_callback(self, task: asyncio.Task) -> None:
		'''
		Callback that is called by the event loop when an update_handler task is done.
		
		This catches and logs unhandled exceptions, so that they don't pass silently.
		Also, it removes the completed task from the `tasks` set.
		'''
		try:
			task.result()
		except Exception:
			logger.exception('Exception in handler')
			
		finally:
			self.tasks.discard(task)
			
	async def _message_to_update(self, message: str) -> Update:
		'''
		Converts raw message (containing a JSON) into a Python dict (with json),
		then validated it and loads it into an Update object with Pydantic.
		'''
		data = json.loads(message)
		return Update.de_json(data)
		
	async def _dispatch(self, message: str) -> None:
		'''
		Converts raw message (containing a JSON) into a Python dict,
		then dispatch it, to the registered handler, in a new task.
		'''
		try:
			update = await self._message_to_update(message)
		except json.JSONDecodeError:
			logger.exception('Failed to decode JSON:')
		except pydantic.ValidationError:
			logger.exception('Failed pydantic validation:')
		else:
			task = asyncio.create_task(self.update_handler(update))
			self.tasks.add(task)
			task.add_done_callback(self._task_done_callback)
			
	async def _shutdown(self) -> None:
		'''
		Wait for pending/running tasks to complete (with a timeout),
		then close the Redis connection.
		'''
		if self.tasks:
			logger.info('Waiting for %d tasks to complete...', len(self.tasks))
			try:
				await asyncio.wait_for(
					asyncio.gather(*self.tasks, return_exceptions=True),
					timeout=self.shutdown_wait_timeout
				)
			except asyncio.TimeoutError:
				logger.warning('Some tasks were still running after timeout, CancelledError was raised.')
				
		try:
			await self.redis_client.aclose()
		except Exception:
			logger.exception('Exception while closing Redis connection:')
			
	async def _listen_forever(self) -> None:
		'''
		Listen for messages coming from the PUBSUB channel forever.
		In case of connection errors, it will retry after a delay.
		'''
		while True:
			try:
				logger.info('Subscribing to channel %s...', self.pubsub_channel)
				await self.pubsub.subscribe(self.pubsub_channel)
				
				logger.info('Subscribed to %s. Waiting for messages...', self.pubsub_channel)
				
				async for message in self.pubsub.listen():
					if message['type'] == 'message':
						try:
							await self._dispatch(message['data'])
						except Exception:
							logger.exception('Exception raised in the dispatcher:')
							
			except redis.ConnectionError as e:
				# logger.exception('Connection error, attempting to reconnect:')
				logger.error('Connection error, attempting to reconnect: %s', e)
				await asyncio.sleep(delay=self.redis_reconnect_delay)
				
				# await self.pubsub.unsubscribe()
				
			except asyncio.CancelledError:
				logger.info('Received termination signal')
				break
				
			except Exception: # catch-all for unexpected exceptions; NEVER let the bot crash!
				logger.exception('Unexpected exception in listen_forever:')
				await asyncio.sleep(delay=self.redis_reconnect_delay)
				
	async def _register_signal_handlers(self, task_to_cancel: asyncio.Task) -> None:
		'''
		Register signal handlers for graceful shutdown on:
		- SIGTERM
		- SIGINT
		'''
		loop = asyncio.get_running_loop()
		
		for sig in (signal.SIGTERM, signal.SIGINT):
			loop.add_signal_handler(
				sig,
				task_to_cancel.cancel
			)
			
	async def run_forever(self) -> None:
		'''
		Wait for incoming updates forever. This method **is blocking**.
		Retries automatically after Redis connection errors, terminates on SIGINT/SIGTERM.
		
		Example:
		```python
		redis_client = redis.Redis(
			host='localhost',
			port=6379
		)
		dispatcher = RedisPubSubAsyncDispatcher(
			update_handler=handler,
			pubsub_channel='my_channel',
			redis_client=redis_client
		)
		await dispatcher.run_forever()
		```
		'''
		task = asyncio.create_task(self._listen_forever())
		
		try:
			await task
		except asyncio.CancelledError:
			logger.info('Received termination signal')
		finally:
			logger.warning('Shutting down...')
			await self._shutdown()
			
