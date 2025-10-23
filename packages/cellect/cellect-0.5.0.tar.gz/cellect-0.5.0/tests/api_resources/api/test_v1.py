# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from cellect import Cellect, AsyncCellect
from tests.utils import assert_matches_type
from cellect.types.api import V1ListProjectsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestV1:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_projects(self, client: Cellect) -> None:
        v1 = client.api.v1.list_projects()
        assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_projects_with_all_params(self, client: Cellect) -> None:
        v1 = client.api.v1.list_projects(
            user_email="user_email",
        )
        assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_projects(self, client: Cellect) -> None:
        response = client.api.v1.with_raw_response.list_projects()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        v1 = response.parse()
        assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_projects(self, client: Cellect) -> None:
        with client.api.v1.with_streaming_response.list_projects() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            v1 = response.parse()
            assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file(self, client: Cellect) -> None:
        v1 = client.api.v1.upload_file(
            file=b"raw file contents",
            project_id="project_id",
        )
        assert_matches_type(object, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file_with_all_params(self, client: Cellect) -> None:
        v1 = client.api.v1.upload_file(
            file=b"raw file contents",
            project_id="project_id",
            crack=True,
        )
        assert_matches_type(object, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload_file(self, client: Cellect) -> None:
        response = client.api.v1.with_raw_response.upload_file(
            file=b"raw file contents",
            project_id="project_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        v1 = response.parse()
        assert_matches_type(object, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload_file(self, client: Cellect) -> None:
        with client.api.v1.with_streaming_response.upload_file(
            file=b"raw file contents",
            project_id="project_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            v1 = response.parse()
            assert_matches_type(object, v1, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncV1:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_projects(self, async_client: AsyncCellect) -> None:
        v1 = await async_client.api.v1.list_projects()
        assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_projects_with_all_params(self, async_client: AsyncCellect) -> None:
        v1 = await async_client.api.v1.list_projects(
            user_email="user_email",
        )
        assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_projects(self, async_client: AsyncCellect) -> None:
        response = await async_client.api.v1.with_raw_response.list_projects()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        v1 = await response.parse()
        assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_projects(self, async_client: AsyncCellect) -> None:
        async with async_client.api.v1.with_streaming_response.list_projects() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            v1 = await response.parse()
            assert_matches_type(V1ListProjectsResponse, v1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file(self, async_client: AsyncCellect) -> None:
        v1 = await async_client.api.v1.upload_file(
            file=b"raw file contents",
            project_id="project_id",
        )
        assert_matches_type(object, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file_with_all_params(self, async_client: AsyncCellect) -> None:
        v1 = await async_client.api.v1.upload_file(
            file=b"raw file contents",
            project_id="project_id",
            crack=True,
        )
        assert_matches_type(object, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload_file(self, async_client: AsyncCellect) -> None:
        response = await async_client.api.v1.with_raw_response.upload_file(
            file=b"raw file contents",
            project_id="project_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        v1 = await response.parse()
        assert_matches_type(object, v1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload_file(self, async_client: AsyncCellect) -> None:
        async with async_client.api.v1.with_streaming_response.upload_file(
            file=b"raw file contents",
            project_id="project_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            v1 = await response.parse()
            assert_matches_type(object, v1, path=["response"])

        assert cast(Any, response.is_closed) is True
