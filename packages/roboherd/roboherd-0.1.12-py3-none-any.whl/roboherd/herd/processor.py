import asyncio
import logging
from dataclasses import dataclass
from typing import List

from almabtrieb import Almabtrieb

from roboherd.cow import RoboCow


logger = logging.getLogger(__name__)


@dataclass
class HerdProcessor:
    connection: Almabtrieb
    incoming_handlers: List[RoboCow]

    def create_tasks(self, task_group: asyncio.TaskGroup):
        tasks = []
        if len(self.incoming_handlers) > 0:
            tasks.append(task_group.create_task(self.process_incoming(self.connection)))

        return tasks

    async def process_incoming(self, connection):
        actor_id_to_cow_map = {}
        for cow in self.incoming_handlers:
            actor_id_to_cow_map[cow.internals.actor_id] = cow

        logger.info("Incoming processing started for %s cows", len(actor_id_to_cow_map))

        async for msg in connection.incoming():
            actor_id = msg["actor"]

            cow = actor_id_to_cow_map.get(actor_id)
            if cow:
                await cow.internals.handlers.handle(
                    msg, "incoming", connection, actor_id, cow=cow
                )

        logger.warning("Process incoming ended")
