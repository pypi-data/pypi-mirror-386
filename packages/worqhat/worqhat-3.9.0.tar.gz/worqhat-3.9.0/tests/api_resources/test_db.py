# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from worqhat import Worqhat, AsyncWorqhat
from tests.utils import assert_matches_type
from worqhat.types import (
    DBExecuteBatchResponse,
    DBExecuteQueryResponse,
    DBInsertRecordResponse,
    DBDeleteRecordsResponse,
    DBUpdateRecordsResponse,
    DBProcessNlQueryResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDB:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_records(self, client: Worqhat) -> None:
        db = client.db.delete_records(
            table="users",
            where={"id": "bar"},
        )
        assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_records_with_all_params(self, client: Worqhat) -> None:
        db = client.db.delete_records(
            table="users",
            where={"id": "bar"},
            environment="production",
        )
        assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete_records(self, client: Worqhat) -> None:
        response = client.db.with_raw_response.delete_records(
            table="users",
            where={"id": "bar"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = response.parse()
        assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete_records(self, client: Worqhat) -> None:
        with client.db.with_streaming_response.delete_records(
            table="users",
            where={"id": "bar"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = response.parse()
            assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_batch(self, client: Worqhat) -> None:
        db = client.db.execute_batch(
            operations=[{"type": "insert"}, {"type": "update"}, {"type": "query"}],
        )
        assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_batch_with_all_params(self, client: Worqhat) -> None:
        db = client.db.execute_batch(
            operations=[
                {
                    "type": "insert",
                    "data": {
                        "name": "bar",
                        "email": "bar",
                    },
                    "query": "query",
                    "table": "users",
                    "where": {"foo": "bar"},
                },
                {
                    "type": "update",
                    "data": {"status": "bar"},
                    "query": "query",
                    "table": "users",
                    "where": {"email": "bar"},
                },
                {
                    "type": "query",
                    "data": {"foo": "bar"},
                    "query": "SELECT * FROM users WHERE status = 'active'",
                    "table": "table",
                    "where": {"foo": "bar"},
                },
            ],
            environment="development",
            transactional=True,
        )
        assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_batch(self, client: Worqhat) -> None:
        response = client.db.with_raw_response.execute_batch(
            operations=[{"type": "insert"}, {"type": "update"}, {"type": "query"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = response.parse()
        assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_batch(self, client: Worqhat) -> None:
        with client.db.with_streaming_response.execute_batch(
            operations=[{"type": "insert"}, {"type": "update"}, {"type": "query"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = response.parse()
            assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_query(self, client: Worqhat) -> None:
        db = client.db.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
        )
        assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_query_with_all_params(self, client: Worqhat) -> None:
        db = client.db.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
            environment="production",
            params={"slug": "bar"},
        )
        assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_query(self, client: Worqhat) -> None:
        response = client.db.with_raw_response.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = response.parse()
        assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_query(self, client: Worqhat) -> None:
        with client.db.with_streaming_response.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = response.parse()
            assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_insert_record(self, client: Worqhat) -> None:
        db = client.db.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
        )
        assert_matches_type(DBInsertRecordResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_insert_record_with_all_params(self, client: Worqhat) -> None:
        db = client.db.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
            environment="production",
        )
        assert_matches_type(DBInsertRecordResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_insert_record(self, client: Worqhat) -> None:
        response = client.db.with_raw_response.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = response.parse()
        assert_matches_type(DBInsertRecordResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_insert_record(self, client: Worqhat) -> None:
        with client.db.with_streaming_response.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = response.parse()
            assert_matches_type(DBInsertRecordResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_process_nl_query(self, client: Worqhat) -> None:
        db = client.db.process_nl_query(
            question="How many active users do we have?",
        )
        assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_process_nl_query_with_all_params(self, client: Worqhat) -> None:
        db = client.db.process_nl_query(
            question="How many active users do we have?",
            context={"foo": "bar"},
            environment="production",
        )
        assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_process_nl_query(self, client: Worqhat) -> None:
        response = client.db.with_raw_response.process_nl_query(
            question="How many active users do we have?",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = response.parse()
        assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_process_nl_query(self, client: Worqhat) -> None:
        with client.db.with_streaming_response.process_nl_query(
            question="How many active users do we have?",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = response.parse()
            assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_records(self, client: Worqhat) -> None:
        db = client.db.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
        )
        assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_records_with_all_params(self, client: Worqhat) -> None:
        db = client.db.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
            environment="production",
        )
        assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_records(self, client: Worqhat) -> None:
        response = client.db.with_raw_response.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = response.parse()
        assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_records(self, client: Worqhat) -> None:
        with client.db.with_streaming_response.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = response.parse()
            assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncDB:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_records(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.delete_records(
            table="users",
            where={"id": "bar"},
        )
        assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_records_with_all_params(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.delete_records(
            table="users",
            where={"id": "bar"},
            environment="production",
        )
        assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete_records(self, async_client: AsyncWorqhat) -> None:
        response = await async_client.db.with_raw_response.delete_records(
            table="users",
            where={"id": "bar"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = await response.parse()
        assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete_records(self, async_client: AsyncWorqhat) -> None:
        async with async_client.db.with_streaming_response.delete_records(
            table="users",
            where={"id": "bar"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = await response.parse()
            assert_matches_type(DBDeleteRecordsResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_batch(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.execute_batch(
            operations=[{"type": "insert"}, {"type": "update"}, {"type": "query"}],
        )
        assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_batch_with_all_params(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.execute_batch(
            operations=[
                {
                    "type": "insert",
                    "data": {
                        "name": "bar",
                        "email": "bar",
                    },
                    "query": "query",
                    "table": "users",
                    "where": {"foo": "bar"},
                },
                {
                    "type": "update",
                    "data": {"status": "bar"},
                    "query": "query",
                    "table": "users",
                    "where": {"email": "bar"},
                },
                {
                    "type": "query",
                    "data": {"foo": "bar"},
                    "query": "SELECT * FROM users WHERE status = 'active'",
                    "table": "table",
                    "where": {"foo": "bar"},
                },
            ],
            environment="development",
            transactional=True,
        )
        assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_batch(self, async_client: AsyncWorqhat) -> None:
        response = await async_client.db.with_raw_response.execute_batch(
            operations=[{"type": "insert"}, {"type": "update"}, {"type": "query"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = await response.parse()
        assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_batch(self, async_client: AsyncWorqhat) -> None:
        async with async_client.db.with_streaming_response.execute_batch(
            operations=[{"type": "insert"}, {"type": "update"}, {"type": "query"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = await response.parse()
            assert_matches_type(DBExecuteBatchResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_query(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
        )
        assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_query_with_all_params(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
            environment="production",
            params={"slug": "bar"},
        )
        assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_query(self, async_client: AsyncWorqhat) -> None:
        response = await async_client.db.with_raw_response.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = await response.parse()
        assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_query(self, async_client: AsyncWorqhat) -> None:
        async with async_client.db.with_streaming_response.execute_query(
            query="SELECT * FROM users WHERE slug = {slug}",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = await response.parse()
            assert_matches_type(DBExecuteQueryResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_insert_record(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
        )
        assert_matches_type(DBInsertRecordResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_insert_record_with_all_params(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
            environment="production",
        )
        assert_matches_type(DBInsertRecordResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_insert_record(self, async_client: AsyncWorqhat) -> None:
        response = await async_client.db.with_raw_response.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = await response.parse()
        assert_matches_type(DBInsertRecordResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_insert_record(self, async_client: AsyncWorqhat) -> None:
        async with async_client.db.with_streaming_response.insert_record(
            data={
                "name": "bar",
                "email": "bar",
            },
            table="users",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = await response.parse()
            assert_matches_type(DBInsertRecordResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_process_nl_query(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.process_nl_query(
            question="How many active users do we have?",
        )
        assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_process_nl_query_with_all_params(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.process_nl_query(
            question="How many active users do we have?",
            context={"foo": "bar"},
            environment="production",
        )
        assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_process_nl_query(self, async_client: AsyncWorqhat) -> None:
        response = await async_client.db.with_raw_response.process_nl_query(
            question="How many active users do we have?",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = await response.parse()
        assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_process_nl_query(self, async_client: AsyncWorqhat) -> None:
        async with async_client.db.with_streaming_response.process_nl_query(
            question="How many active users do we have?",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = await response.parse()
            assert_matches_type(DBProcessNlQueryResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_records(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
        )
        assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_records_with_all_params(self, async_client: AsyncWorqhat) -> None:
        db = await async_client.db.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
            environment="production",
        )
        assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_records(self, async_client: AsyncWorqhat) -> None:
        response = await async_client.db.with_raw_response.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        db = await response.parse()
        assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_records(self, async_client: AsyncWorqhat) -> None:
        async with async_client.db.with_streaming_response.update_records(
            data={"status": "bar"},
            table="users",
            where={"id": "bar"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            db = await response.parse()
            assert_matches_type(DBUpdateRecordsResponse, db, path=["response"])

        assert cast(Any, response.is_closed) is True
