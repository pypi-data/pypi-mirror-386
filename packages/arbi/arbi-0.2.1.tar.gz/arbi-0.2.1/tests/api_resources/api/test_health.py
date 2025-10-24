# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type
from arbi.types.api import (
    HealthCheckAppResponse,
    HealthGetModelsResponse,
    HealthCheckModelsResponse,
    HealthCheckServicesResponse,
    HealthRetrieveStatusResponse,
    HealthRetrieveVersionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestHealth:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_check_app(self, client: Arbi) -> None:
        health = client.api.health.check_app()
        assert_matches_type(HealthCheckAppResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_check_app(self, client: Arbi) -> None:
        response = client.api.health.with_raw_response.check_app()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(HealthCheckAppResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_check_app(self, client: Arbi) -> None:
        with client.api.health.with_streaming_response.check_app() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(HealthCheckAppResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_check_models(self, client: Arbi) -> None:
        health = client.api.health.check_models()
        assert_matches_type(HealthCheckModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_check_models(self, client: Arbi) -> None:
        response = client.api.health.with_raw_response.check_models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(HealthCheckModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_check_models(self, client: Arbi) -> None:
        with client.api.health.with_streaming_response.check_models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(HealthCheckModelsResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_check_services(self, client: Arbi) -> None:
        health = client.api.health.check_services()
        assert_matches_type(HealthCheckServicesResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_check_services(self, client: Arbi) -> None:
        response = client.api.health.with_raw_response.check_services()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(HealthCheckServicesResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_check_services(self, client: Arbi) -> None:
        with client.api.health.with_streaming_response.check_services() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(HealthCheckServicesResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_models(self, client: Arbi) -> None:
        health = client.api.health.get_models()
        assert_matches_type(HealthGetModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_models(self, client: Arbi) -> None:
        response = client.api.health.with_raw_response.get_models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(HealthGetModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_models(self, client: Arbi) -> None:
        with client.api.health.with_streaming_response.get_models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(HealthGetModelsResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_status(self, client: Arbi) -> None:
        health = client.api.health.retrieve_status()
        assert_matches_type(HealthRetrieveStatusResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_status(self, client: Arbi) -> None:
        response = client.api.health.with_raw_response.retrieve_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(HealthRetrieveStatusResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_status(self, client: Arbi) -> None:
        with client.api.health.with_streaming_response.retrieve_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(HealthRetrieveStatusResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_version(self, client: Arbi) -> None:
        health = client.api.health.retrieve_version()
        assert_matches_type(HealthRetrieveVersionResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_version(self, client: Arbi) -> None:
        response = client.api.health.with_raw_response.retrieve_version()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(HealthRetrieveVersionResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_version(self, client: Arbi) -> None:
        with client.api.health.with_streaming_response.retrieve_version() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(HealthRetrieveVersionResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncHealth:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_check_app(self, async_client: AsyncArbi) -> None:
        health = await async_client.api.health.check_app()
        assert_matches_type(HealthCheckAppResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_check_app(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.health.with_raw_response.check_app()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(HealthCheckAppResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_check_app(self, async_client: AsyncArbi) -> None:
        async with async_client.api.health.with_streaming_response.check_app() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(HealthCheckAppResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_check_models(self, async_client: AsyncArbi) -> None:
        health = await async_client.api.health.check_models()
        assert_matches_type(HealthCheckModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_check_models(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.health.with_raw_response.check_models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(HealthCheckModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_check_models(self, async_client: AsyncArbi) -> None:
        async with async_client.api.health.with_streaming_response.check_models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(HealthCheckModelsResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_check_services(self, async_client: AsyncArbi) -> None:
        health = await async_client.api.health.check_services()
        assert_matches_type(HealthCheckServicesResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_check_services(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.health.with_raw_response.check_services()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(HealthCheckServicesResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_check_services(self, async_client: AsyncArbi) -> None:
        async with async_client.api.health.with_streaming_response.check_services() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(HealthCheckServicesResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_models(self, async_client: AsyncArbi) -> None:
        health = await async_client.api.health.get_models()
        assert_matches_type(HealthGetModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_models(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.health.with_raw_response.get_models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(HealthGetModelsResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_models(self, async_client: AsyncArbi) -> None:
        async with async_client.api.health.with_streaming_response.get_models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(HealthGetModelsResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_status(self, async_client: AsyncArbi) -> None:
        health = await async_client.api.health.retrieve_status()
        assert_matches_type(HealthRetrieveStatusResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_status(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.health.with_raw_response.retrieve_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(HealthRetrieveStatusResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_status(self, async_client: AsyncArbi) -> None:
        async with async_client.api.health.with_streaming_response.retrieve_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(HealthRetrieveStatusResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_version(self, async_client: AsyncArbi) -> None:
        health = await async_client.api.health.retrieve_version()
        assert_matches_type(HealthRetrieveVersionResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_version(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.health.with_raw_response.retrieve_version()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(HealthRetrieveVersionResponse, health, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_version(self, async_client: AsyncArbi) -> None:
        async with async_client.api.health.with_streaming_response.retrieve_version() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(HealthRetrieveVersionResponse, health, path=["response"])

        assert cast(Any, response.is_closed) is True
