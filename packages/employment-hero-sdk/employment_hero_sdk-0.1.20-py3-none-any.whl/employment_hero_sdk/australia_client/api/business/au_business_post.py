from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.au_business_export_model import AuBusinessExportModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: Union[
        AuBusinessExportModel,
        AuBusinessExportModel,
    ],
    setup_default_data: Union[Unset, bool] = True,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}

    params: Dict[str, Any] = {}

    params["setupDefaultData"] = setup_default_data

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "post",
        "url": "/api/v2/business",
        "params": params,
    }

    if isinstance(body, AuBusinessExportModel):
        _json_body = body.to_dict()

        _kwargs["json"] = _json_body
        headers["Content-Type"] = "application/json"
    if isinstance(body, AuBusinessExportModel):
        _data_body = body.to_dict()

        _kwargs["data"] = _data_body
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[AuBusinessExportModel]:
    if response.status_code == HTTPStatus.OK:
        response_200 = AuBusinessExportModel.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[AuBusinessExportModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        AuBusinessExportModel,
        AuBusinessExportModel,
    ],
    setup_default_data: Union[Unset, bool] = True,
) -> Response[AuBusinessExportModel]:
    """Create New Business

     Creates a new business.

    Args:
        setup_default_data (Union[Unset, bool]):  Default: True.
        body (AuBusinessExportModel):
        body (AuBusinessExportModel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuBusinessExportModel]
    """

    kwargs = _get_kwargs(
        body=body,
        setup_default_data=setup_default_data,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        AuBusinessExportModel,
        AuBusinessExportModel,
    ],
    setup_default_data: Union[Unset, bool] = True,
) -> Optional[AuBusinessExportModel]:
    """Create New Business

     Creates a new business.

    Args:
        setup_default_data (Union[Unset, bool]):  Default: True.
        body (AuBusinessExportModel):
        body (AuBusinessExportModel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuBusinessExportModel
    """

    return sync_detailed(
        client=client,
        body=body,
        setup_default_data=setup_default_data,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        AuBusinessExportModel,
        AuBusinessExportModel,
    ],
    setup_default_data: Union[Unset, bool] = True,
) -> Response[AuBusinessExportModel]:
    """Create New Business

     Creates a new business.

    Args:
        setup_default_data (Union[Unset, bool]):  Default: True.
        body (AuBusinessExportModel):
        body (AuBusinessExportModel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuBusinessExportModel]
    """

    kwargs = _get_kwargs(
        body=body,
        setup_default_data=setup_default_data,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        AuBusinessExportModel,
        AuBusinessExportModel,
    ],
    setup_default_data: Union[Unset, bool] = True,
) -> Optional[AuBusinessExportModel]:
    """Create New Business

     Creates a new business.

    Args:
        setup_default_data (Union[Unset, bool]):  Default: True.
        body (AuBusinessExportModel):
        body (AuBusinessExportModel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuBusinessExportModel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            setup_default_data=setup_default_data,
        )
    ).parsed
