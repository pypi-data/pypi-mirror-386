from collections.abc import Callable
import asyncio
from ...interfaces.zammad import zammad
from ..BaseAction import BaseAction


class Zammad(BaseAction, zammad):
    """zammad.

    Generic Interface for managing Zammad instances.
    

        Example:

        ```yaml
        Zammad:
          Group: SyncZammad
          comment: Create User by Sync AD into Zammad
          method: create_user
          args:
            firstname: '{firstname}'
            lastname: '{lastname}'
            email: '{email}'
            login: '{login}'
            organization: T-ROC GLOBAL
            roles:
            - Customer
        ```

    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ) -> None:
        """Init Method."""
        BaseAction.__init__(self, loop=loop, job=job, stat=stat, **kwargs)
        zammad.__init__(self, **kwargs)
