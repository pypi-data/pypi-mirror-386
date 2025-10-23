from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.asset_bulk_upload_check_dto import AssetBulkUploadCheckDto
from ...models.asset_bulk_upload_check_response_dto import (
    AssetBulkUploadCheckResponseDto,
)
from ...types import Response


def _get_kwargs(
    *,
    body: AssetBulkUploadCheckDto,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/assets/bulk-upload-check",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[AssetBulkUploadCheckResponseDto]:
    if response.status_code == 200:
        response_200 = AssetBulkUploadCheckResponseDto.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[AssetBulkUploadCheckResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: AssetBulkUploadCheckDto,
) -> Response[AssetBulkUploadCheckResponseDto]:
    """checkBulkUpload

     Checks if assets exist by checksums. This endpoint requires the `asset.upload` permission.

    Args:
        body (AssetBulkUploadCheckDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssetBulkUploadCheckResponseDto]
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
    client: AuthenticatedClient,
    body: AssetBulkUploadCheckDto,
) -> Optional[AssetBulkUploadCheckResponseDto]:
    """checkBulkUpload

     Checks if assets exist by checksums. This endpoint requires the `asset.upload` permission.

    Args:
        body (AssetBulkUploadCheckDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssetBulkUploadCheckResponseDto
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: AssetBulkUploadCheckDto,
) -> Response[AssetBulkUploadCheckResponseDto]:
    """checkBulkUpload

     Checks if assets exist by checksums. This endpoint requires the `asset.upload` permission.

    Args:
        body (AssetBulkUploadCheckDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssetBulkUploadCheckResponseDto]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: AssetBulkUploadCheckDto,
) -> Optional[AssetBulkUploadCheckResponseDto]:
    """checkBulkUpload

     Checks if assets exist by checksums. This endpoint requires the `asset.upload` permission.

    Args:
        body (AssetBulkUploadCheckDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssetBulkUploadCheckResponseDto
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
