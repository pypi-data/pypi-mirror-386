import datetime
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.birthday_report_export_model import BirthdayReportExportModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    business_id: str,
    *,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    location_id: Union[Unset, int] = 0,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_from_date = from_date.isoformat()
    params["fromDate"] = json_from_date

    json_to_date = to_date.isoformat()
    params["toDate"] = json_to_date

    params["locationId"] = location_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/api/v2/business/{business_id}/report/birthday",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[List["BirthdayReportExportModel"]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = BirthdayReportExportModel.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[List["BirthdayReportExportModel"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    business_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    location_id: Union[Unset, int] = 0,
) -> Response[List["BirthdayReportExportModel"]]:
    """Birthday Report

     Generates a birthday report.

    Args:
        business_id (str):
        from_date (datetime.datetime):
        to_date (datetime.datetime):
        location_id (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['BirthdayReportExportModel']]
    """

    kwargs = _get_kwargs(
        business_id=business_id,
        from_date=from_date,
        to_date=to_date,
        location_id=location_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    business_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    location_id: Union[Unset, int] = 0,
) -> Optional[List["BirthdayReportExportModel"]]:
    """Birthday Report

     Generates a birthday report.

    Args:
        business_id (str):
        from_date (datetime.datetime):
        to_date (datetime.datetime):
        location_id (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['BirthdayReportExportModel']
    """

    return sync_detailed(
        business_id=business_id,
        client=client,
        from_date=from_date,
        to_date=to_date,
        location_id=location_id,
    ).parsed


async def asyncio_detailed(
    business_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    location_id: Union[Unset, int] = 0,
) -> Response[List["BirthdayReportExportModel"]]:
    """Birthday Report

     Generates a birthday report.

    Args:
        business_id (str):
        from_date (datetime.datetime):
        to_date (datetime.datetime):
        location_id (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['BirthdayReportExportModel']]
    """

    kwargs = _get_kwargs(
        business_id=business_id,
        from_date=from_date,
        to_date=to_date,
        location_id=location_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    business_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    location_id: Union[Unset, int] = 0,
) -> Optional[List["BirthdayReportExportModel"]]:
    """Birthday Report

     Generates a birthday report.

    Args:
        business_id (str):
        from_date (datetime.datetime):
        to_date (datetime.datetime):
        location_id (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['BirthdayReportExportModel']
    """

    return (
        await asyncio_detailed(
            business_id=business_id,
            client=client,
            from_date=from_date,
            to_date=to_date,
            location_id=location_id,
        )
    ).parsed
