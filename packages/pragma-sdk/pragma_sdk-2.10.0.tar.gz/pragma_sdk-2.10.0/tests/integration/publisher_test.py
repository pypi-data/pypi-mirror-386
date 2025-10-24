import pytest
from dotenv import load_dotenv

from pragma_sdk.onchain.client import PragmaOnChainClient
from pragma_sdk.common.types.entry import FutureEntry, SpotEntry, GenericEntry
from pragma_sdk.common.fetchers.fetcher_client import FetcherClient
from pragma_sdk.common.fetchers.fetchers import (
    BinanceFetcher,
    BitstampFetcher,
    BybitFetcher,
    CoinbaseFetcher,
    DefillamaFetcher,
    GateioFetcher,
    GeckoTerminalFetcher,
    HuobiFetcher,
    KucoinFetcher,
    MEXCFetcher,
    OkxFetcher,
)
from pragma_sdk.common.fetchers.future_fetchers import (
    OkxFutureFetcher,
    BinanceFutureFetcher,
    ByBitFutureFetcher,
)
from pragma_sdk.common.fetchers.generic_fetchers.deribit.fetcher import (
    DeribitOptionsFetcher,
)
from tests.integration.constants import SAMPLE_PAIRS

ALL_SPOT_FETCHERS = [
    BinanceFetcher,
    BitstampFetcher,
    BybitFetcher,
    CoinbaseFetcher,
    DefillamaFetcher,
    GateioFetcher,
    GeckoTerminalFetcher,
    HuobiFetcher,
    KucoinFetcher,
    MEXCFetcher,
    OkxFetcher,
]
ALL_FUTURE_FETCHERS = [OkxFutureFetcher, ByBitFutureFetcher, BinanceFutureFetcher]
ALL_GENERIC_FETCHERS = [DeribitOptionsFetcher]

ALL_FETCHERS = ALL_SPOT_FETCHERS + ALL_FUTURE_FETCHERS + ALL_GENERIC_FETCHERS


load_dotenv()

PUBLISHER_NAME = "PRAGMA"


@pytest.mark.asyncio
async def test_publisher_client_all_assets(pragma_client: PragmaOnChainClient):
    fetcher = FetcherClient()
    fetcher.add_fetchers(
        [fetcher(SAMPLE_PAIRS, PUBLISHER_NAME) for fetcher in ALL_FETCHERS]
    )

    # Do not raise exceptions
    data = await fetcher.fetch(return_exceptions=True)

    # Assert that we don't have any exceptions in the response
    assert all(
        [
            isinstance(entry, SpotEntry)
            or isinstance(entry, FutureEntry)
            or isinstance(entry, GenericEntry)
            for entry in data
        ]
    )

    await pragma_client.publish_many(data)
