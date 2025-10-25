"""Unit tests for SequenceApiClient."""

import pytest
from py_get_sequence_api_client.client import (
    SequenceApiClient,
    SequenceApiError,
    SequenceAuthError,
)


class DummyResponse:
    """A dummy aiohttp response for testing SequenceApiClient."""

    def __init__(self, status, json_data):
        """Initialize with status and JSON data."""
        self.status = status
        self._json_data = json_data

    async def json(self):
        """Return the dummy JSON data."""
        return self._json_data

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context manager."""


class DummySession:
    """A dummy aiohttp session for testing SequenceApiClient."""

    def __init__(self, response):
        """Initialize with a dummy response."""
        self._response = response

    def post(self, url, headers=None, json=None):
        """Return the dummy response for POST requests."""
        return self._response


@pytest.mark.asyncio
async def test_async_get_accounts_success():
    """Test successful retrieval of accounts."""
    accounts_data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Pod",
                    "balance": {"amountInDollars": 100, "error": None},
                }
            ]
        }
    }
    dummy_response = DummyResponse(200, accounts_data)
    session = DummySession(dummy_response)
    client = SequenceApiClient(session, "test-token")
    result = await client.async_get_accounts()
    assert result == accounts_data


@pytest.mark.asyncio
async def test_async_get_accounts_auth_error():
    """Test authentication error handling."""
    dummy_response = DummyResponse(401, {})
    session = DummySession(dummy_response)
    client = SequenceApiClient(session, "bad-token")
    with pytest.raises(SequenceAuthError):
        await client.async_get_accounts()


@pytest.mark.asyncio
async def test_async_get_accounts_api_error():
    """Test API error handling for non-200 responses."""
    dummy_response = DummyResponse(500, {})
    session = DummySession(dummy_response)
    client = SequenceApiClient(session, "test-token")
    with pytest.raises(SequenceApiError):
        await client.async_get_accounts()


@pytest.mark.asyncio
async def test_async_test_connection_success():
    """Test connection success for SequenceApiClient."""
    accounts_data = {"data": {"accounts": []}}
    dummy_response = DummyResponse(200, accounts_data)
    session = DummySession(dummy_response)
    client = SequenceApiClient(session, "test-token")
    assert await client.async_test_connection() is True


@pytest.mark.asyncio
async def test_async_test_connection_failure():
    """Test connection failure for SequenceApiClient."""
    dummy_response = DummyResponse(401, {})
    session = DummySession(dummy_response)
    client = SequenceApiClient(session, "bad-token")
    assert await client.async_test_connection() is False


# Add more tests for balance and account helpers


def test_get_pod_accounts():
    """Test filtering Pod accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Pod",
                    "balance": {"amountInDollars": 100, "error": None},
                },
                {
                    "id": "2",
                    "type": "Income Source",
                    "balance": {"amountInDollars": 50, "error": None},
                },
            ]
        }
    }
    pods = client.get_pod_accounts(data)
    assert len(pods) == 1
    assert pods[0]["type"] == "Pod"


def test_get_total_balance():
    """Test total balance calculation across all accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Pod",
                    "balance": {"amountInDollars": 100, "error": None},
                },
                {
                    "id": "2",
                    "type": "Income Source",
                    "balance": {"amountInDollars": 50, "error": None},
                },
                {
                    "id": "3",
                    "type": "Pod",
                    "balance": {"amountInDollars": None, "error": "err"},
                },
            ]
        }
    }
    total = client.get_total_balance(data)
    assert total == 150


def test_get_income_source_accounts():
    """Test filtering Income Source accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Pod",
                    "balance": {"amountInDollars": 100, "error": None},
                },
                {
                    "id": "2",
                    "type": "Income Source",
                    "balance": {"amountInDollars": 50, "error": None},
                },
            ]
        }
    }
    sources = client.get_income_source_accounts(data)
    assert len(sources) == 1
    assert sources[0]["type"] == "Income Source"


def test_get_pod_balance():
    """Test total balance calculation for Pod accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Pod",
                    "balance": {"amountInDollars": 100, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "balance": {"amountInDollars": 50, "error": None},
                },
                {
                    "id": "3",
                    "type": "Pod",
                    "balance": {"amountInDollars": None, "error": "err"},
                },
            ]
        }
    }
    total = client.get_pod_balance(data)
    assert total == 150


def test_get_liability_accounts_type():
    """Test filtering Liability accounts by type."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Liability",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    liabilities = client.get_liability_accounts(data)
    assert len(liabilities) == 1
    assert liabilities[0]["type"] == "Liability"


def test_get_liability_accounts_ids():
    """Test filtering Liability accounts by configured IDs."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Account",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    liabilities = client.get_liability_accounts(data, ["1"])
    assert len(liabilities) == 1
    assert liabilities[0]["id"] == "1"


def test_get_investment_accounts_type():
    """Test filtering Investment accounts by type."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Investment",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    investments = client.get_investment_accounts(data)
    assert len(investments) == 1
    assert investments[0]["type"] == "Investment"


def test_get_investment_accounts_ids():
    """Test filtering Investment accounts by configured IDs."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Account",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    investments = client.get_investment_accounts(data, ["1"])
    assert len(investments) == 1
    assert investments[0]["id"] == "1"


def test_get_external_accounts():
    """Test filtering External accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Account",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "balance": {"amountInDollars": 20, "error": None},
                },
                {
                    "id": "3",
                    "type": "Income Source",
                    "balance": {"amountInDollars": 30, "error": None},
                },
                {
                    "id": "4",
                    "type": "Liability",
                    "balance": {"amountInDollars": 40, "error": None},
                },
                {
                    "id": "5",
                    "type": "Investment",
                    "balance": {"amountInDollars": 50, "error": None},
                },
            ]
        }
    }
    externals = client.get_external_accounts(data)
    assert len(externals) == 1
    assert externals[0]["type"] == "Account"


def test_get_balance_by_type():
    """Test total balance for a specific account type."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Pod",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "balance": {"amountInDollars": 20, "error": None},
                },
                {
                    "id": "3",
                    "type": "Income Source",
                    "balance": {"amountInDollars": 30, "error": None},
                },
            ]
        }
    }
    total = client.get_balance_by_type(data, "Pod")
    assert total == 30


def test_get_account_types_summary():
    """Test summary of all account types and their totals."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Pod",
                    "name": "Pod1",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Pod",
                    "name": "Pod2",
                    "balance": {"amountInDollars": 20, "error": None},
                },
                {
                    "id": "3",
                    "type": "Income Source",
                    "name": "Inc1",
                    "balance": {"amountInDollars": 30, "error": None},
                },
            ]
        }
    }
    summary = client.get_account_types_summary(data)
    assert summary["Pod"]["count"] == 2
    assert summary["Pod"]["total_balance"] == 30
    assert summary["Income Source"]["count"] == 1
    assert summary["Income Source"]["total_balance"] == 30


def test_get_configured_liability_balance():
    """Test total balance for configured liability accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Liability",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Account",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    total = client.get_configured_liability_balance(data, ["2"])
    assert total == 30


def test_get_configured_investment_balance():
    """Test total balance for configured investment accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Investment",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Account",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    total = client.get_configured_investment_balance(data, ["2"])
    assert total == 30


def test_get_uncategorized_external_accounts():
    """Test uncategorized external accounts filtering."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Account",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Account",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    uncategorized = client.get_uncategorized_external_accounts(data, ["1"], ["3"])
    assert len(uncategorized) == 1
    assert uncategorized[0]["id"] == "2"


def test_get_uncategorized_external_balance():
    """Test total balance for uncategorized external accounts."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Account",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Account",
                    "balance": {"amountInDollars": 20, "error": None},
                },
            ]
        }
    }
    total = client.get_uncategorized_external_balance(data, ["1"], ["3"])
    assert total == 20


def test_get_adjusted_total_balance_none():
    """Test adjusted total balance returns None if liabilities not configured."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Account",
                    "balance": {"amountInDollars": 10, "error": None},
                },
            ]
        }
    }
    result = client.get_adjusted_total_balance(data, None, False)
    assert result is None


def test_get_adjusted_total_balance_with_liabilities():
    """Test adjusted total balance with liabilities configured."""
    client = SequenceApiClient(None, "token")
    data = {
        "data": {
            "accounts": [
                {
                    "id": "1",
                    "type": "Account",
                    "balance": {"amountInDollars": 10, "error": None},
                },
                {
                    "id": "2",
                    "type": "Account",
                    "balance": {"amountInDollars": 5, "error": None},
                },
            ]
        }
    }
    # Mark id "2" as liability, so its balance is negative
    result = client.get_adjusted_total_balance(data, ["2"], True)
    assert result == 5
