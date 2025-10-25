# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from letta_client import Letta, AsyncLetta
from letta_client.pagination import SyncArrayPage, AsyncArrayPage
from letta_client.types.agents import LettaResponse, LettaMessageUnion
from letta_client.types.groups import (
    MessageModifyResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMessages:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Letta) -> None:
        message = client.groups.messages.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
        )
        assert_matches_type(SyncArrayPage[LettaMessageUnion], message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Letta) -> None:
        message = client.groups.messages.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            after="after",
            assistant_message_tool_kwarg="assistant_message_tool_kwarg",
            assistant_message_tool_name="assistant_message_tool_name",
            before="before",
            limit=0,
            order="asc",
            order_by="created_at",
            use_assistant_message=True,
        )
        assert_matches_type(SyncArrayPage[LettaMessageUnion], message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(SyncArrayPage[LettaMessageUnion], message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(SyncArrayPage[LettaMessageUnion], message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.list(
                group_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_overload_1(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_with_all_params_overload_1(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
            message_type="system_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_modify_overload_1(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_modify_overload_1(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_modify_overload_1(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                content="content",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                content="content",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_overload_2(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "type": "text",
                }
            ],
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_with_all_params_overload_2(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "signature": "signature",
                    "type": "text",
                }
            ],
            message_type="user_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_modify_overload_2(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "type": "text",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_modify_overload_2(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "type": "text",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_modify_overload_2(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                content=[
                    {
                        "text": "text",
                        "type": "text",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                content=[
                    {
                        "text": "text",
                        "type": "text",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_overload_3(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_with_all_params_overload_3(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
            message_type="reasoning_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_modify_overload_3(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_modify_overload_3(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_modify_overload_3(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                reasoning="reasoning",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                reasoning="reasoning",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_overload_4(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[{"text": "text"}],
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_with_all_params_overload_4(self, client: Letta) -> None:
        message = client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "signature": "signature",
                    "type": "text",
                }
            ],
            message_type="assistant_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_modify_overload_4(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[{"text": "text"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_modify_overload_4(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[{"text": "text"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_modify_overload_4(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                content=[{"text": "text"}],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                content=[{"text": "text"}],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_reset(self, client: Letta) -> None:
        message = client.groups.messages.reset(
            "group-123e4567-e89b-42d3-8456-426614174000",
        )
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_reset(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.reset(
            "group-123e4567-e89b-42d3-8456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_reset(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.reset(
            "group-123e4567-e89b-42d3-8456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(object, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_reset(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.reset(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_send(self, client: Letta) -> None:
        message = client.groups.messages.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )
        assert_matches_type(LettaResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_send_with_all_params(self, client: Letta) -> None:
        message = client.groups.messages.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "signature": "signature",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                    "batch_item_id": "batch_item_id",
                    "group_id": "group_id",
                    "name": "name",
                    "otid": "otid",
                    "sender_id": "sender_id",
                    "type": "message",
                }
            ],
            assistant_message_tool_kwarg="assistant_message_tool_kwarg",
            assistant_message_tool_name="assistant_message_tool_name",
            enable_thinking="enable_thinking",
            include_return_message_types=["system_message"],
            max_steps=0,
            use_assistant_message=True,
        )
        assert_matches_type(LettaResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_send(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(LettaResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_send(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(LettaResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_send(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.send(
                group_id="",
                messages=[
                    {
                        "content": [
                            {
                                "text": "text",
                                "type": "text",
                            }
                        ],
                        "role": "user",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stream(self, client: Letta) -> None:
        message = client.groups.messages.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stream_with_all_params(self, client: Letta) -> None:
        message = client.groups.messages.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "signature": "signature",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                    "batch_item_id": "batch_item_id",
                    "group_id": "group_id",
                    "name": "name",
                    "otid": "otid",
                    "sender_id": "sender_id",
                    "type": "message",
                }
            ],
            assistant_message_tool_kwarg="assistant_message_tool_kwarg",
            assistant_message_tool_name="assistant_message_tool_name",
            background=True,
            enable_thinking="enable_thinking",
            include_pings=True,
            include_return_message_types=["system_message"],
            max_steps=0,
            stream_tokens=True,
            use_assistant_message=True,
        )
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_stream(self, client: Letta) -> None:
        response = client.groups.messages.with_raw_response.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = response.parse()
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_stream(self, client: Letta) -> None:
        with client.groups.messages.with_streaming_response.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = response.parse()
            assert_matches_type(object, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_stream(self, client: Letta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            client.groups.messages.with_raw_response.stream(
                group_id="",
                messages=[
                    {
                        "content": [
                            {
                                "text": "text",
                                "type": "text",
                            }
                        ],
                        "role": "user",
                    }
                ],
            )


class TestAsyncMessages:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
        )
        assert_matches_type(AsyncArrayPage[LettaMessageUnion], message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            after="after",
            assistant_message_tool_kwarg="assistant_message_tool_kwarg",
            assistant_message_tool_name="assistant_message_tool_name",
            before="before",
            limit=0,
            order="asc",
            order_by="created_at",
            use_assistant_message=True,
        )
        assert_matches_type(AsyncArrayPage[LettaMessageUnion], message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(AsyncArrayPage[LettaMessageUnion], message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.list(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(AsyncArrayPage[LettaMessageUnion], message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.list(
                group_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_overload_1(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_with_all_params_overload_1(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
            message_type="system_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_modify_overload_1(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_modify_overload_1(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content="content",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_modify_overload_1(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                content="content",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                content="content",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_overload_2(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "type": "text",
                }
            ],
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_with_all_params_overload_2(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "signature": "signature",
                    "type": "text",
                }
            ],
            message_type="user_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_modify_overload_2(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "type": "text",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_modify_overload_2(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "type": "text",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_modify_overload_2(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                content=[
                    {
                        "text": "text",
                        "type": "text",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                content=[
                    {
                        "text": "text",
                        "type": "text",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_overload_3(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_with_all_params_overload_3(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
            message_type="reasoning_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_modify_overload_3(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_modify_overload_3(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            reasoning="reasoning",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_modify_overload_3(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                reasoning="reasoning",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                reasoning="reasoning",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_overload_4(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[{"text": "text"}],
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_with_all_params_overload_4(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[
                {
                    "text": "text",
                    "signature": "signature",
                    "type": "text",
                }
            ],
            message_type="assistant_message",
        )
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_modify_overload_4(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[{"text": "text"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(MessageModifyResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_modify_overload_4(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.modify(
            message_id="message-123e4567-e89b-42d3-8456-426614174000",
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            content=[{"text": "text"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(MessageModifyResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_modify_overload_4(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="message-123e4567-e89b-42d3-8456-426614174000",
                group_id="",
                content=[{"text": "text"}],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_id` but received ''"):
            await async_client.groups.messages.with_raw_response.modify(
                message_id="",
                group_id="group-123e4567-e89b-42d3-8456-426614174000",
                content=[{"text": "text"}],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_reset(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.reset(
            "group-123e4567-e89b-42d3-8456-426614174000",
        )
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_reset(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.reset(
            "group-123e4567-e89b-42d3-8456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_reset(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.reset(
            "group-123e4567-e89b-42d3-8456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(object, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_reset(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.reset(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_send(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )
        assert_matches_type(LettaResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_send_with_all_params(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "signature": "signature",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                    "batch_item_id": "batch_item_id",
                    "group_id": "group_id",
                    "name": "name",
                    "otid": "otid",
                    "sender_id": "sender_id",
                    "type": "message",
                }
            ],
            assistant_message_tool_kwarg="assistant_message_tool_kwarg",
            assistant_message_tool_name="assistant_message_tool_name",
            enable_thinking="enable_thinking",
            include_return_message_types=["system_message"],
            max_steps=0,
            use_assistant_message=True,
        )
        assert_matches_type(LettaResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_send(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(LettaResponse, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_send(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.send(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(LettaResponse, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_send(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.send(
                group_id="",
                messages=[
                    {
                        "content": [
                            {
                                "text": "text",
                                "type": "text",
                            }
                        ],
                        "role": "user",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stream(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stream_with_all_params(self, async_client: AsyncLetta) -> None:
        message = await async_client.groups.messages.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "signature": "signature",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                    "batch_item_id": "batch_item_id",
                    "group_id": "group_id",
                    "name": "name",
                    "otid": "otid",
                    "sender_id": "sender_id",
                    "type": "message",
                }
            ],
            assistant_message_tool_kwarg="assistant_message_tool_kwarg",
            assistant_message_tool_name="assistant_message_tool_name",
            background=True,
            enable_thinking="enable_thinking",
            include_pings=True,
            include_return_message_types=["system_message"],
            max_steps=0,
            stream_tokens=True,
            use_assistant_message=True,
        )
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_stream(self, async_client: AsyncLetta) -> None:
        response = await async_client.groups.messages.with_raw_response.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        message = await response.parse()
        assert_matches_type(object, message, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_stream(self, async_client: AsyncLetta) -> None:
        async with async_client.groups.messages.with_streaming_response.stream(
            group_id="group-123e4567-e89b-42d3-8456-426614174000",
            messages=[
                {
                    "content": [
                        {
                            "text": "text",
                            "type": "text",
                        }
                    ],
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            message = await response.parse()
            assert_matches_type(object, message, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_stream(self, async_client: AsyncLetta) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `group_id` but received ''"):
            await async_client.groups.messages.with_raw_response.stream(
                group_id="",
                messages=[
                    {
                        "content": [
                            {
                                "text": "text",
                                "type": "text",
                            }
                        ],
                        "role": "user",
                    }
                ],
            )
