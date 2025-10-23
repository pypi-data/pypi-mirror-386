from http import HTTPStatus
from io import BytesIO
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.asset_media_size import AssetMediaSize
from ...types import UNSET, File, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    key: Union[Unset, str] = UNSET,
    size: Union[Unset, AssetMediaSize] = UNSET,
    slug: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["key"] = key

    json_size: Union[Unset, str] = UNSET
    if not isinstance(size, Unset):
        json_size = size.value

    params["size"] = json_size

    params["slug"] = slug

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/assets/{id}/thumbnail".format(
            id=id,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[File]:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.content))

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[File]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient,
    key: Union[Unset, str] = UNSET,
    size: Union[Unset, AssetMediaSize] = UNSET,
    slug: Union[Unset, str] = UNSET,
) -> Response[File]:
    """This endpoint requires the `asset.view` permission.

    Args:
        id (UUID):
        key (Union[Unset, str]):
        size (Union[Unset, AssetMediaSize]):
        slug (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[File]
    """

    kwargs = _get_kwargs(
        id=id,
        key=key,
        size=size,
        slug=slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: AuthenticatedClient,
    key: Union[Unset, str] = UNSET,
    size: Union[Unset, AssetMediaSize] = UNSET,
    slug: Union[Unset, str] = UNSET,
) -> Optional[File]:
    """This endpoint requires the `asset.view` permission.

    Args:
        id (UUID):
        key (Union[Unset, str]):
        size (Union[Unset, AssetMediaSize]):
        slug (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        File
    """

    return sync_detailed(
        id=id,
        client=client,
        key=key,
        size=size,
        slug=slug,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient,
    key: Union[Unset, str] = UNSET,
    size: Union[Unset, AssetMediaSize] = UNSET,
    slug: Union[Unset, str] = UNSET,
) -> Response[File]:
    """This endpoint requires the `asset.view` permission.

    Args:
        id (UUID):
        key (Union[Unset, str]):
        size (Union[Unset, AssetMediaSize]):
        slug (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[File]
    """

    kwargs = _get_kwargs(
        id=id,
        key=key,
        size=size,
        slug=slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient,
    key: Union[Unset, str] = UNSET,
    size: Union[Unset, AssetMediaSize] = UNSET,
    slug: Union[Unset, str] = UNSET,
) -> Optional[File]:
    """This endpoint requires the `asset.view` permission.

    Args:
        id (UUID):
        key (Union[Unset, str]):
        size (Union[Unset, AssetMediaSize]):
        slug (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        File
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            key=key,
            size=size,
            slug=slug,
        )
    ).parsed
