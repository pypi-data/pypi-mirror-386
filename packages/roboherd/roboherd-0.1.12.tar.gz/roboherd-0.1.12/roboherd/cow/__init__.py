import logging

from typing import Any, Callable, List

from dataclasses import dataclass, field
from fast_depends import inject

from cron_descriptor import get_description
from almabtrieb import Almabtrieb

from .types import Information
from .handlers import Handlers, HandlerConfiguration
from .profile import determine_profile_update

logger = logging.getLogger(__name__)


@dataclass
class CronEntry:
    """A cron entry"""

    crontab: str = field(metadata=dict(description="""The cron expression"""))

    func: Callable = field(metadata=dict(description="""The function to be called"""))


@dataclass
class RoboCowInternals:
    """Internal data for the cow"""

    profile: dict[str, Any] | None = field(
        default=None,
        metadata=dict(
            description="""The profile of the cow, aka as the actor object in ActivityPub"""
        ),
    )

    actor_id: str | None = field(
        default=None,
        metadata=dict(description="""Actor Id of the cow; loaded automatically"""),
    )

    handlers: Handlers = field(
        default_factory=Handlers,
        metadata=dict(
            description="""Handlers for incoming and outgoing messages, added through annotations"""
        ),
    )
    handler_configuration: List[HandlerConfiguration] = field(
        default_factory=list,
        metadata=dict(
            description="""Handler configurations, added through annotations"""
        ),
    )

    cron_entries: List[CronEntry] = field(
        default_factory=list,
        metadata=dict(description="""Cron entries, created through annotations"""),
    )

    startup_routine: Callable | None = None

    base_url: str | None = field(default=None)


@dataclass
class RoboCow:
    information: Information = field(
        metadata=dict(description="Information about the cow")
    )

    auto_follow: bool = field(
        default=True,
        metadata=dict(
            description="""Whether to automatically accept follow requests"""
        ),
    )

    skip_profile_update: bool = field(
        default=False,
        metadata=dict(
            description="When set to True the profile is not updated automatically. Useful when managing a cow from multiple scripts."
        ),
    )

    internals: RoboCowInternals = field(
        default_factory=RoboCowInternals,
        metadata=dict(description="Internal data for the cow"),
    )

    @staticmethod
    def create(**kwargs):
        """Creates a new cow, by creating a new [Information][roboherd.cow.types.Information].

        ```python
        >>> RoboCow.create(name="my cow")
        RoboCow(information=Information(type='Service', handle=None, name='my cow', ...

        ```

        The parameter `description_md` is transformed from markdown to html and then
        assigned to `description`.

        ```python
        >> cow = RoboCow.create(description_md="__bold__")
        >> cow.information.description
        '<p><strong>bold</strong></p>'

        ```
        """

        if "description_md" in kwargs:
            import markdown

            kwargs["description"] = markdown.markdown(kwargs["description_md"])
            del kwargs["description_md"]

        information = Information.model_validate(kwargs)
        return RoboCow(information=information)

    def action(self, action: str = "*", activity_type: str = "*"):
        """Adds a handler for an event. Use "*" as a wildcard.

        Usage:

        ```python
        cow = Robocow(information=Information(handle="example"))

        @cow.action(action="outgoing", activity_type="Follow")
        async def handle_outgoing_follow(data):
            ...
        ```
        """

        config = HandlerConfiguration(
            action=action,
            activity_type=activity_type,
        )

        def inner(func):
            config.func = func
            self.internals.handlers.add_handler(config, func)
            self.internals.handler_configuration.append(config)
            return func

        return inner

    def cron(self, crontab):
        def inner(func):
            self.internals.cron_entries.append(CronEntry(crontab, func))

            return func

        return inner

    def incoming(self, func):
        """Adds a handler for an incoming message. Usage:

        ```python
        cow = Robocow("example")

        @cow.incoming
        async def handle_incoming(data):
            ...
        ```
        """
        config = HandlerConfiguration(
            action="incoming",
            activity_type="*",
        )
        self.internals.handlers.add_handler(config, func)
        return func

    def incoming_create(self, func):
        """Adds a handler for an incoming activity if the
        activity is of type_create

        ```python
        cow = Robocow("example")

        @cow.incoming_create
        async def handle_incoming(data):
            ...
        ```
        """
        config = HandlerConfiguration(
            action="incoming", activity_type="Create", func=func
        )
        self.internals.handler_configuration.append(config)
        self.internals.handlers.add_handler(config, func)
        return func

    def startup(self, func):
        """Adds a startup routine to be run when the cow is started."""

        self.internals.startup_routine = func

    async def run_startup(self, connection: Almabtrieb):
        """Runs when the cow is birthed"""

        if self.internals.profile is None:
            if not self.internals.actor_id:
                raise ValueError("Actor ID is not set")
            result = await connection.fetch(
                self.internals.actor_id, self.internals.actor_id
            )
            if not result.data:
                raise ValueError("Could not retrieve profile")
            self.internals.profile = result.data

        if self.internals.cron_entries:
            frequency = ", ".join(
                get_description(entry.crontab) for entry in self.internals.cron_entries
            )
            self.information.frequency = frequency

        if not self.skip_profile_update:
            await self._run_profile_update(connection)

        if self.internals.startup_routine:
            await inject(self.internals.startup_routine)(
                cow=self,  # type:ignore
                connection=connection,  # type:ignore
                actor_id=self.internals.actor_id,  # type:ignore
            )  # type:ignore

    async def _run_profile_update(self, connection: Almabtrieb):
        if self.internals.profile is None:
            raise ValueError("Profile is not set")

        update = determine_profile_update(self.information, self.internals.profile)

        if update:
            logger.info("Updating profile for %s", self.information.handle)

            await connection.trigger("update_actor", update)
