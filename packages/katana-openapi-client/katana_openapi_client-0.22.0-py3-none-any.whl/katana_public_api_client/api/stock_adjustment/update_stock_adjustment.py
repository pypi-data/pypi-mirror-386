from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.stock_adjustment import StockAdjustment
from ...models.update_stock_adjustment_request import UpdateStockAdjustmentRequest


def _get_kwargs(
    id: int,
    *,
    body: UpdateStockAdjustmentRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/stock_adjustments/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | StockAdjustment | None:
    if response.status_code == 200:
        response_200 = StockAdjustment.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = DetailedErrorResponse.from_dict(response.json())

        return response_422

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
) -> Response[DetailedErrorResponse | ErrorResponse | StockAdjustment]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStockAdjustmentRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | StockAdjustment]:
    """Update a stock adjustment

     Updates the specified stock adjustment by setting the values of the parameters passed. Any
    parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStockAdjustmentRequest): Request payload for updating an existing stock
            adjustment Example: {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date':
            '2024-01-17T14:30:00.000Z', 'additional_info': 'Cycle count correction - updated',
            'status': 'COMPLETED'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, StockAdjustment]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStockAdjustmentRequest,
) -> DetailedErrorResponse | ErrorResponse | StockAdjustment | None:
    """Update a stock adjustment

     Updates the specified stock adjustment by setting the values of the parameters passed. Any
    parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStockAdjustmentRequest): Request payload for updating an existing stock
            adjustment Example: {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date':
            '2024-01-17T14:30:00.000Z', 'additional_info': 'Cycle count correction - updated',
            'status': 'COMPLETED'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, StockAdjustment]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStockAdjustmentRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | StockAdjustment]:
    """Update a stock adjustment

     Updates the specified stock adjustment by setting the values of the parameters passed. Any
    parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStockAdjustmentRequest): Request payload for updating an existing stock
            adjustment Example: {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date':
            '2024-01-17T14:30:00.000Z', 'additional_info': 'Cycle count correction - updated',
            'status': 'COMPLETED'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, StockAdjustment]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStockAdjustmentRequest,
) -> DetailedErrorResponse | ErrorResponse | StockAdjustment | None:
    """Update a stock adjustment

     Updates the specified stock adjustment by setting the values of the parameters passed. Any
    parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStockAdjustmentRequest): Request payload for updating an existing stock
            adjustment Example: {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date':
            '2024-01-17T14:30:00.000Z', 'additional_info': 'Cycle count correction - updated',
            'status': 'COMPLETED'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, StockAdjustment]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
