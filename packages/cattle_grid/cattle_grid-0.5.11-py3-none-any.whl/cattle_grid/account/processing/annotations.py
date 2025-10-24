from dataclasses import dataclass
from typing import Annotated

from fast_depends import Depends
from faststream import Context
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from cattle_grid.database.account import Account, ActorForAccount
from cattle_grid.database.activity_pub_actor import Actor
from cattle_grid.model.account import WithActor
from cattle_grid.dependencies import SqlSession, AccountExchangePublisher
from cattle_grid.dependencies.processing import RoutingKey
from cattle_grid.dependencies.account import AccountName


def method_from_routing_key(
    name: AccountName,
    routing_key: RoutingKey,
) -> str:
    """
    Extracts the method from the routing key

    ```pycon
    >>> method_from_routing_key("alice", "send.alice.trigger.method.first")
    'method.first'

    ```
    """
    start_string = f"send.{name}.trigger."
    if routing_key.startswith(start_string):
        return routing_key.removeprefix(start_string)
    else:
        raise ValueError("Invalid routing key for trigger")


MethodFromRoutingKey = Annotated[str, Depends(method_from_routing_key)]
"""Returns the method of a trigger message"""


async def account(name: AccountName, session: SqlSession) -> Account:
    account = await session.scalar(
        select(Account).where(Account.name == name).options(joinedload(Account.actors))
    )
    if account is None:
        raise ValueError("Account not found for name %s", name)

    return account


AccountFromRoutingKey = Annotated[Account, Depends(account)]
"""Returns the account from the routing key"""


async def actor_for_account_from_account(
    msg: WithActor, account: Annotated[Account, Depends(account)]
) -> ActorForAccount | None:
    for actor in account.actors:
        if actor.actor == msg.actor:
            return actor
    return None


ActorForAccountFromMessage = Annotated[
    ActorForAccount, Depends(actor_for_account_from_account)
]
"""The actor provided in the send message"""


async def actor_from_account(
    account: Account, actor_id: str, session: AsyncSession
) -> Actor | None:
    for actor in account.actors:
        if actor.actor == actor_id:
            return await session.scalar(select(Actor).where(Actor.actor_id == actor_id))
    return None


async def actor(
    msg: WithActor, session: SqlSession, account: Account = Depends(account)
):
    actor = await actor_from_account(account, msg.actor, session)
    if not actor:
        raise ValueError(
            f"Actor not found for account name {account.name} and actor id {msg.actor}"
        )
    return actor


ActorFromMessage = Annotated[Actor, Depends(actor)]
"""The actor provided in the send message"""


@dataclass
class ResponderClass:
    name: AccountName
    publisher: AccountExchangePublisher
    reply_to: str | None = Context("message.reply_to")

    async def respond(self, method: str, response):
        if self.reply_to:
            return response
        await self.publisher(
            response,
            routing_key=f"receive.{self.name}.response.{method}",
        )

    async def error(self):
        if self.reply_to:
            return {}
        await self.publisher(
            {"error": "Something went wrong"},
            routing_key=f"error.{self.name}",
        )


Responder = Annotated[ResponderClass, Depends(ResponderClass)]
