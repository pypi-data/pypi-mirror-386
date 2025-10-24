from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_serial_numbers_resource_type import (
    GetAllSerialNumbersResourceType,
)
from ...models.serial_number_list_response import SerialNumberListResponse


def _get_kwargs(
    *,
    resource_type: Unset | GetAllSerialNumbersResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_resource_type: Unset | str = UNSET
    if not isinstance(resource_type, Unset):
        json_resource_type = resource_type.value

    params["resource_type"] = json_resource_type

    params["resource_id"] = resource_id

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/serial_numbers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SerialNumberListResponse | None:
    if response.status_code == 200:
        response_200 = SerialNumberListResponse.from_dict(response.json())

        return response_200

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
) -> Response[ErrorResponse | SerialNumberListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    resource_type: Unset | GetAllSerialNumbersResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[ErrorResponse | SerialNumberListResponse]:
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        resource_type (Union[Unset, GetAllSerialNumbersResourceType]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, SerialNumberListResponse]]
    """

    kwargs = _get_kwargs(
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    resource_type: Unset | GetAllSerialNumbersResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> ErrorResponse | SerialNumberListResponse | None:
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        resource_type (Union[Unset, GetAllSerialNumbersResourceType]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, SerialNumberListResponse]
    """

    return sync_detailed(
        client=client,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    resource_type: Unset | GetAllSerialNumbersResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[ErrorResponse | SerialNumberListResponse]:
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        resource_type (Union[Unset, GetAllSerialNumbersResourceType]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, SerialNumberListResponse]]
    """

    kwargs = _get_kwargs(
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    resource_type: Unset | GetAllSerialNumbersResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> ErrorResponse | SerialNumberListResponse | None:
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        resource_type (Union[Unset, GetAllSerialNumbersResourceType]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, SerialNumberListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
            page=page,
        )
    ).parsed
