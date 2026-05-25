import httpx
import pytest

from addictune_sdk.api.assets import AssetsAPI
from addictune_sdk.exceptions import AddictuneNotFoundError
from tests.conftest import make_response


@pytest.mark.asyncio
async def test_get_bytes_returns_asset_content(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, text="image-data")

    result = await AssetsAPI(mock_client).get_bytes("https://cdn.example/image.png")

    assert result == b"image-data"
    mock_client.get.assert_called_once_with("https://cdn.example/image.png")


@pytest.mark.asyncio
async def test_get_bytes_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(404, text="Not Found")

    with pytest.raises(AddictuneNotFoundError):
        await AssetsAPI(mock_client).get_bytes("https://cdn.example/missing.png")

