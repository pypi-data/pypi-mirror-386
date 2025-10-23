from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.employee_access_model import EmployeeAccessModel
from ...types import UNSET, Response


def _get_kwargs(
    business_id: str,
    employee_id: str,
    *,
    email: str,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["email"] = email

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/api/v2/business/{business_id}/employee/{employee_id}/access/email",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[EmployeeAccessModel]:
    if response.status_code == HTTPStatus.OK:
        response_200 = EmployeeAccessModel.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[EmployeeAccessModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    business_id: str,
    employee_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    email: str,
) -> Response[EmployeeAccessModel]:
    """Get Employee Access for User

     Gets a list of all employees to which the user (specified by email) has access.

    Args:
        business_id (str):
        employee_id (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmployeeAccessModel]
    """

    kwargs = _get_kwargs(
        business_id=business_id,
        employee_id=employee_id,
        email=email,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    business_id: str,
    employee_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    email: str,
) -> Optional[EmployeeAccessModel]:
    """Get Employee Access for User

     Gets a list of all employees to which the user (specified by email) has access.

    Args:
        business_id (str):
        employee_id (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmployeeAccessModel
    """

    return sync_detailed(
        business_id=business_id,
        employee_id=employee_id,
        client=client,
        email=email,
    ).parsed


async def asyncio_detailed(
    business_id: str,
    employee_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    email: str,
) -> Response[EmployeeAccessModel]:
    """Get Employee Access for User

     Gets a list of all employees to which the user (specified by email) has access.

    Args:
        business_id (str):
        employee_id (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmployeeAccessModel]
    """

    kwargs = _get_kwargs(
        business_id=business_id,
        employee_id=employee_id,
        email=email,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    business_id: str,
    employee_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    email: str,
) -> Optional[EmployeeAccessModel]:
    """Get Employee Access for User

     Gets a list of all employees to which the user (specified by email) has access.

    Args:
        business_id (str):
        employee_id (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmployeeAccessModel
    """

    return (
        await asyncio_detailed(
            business_id=business_id,
            employee_id=employee_id,
            client=client,
            email=email,
        )
    ).parsed
