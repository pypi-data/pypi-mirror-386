from sqlalchemy.ext.asyncio import AsyncSession

from cattle_grid.model.account import (
    NameAndVersion,
    InformationResponse,
)
from cattle_grid.model.extension import MethodInformationModel
from cattle_grid.version import __version__

from cattle_grid.database.account import Account
from cattle_grid.manage import AccountManager


def cattle_drive_version():
    """
    Gives the current cattle drive version

    ```python
    >>> print(cattle_drive_version().model_dump_json(indent=2))
    {
      "name": "CattleDrive",
      "version": "0.1.1"
    }

    ```
    """
    return NameAndVersion(name="CattleDrive", version="0.1.1")


def protocol_and_backend() -> dict[str, NameAndVersion]:
    protocol = cattle_drive_version()
    backend = NameAndVersion(name="cattle_grid", version=__version__)

    return dict(protocol=protocol, backend=backend)


async def create_information_response(
    session: AsyncSession,
    account: Account,
    method_information: list[MethodInformationModel],
) -> InformationResponse:
    manager = AccountManager(account=account, session=session)

    base_urls = await manager.allowed_base_urls()

    await session.refresh(account, attribute_names=["actors"])

    return InformationResponse(
        account_name=account.name,
        base_urls=base_urls,
        actors=manager.account_information(),
        **protocol_and_backend(),
        method_information=method_information,
    )
