# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type
from arbi.types.api import (
    TagCreateResponse,
    TagDeleteResponse,
    TagUpdateResponse,
    TagGetDocsResponse,
    TagApplyToDocsResponse,
    TagRemoveFromDocsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTag:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Arbi) -> None:
        tag = client.api.tag.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(TagCreateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Arbi) -> None:
        tag = client.api.tag.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
            parent_ext_id="tag-bFXA5r3A",
            shared=True,
        )
        assert_matches_type(TagCreateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Arbi) -> None:
        response = client.api.tag.with_raw_response.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = response.parse()
        assert_matches_type(TagCreateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Arbi) -> None:
        with client.api.tag.with_streaming_response.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = response.parse()
            assert_matches_type(TagCreateResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Arbi) -> None:
        tag = client.api.tag.update(
            tag_ext_id="tag",
        )
        assert_matches_type(TagUpdateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Arbi) -> None:
        tag = client.api.tag.update(
            tag_ext_id="tag",
            name="name",
            shared=True,
        )
        assert_matches_type(TagUpdateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Arbi) -> None:
        response = client.api.tag.with_raw_response.update(
            tag_ext_id="tag",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = response.parse()
        assert_matches_type(TagUpdateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Arbi) -> None:
        with client.api.tag.with_streaming_response.update(
            tag_ext_id="tag",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = response.parse()
            assert_matches_type(TagUpdateResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            client.api.tag.with_raw_response.update(
                tag_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Arbi) -> None:
        tag = client.api.tag.delete(
            "tag",
        )
        assert_matches_type(TagDeleteResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Arbi) -> None:
        response = client.api.tag.with_raw_response.delete(
            "tag",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = response.parse()
        assert_matches_type(TagDeleteResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Arbi) -> None:
        with client.api.tag.with_streaming_response.delete(
            "tag",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = response.parse()
            assert_matches_type(TagDeleteResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            client.api.tag.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_apply_to_docs(self, client: Arbi) -> None:
        tag = client.api.tag.apply_to_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )
        assert_matches_type(TagApplyToDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_apply_to_docs(self, client: Arbi) -> None:
        response = client.api.tag.with_raw_response.apply_to_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = response.parse()
        assert_matches_type(TagApplyToDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_apply_to_docs(self, client: Arbi) -> None:
        with client.api.tag.with_streaming_response.apply_to_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = response.parse()
            assert_matches_type(TagApplyToDocsResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_apply_to_docs(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            client.api.tag.with_raw_response.apply_to_docs(
                tag_ext_id="",
                doc_ids=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_docs(self, client: Arbi) -> None:
        tag = client.api.tag.get_docs(
            "tag",
        )
        assert_matches_type(TagGetDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_docs(self, client: Arbi) -> None:
        response = client.api.tag.with_raw_response.get_docs(
            "tag",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = response.parse()
        assert_matches_type(TagGetDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_docs(self, client: Arbi) -> None:
        with client.api.tag.with_streaming_response.get_docs(
            "tag",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = response.parse()
            assert_matches_type(TagGetDocsResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_docs(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            client.api.tag.with_raw_response.get_docs(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_remove_from_docs(self, client: Arbi) -> None:
        tag = client.api.tag.remove_from_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )
        assert_matches_type(TagRemoveFromDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_remove_from_docs(self, client: Arbi) -> None:
        response = client.api.tag.with_raw_response.remove_from_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = response.parse()
        assert_matches_type(TagRemoveFromDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_remove_from_docs(self, client: Arbi) -> None:
        with client.api.tag.with_streaming_response.remove_from_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = response.parse()
            assert_matches_type(TagRemoveFromDocsResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_remove_from_docs(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            client.api.tag.with_raw_response.remove_from_docs(
                tag_ext_id="",
                doc_ids=["string"],
            )


class TestAsyncTag:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(TagCreateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
            parent_ext_id="tag-bFXA5r3A",
            shared=True,
        )
        assert_matches_type(TagCreateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.tag.with_raw_response.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = await response.parse()
        assert_matches_type(TagCreateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncArbi) -> None:
        async with async_client.api.tag.with_streaming_response.create(
            name="name",
            workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = await response.parse()
            assert_matches_type(TagCreateResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.update(
            tag_ext_id="tag",
        )
        assert_matches_type(TagUpdateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.update(
            tag_ext_id="tag",
            name="name",
            shared=True,
        )
        assert_matches_type(TagUpdateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.tag.with_raw_response.update(
            tag_ext_id="tag",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = await response.parse()
        assert_matches_type(TagUpdateResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncArbi) -> None:
        async with async_client.api.tag.with_streaming_response.update(
            tag_ext_id="tag",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = await response.parse()
            assert_matches_type(TagUpdateResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            await async_client.api.tag.with_raw_response.update(
                tag_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.delete(
            "tag",
        )
        assert_matches_type(TagDeleteResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.tag.with_raw_response.delete(
            "tag",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = await response.parse()
        assert_matches_type(TagDeleteResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncArbi) -> None:
        async with async_client.api.tag.with_streaming_response.delete(
            "tag",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = await response.parse()
            assert_matches_type(TagDeleteResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            await async_client.api.tag.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_apply_to_docs(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.apply_to_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )
        assert_matches_type(TagApplyToDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_apply_to_docs(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.tag.with_raw_response.apply_to_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = await response.parse()
        assert_matches_type(TagApplyToDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_apply_to_docs(self, async_client: AsyncArbi) -> None:
        async with async_client.api.tag.with_streaming_response.apply_to_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = await response.parse()
            assert_matches_type(TagApplyToDocsResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_apply_to_docs(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            await async_client.api.tag.with_raw_response.apply_to_docs(
                tag_ext_id="",
                doc_ids=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_docs(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.get_docs(
            "tag",
        )
        assert_matches_type(TagGetDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_docs(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.tag.with_raw_response.get_docs(
            "tag",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = await response.parse()
        assert_matches_type(TagGetDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_docs(self, async_client: AsyncArbi) -> None:
        async with async_client.api.tag.with_streaming_response.get_docs(
            "tag",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = await response.parse()
            assert_matches_type(TagGetDocsResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_docs(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            await async_client.api.tag.with_raw_response.get_docs(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_remove_from_docs(self, async_client: AsyncArbi) -> None:
        tag = await async_client.api.tag.remove_from_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )
        assert_matches_type(TagRemoveFromDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_remove_from_docs(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.tag.with_raw_response.remove_from_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tag = await response.parse()
        assert_matches_type(TagRemoveFromDocsResponse, tag, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_remove_from_docs(self, async_client: AsyncArbi) -> None:
        async with async_client.api.tag.with_streaming_response.remove_from_docs(
            tag_ext_id="tag",
            doc_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tag = await response.parse()
            assert_matches_type(TagRemoveFromDocsResponse, tag, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_remove_from_docs(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tag_ext_id` but received ''"):
            await async_client.api.tag.with_raw_response.remove_from_docs(
                tag_ext_id="",
                doc_ids=["string"],
            )
