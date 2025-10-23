# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from tests.utils import assert_matches_type
from payi.types.use_cases import UseCaseDefinition

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLimitConfig:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Payi) -> None:
        limit_config = client.use_cases.definitions.limit_config.create(
            use_case_name="use_case_name",
            max=0,
        )
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: Payi) -> None:
        limit_config = client.use_cases.definitions.limit_config.create(
            use_case_name="use_case_name",
            max=0,
            limit_type="block",
            properties={"foo": "string"},
            threshold=0,
        )
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: Payi) -> None:
        response = client.use_cases.definitions.limit_config.with_raw_response.create(
            use_case_name="use_case_name",
            max=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit_config = response.parse()
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: Payi) -> None:
        with client.use_cases.definitions.limit_config.with_streaming_response.create(
            use_case_name="use_case_name",
            max=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit_config = response.parse()
            assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.limit_config.with_raw_response.create(
                use_case_name="",
                max=0,
            )

    @parametrize
    def test_method_delete(self, client: Payi) -> None:
        limit_config = client.use_cases.definitions.limit_config.delete(
            "use_case_name",
        )
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: Payi) -> None:
        response = client.use_cases.definitions.limit_config.with_raw_response.delete(
            "use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit_config = response.parse()
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: Payi) -> None:
        with client.use_cases.definitions.limit_config.with_streaming_response.delete(
            "use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit_config = response.parse()
            assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.limit_config.with_raw_response.delete(
                "",
            )


class TestAsyncLimitConfig:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncPayi) -> None:
        limit_config = await async_client.use_cases.definitions.limit_config.create(
            use_case_name="use_case_name",
            max=0,
        )
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncPayi) -> None:
        limit_config = await async_client.use_cases.definitions.limit_config.create(
            use_case_name="use_case_name",
            max=0,
            limit_type="block",
            properties={"foo": "string"},
            threshold=0,
        )
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.limit_config.with_raw_response.create(
            use_case_name="use_case_name",
            max=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit_config = await response.parse()
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.limit_config.with_streaming_response.create(
            use_case_name="use_case_name",
            max=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit_config = await response.parse()
            assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.limit_config.with_raw_response.create(
                use_case_name="",
                max=0,
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncPayi) -> None:
        limit_config = await async_client.use_cases.definitions.limit_config.delete(
            "use_case_name",
        )
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.limit_config.with_raw_response.delete(
            "use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit_config = await response.parse()
        assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.limit_config.with_streaming_response.delete(
            "use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit_config = await response.parse()
            assert_matches_type(UseCaseDefinition, limit_config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.limit_config.with_raw_response.delete(
                "",
            )
