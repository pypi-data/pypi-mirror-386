from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.error_response import ErrorResponse
from ...models.product_operation_rerank import ProductOperationRerank
from ...models.product_operation_rerank_request import ProductOperationRerankRequest


def _get_kwargs(
    *,
    body: ProductOperationRerankRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/product_operation_rerank",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ProductOperationRerank | None:
    if response.status_code == 200:
        response_200 = ProductOperationRerank.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | ProductOperationRerank]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ProductOperationRerankRequest,
) -> Response[ErrorResponse | ProductOperationRerank]:
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest): Request payload for reordering product operations
            within a manufacturing workflow to optimize production sequence Example:
            {'rank_product_operation_id': 501, 'preceeding_product_operation_id': 499, 'should_group':
            True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ProductOperationRerank]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: ProductOperationRerankRequest,
) -> ErrorResponse | ProductOperationRerank | None:
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest): Request payload for reordering product operations
            within a manufacturing workflow to optimize production sequence Example:
            {'rank_product_operation_id': 501, 'preceeding_product_operation_id': 499, 'should_group':
            True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ProductOperationRerank]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ProductOperationRerankRequest,
) -> Response[ErrorResponse | ProductOperationRerank]:
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest): Request payload for reordering product operations
            within a manufacturing workflow to optimize production sequence Example:
            {'rank_product_operation_id': 501, 'preceeding_product_operation_id': 499, 'should_group':
            True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ProductOperationRerank]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ProductOperationRerankRequest,
) -> ErrorResponse | ProductOperationRerank | None:
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest): Request payload for reordering product operations
            within a manufacturing workflow to optimize production sequence Example:
            {'rank_product_operation_id': 501, 'preceeding_product_operation_id': 499, 'should_group':
            True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ProductOperationRerank]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
