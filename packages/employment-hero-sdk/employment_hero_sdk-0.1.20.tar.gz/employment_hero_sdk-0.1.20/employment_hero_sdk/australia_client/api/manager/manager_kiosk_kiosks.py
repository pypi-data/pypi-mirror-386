from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.time_and_attendance_kiosk_model import TimeAndAttendanceKioskModel
from ...types import Response


def _get_kwargs(
    business_id: int,
) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/api/v2/business/{business_id}/manager/kiosk",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[List["TimeAndAttendanceKioskModel"]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = TimeAndAttendanceKioskModel.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[List["TimeAndAttendanceKioskModel"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    business_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[List["TimeAndAttendanceKioskModel"]]:
    """Get Kiosks

     Returns all kiosks that the user has access to for this business

    Args:
        business_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['TimeAndAttendanceKioskModel']]
    """

    kwargs = _get_kwargs(
        business_id=business_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    business_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[List["TimeAndAttendanceKioskModel"]]:
    """Get Kiosks

     Returns all kiosks that the user has access to for this business

    Args:
        business_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['TimeAndAttendanceKioskModel']
    """

    return sync_detailed(
        business_id=business_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    business_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[List["TimeAndAttendanceKioskModel"]]:
    """Get Kiosks

     Returns all kiosks that the user has access to for this business

    Args:
        business_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['TimeAndAttendanceKioskModel']]
    """

    kwargs = _get_kwargs(
        business_id=business_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    business_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[List["TimeAndAttendanceKioskModel"]]:
    """Get Kiosks

     Returns all kiosks that the user has access to for this business

    Args:
        business_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['TimeAndAttendanceKioskModel']
    """

    return (
        await asyncio_detailed(
            business_id=business_id,
            client=client,
        )
    ).parsed
