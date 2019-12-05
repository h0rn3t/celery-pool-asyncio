# import asyncio
from celery import beat

from . import pool


async def apply_async(self, entry, producer=None, advance=True, **kwargs):
    # Update time-stamps and run counts before we actually execute,
    # so we have that done if an exception is raised (doesn't schedule
    # forever.)
    entry = self.reserve(entry) if advance else entry
    task = self.app.tasks.get(entry.task)

    try:
        if task:
            return await task.apply_async(
                entry.args, entry.kwargs,
                producer=producer,
                **entry.options,
            )
        else:
            return await self.send_task(
                entry.task,
                entry.args,
                entry.kwargs,
                producer=producer,
                **entry.options,
            )
    except Exception as exc:  # pylint: disable=broad-except
        excmsg = "Couldn't apply scheduled task {entry.name}: {exc}".format(
            entry=entry,
            exc=exc,
        )
        beat.reraise(
            beat.SchedulingError,
            beat.SchedulingError(excmsg),
            beat.sys.exc_info()[2],
        )
    finally:
        self._tasks_since_sync += 1
        if self.should_sync():
            self._do_sync()


def apply_entry(self, entry, producer=None):
    beat.info('Scheduler: Sending due task %s (%s)', entry.name, entry.task)
    try:
        coro = self.apply_async(
            entry=entry,
            producer=producer,
            advance=False,
        )
        result = pool.run(coro)
    except Exception as exc:  # pylint: disable=broad-except
        beat.error(
            'Message Error: %s\n%s',
            exc,
            beat.traceback.format_stack(),
            exc_info=True,
        )
    else:
        beat.debug(
            '%s sent. id->%s',
            entry.task,
            result.id,
        )


def patch_beat():
    ScheduleEntry = beat.ScheduleEntry
    ScheduleEntry.apply_async = apply_async
    ScheduleEntry.apply_entry = apply_entry
