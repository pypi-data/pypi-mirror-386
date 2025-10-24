import pytest

from cattle_grid.testing.fixtures import *  # noqa

from .account import AccountManager


async def test_creation_not_found(sql_session):
    with pytest.raises(ValueError):
        await AccountManager.for_name_and_password(sql_session, "not", "found")


async def test_creation(sql_session, account_for_test):
    account_manager = await AccountManager.for_name_and_password(
        sql_session, account_for_test.name, account_for_test.name
    )
    assert account_manager.account == account_for_test


async def test_creation_for_name(sql_session, account_for_test):
    account_manager = await AccountManager.for_name(sql_session, account_for_test.name)
    assert account_manager.account == account_for_test
