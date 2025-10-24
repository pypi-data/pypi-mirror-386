import asyncio
import logging
import signal
from typing import Any, Callable, Coroutine, TypeAlias

import httpx

import botapi
from botapi.types import Update

logger = logging.getLogger(__name__)

UpdateHandler: TypeAlias = Callable[[Update], Coroutine[Any, Any, None]]


class GetUpdatesAsyncDispatcher:
	update_handler: UpdateHandler
	tasks_shutdown_timeout: float
	tasks: set[asyncio.Task] # prevent gc from collecting tasks before they finish
	bot: 'botapi.api.BotAPI'
	reconnect_delay: float
	allowed_updates: list[str]
	offset: int
	
	def __init__(
		self,
		update_handler: UpdateHandler,
		bot: 'botapi.api.BotAPI',
		allowed_updates: list[str], # botapi.enums.UpdateType
		reconnect_delay: float = 5,
		shutdown_wait_timeout: float = 3
	) -> None:
		'''
		Dispatcher that receives updates with long polling (`getUpdates`)
		and dispatches them to a registered async handler.
		
		Args:
			update_handler (UpdateHandler):
				Async function to handle received messages.
			bot (botapi.api.BotAPI):
				A `Bot` instance.
			allowed_updates (list[botapi.enums.UpdateType]):
				List of allowed update types.
			reconnect_delay (float, optional):
				Delay in seconds before retrying after a failed request.
			shutdown_wait_timeout (float, optional):
				Timeout in seconds to wait for pending tasks to complete on shutdown.
		'''
		self.bot = bot
		self.update_handler = update_handler
		self.allowed_updates = allowed_updates
		self.reconnect_delay = reconnect_delay
		self.shutdown_wait_timeout = shutdown_wait_timeout
		self.offset = -1
		self.tasks = set()
		
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
			
	async def _dispatch(self, update: Update) -> None:
		'''
		Dispatches the update to the registered handler, in a new task.
		'''
		task = asyncio.create_task(self.update_handler(update))
		self.tasks.add(task)
		task.add_done_callback(self._task_done_callback)
		
	async def _shutdown(self) -> None:
		'''
		Wait for pending/running tasks to complete (with a timeout),
		then exits.
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
				
	async def _listen_forever(self) -> None:
		'''
		Listen for incoming updates forever, with long polling.
		In case of connection errors, it will retry after a delay.
		'''
		GET_UPDATES_TIMEOUT = int(self.bot.session.timeout.read or 60) - 10 # 10 seconds less than the read timeout
		
		self.offset = -1
		
		while True:
			try:
				result = await self.bot.get_updates(
					offset=self.offset,
					limit=100,
					timeout=GET_UPDATES_TIMEOUT,
					allowed_updates=self.allowed_updates,
				)
				
				if result:
					self.offset = result[-1].update_id + 1 # next update offset
					
					for update in result:
						try:
							await self._dispatch(update)
						except Exception:
							logger.exception('Exception raised in the dispatcher:')
							
							
			except botapi.errors.BotAPIError as e:
				# logger.exception('Bot API error:')
				logger.error('Bot API error, retrying soon: %s', e)
				await asyncio.sleep(delay=self.reconnect_delay)
				#TODO manage specific error codes (like 409 Conflict or 401 Unauthorized)
				
			except httpx.RequestError as e:
				# logger.exception('Request error:')
				logger.error('Request error, retrying soon: %s', e)
				await asyncio.sleep(delay=self.reconnect_delay)
				
			except asyncio.CancelledError:
				logger.info('Received termination signal')
				break
				
			except Exception: # catch-all for unexpected exceptions; NEVER let the bot crash!
				logger.exception('Unexpected exception in listen_forever:')
				await asyncio.sleep(delay=self.reconnect_delay)
				
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
		Waits for incoming updates forever, and dispatches them to the registered handler.
		This method **is blocking**, it terminates on SIGINT/SIGTERM signals.
		
		This method automatically retries failed `getUpdates` requests after a short delay.
		
		Example:
		```python
		dispatcher = GetUpdatesAsyncDispatcher(
			update_handler=handler,
			bot=bot,
			allowed_updates=[
				botapi.enums.UpdateType.MESSAGE,
				botapi.enums.UpdateType.EDITED_MESSAGE,
				botapi.enums.UpdateType.CALLBACK_QUERY,
				botapi.enums.UpdateType.CHAT_MEMBER_UPDATED,
				botapi.enums.UpdateType.CHAT_JOIN_REQUEST,
			]
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
			
