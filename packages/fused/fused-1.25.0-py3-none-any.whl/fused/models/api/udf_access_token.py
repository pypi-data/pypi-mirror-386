import re
import urllib.parse
import warnings
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fused._formatter.formatter_udf_access_token import (
    fused_udf_access_token_list_repr,
    fused_udf_access_token_repr,
)
from fused.models.base import FusedBaseModel
from fused.warnings import FusedDeprecationWarning

from .._inplace import _maybe_inplace


def _make_dtype_query_params(
    *,
    format: Optional[str] = None,
    dtype_out_vector: Optional[str] = None,
    dtype_out_raster: Optional[str] = None,
):
    if dtype_out_raster is not None or dtype_out_vector is not None:
        if format is not None:
            raise ValueError("Cannot specify both format and dtype_out_*")
        else:
            warnings.warn(
                "The 'dtype_out_vector' and 'dtype_out_raster' parameters are "
                "deprecated. Use the 'format' parameter instead.",
                FusedDeprecationWarning,
                stacklevel=3,
            )

    ret = urllib.parse.urlencode(
        {
            **({"format": format} if format else {}),
            **({"dtype_out_vector": dtype_out_vector} if dtype_out_vector else {}),
            **({"dtype_out_raster": dtype_out_raster} if dtype_out_raster else {}),
        }
    )
    if ret:
        return f"?{ret}"
    return ret


OLD_TOKEN_REGEX = re.compile("^[a-f0-9]{64}$")


def is_udf_token(maybe_token: str):
    if OLD_TOKEN_REGEX.match(maybe_token):
        return True
    return maybe_token.startswith("UDF_") or maybe_token.startswith("fsh_")


class UdfAccessToken(FusedBaseModel):
    token: str
    udf_email: Optional[str] = None
    udf_slug: Optional[str] = None
    udf_id: Optional[str] = None
    enabled: bool
    owning_user_id: Optional[str] = None
    owning_execution_environment_id: Optional[str] = (None,)
    client_id: Optional[str]
    public_read: Optional[bool] = None
    access_scope: Optional[str] = None
    cache: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]]
    last_updated: datetime

    def update(
        self,
        client_id: Optional[str] = None,
        cache: Optional[bool] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        public_read: Optional[bool] = None,
        access_scope: Optional[str] = None,
        enabled: Optional[bool] = None,
        inplace: bool = False,
    ) -> "UdfAccessToken":
        ret = _maybe_inplace(self, inplace)
        return ret.model_copy(
            update=self._api.update_udf_access_token(
                token=self.token,
                client_id=client_id,
                cache=cache,
                public_read=public_read,
                access_scope=access_scope,
                metadata_json=metadata_json,
                enabled=enabled,
            ).model_dump()
        )

    def refresh(self, inplace: bool = False) -> "UdfAccessToken":
        ret = _maybe_inplace(self, inplace)
        return ret.model_copy(
            update=self._api.get_udf_access_token(self.token).model_dump()
        )

    def delete(self) -> "UdfAccessToken":
        return self._api.delete_udf_access_token(self.token)

    def get_file_url(
        self,
        *,
        format: Optional[str] = None,
        dtype_out_vector: Optional[str] = None,
        dtype_out_raster: Optional[str] = None,
    ) -> str:
        query_params = _make_dtype_query_params(
            format=format,
            dtype_out_vector=dtype_out_vector,
            dtype_out_raster=dtype_out_raster,
        )
        return f"{self._api.shared_udf_base_url}/{self.token}/run{query_params}"

    def get_tile_url(
        self,
        *,
        x: Union[int, str, None] = None,
        y: Union[int, str, None] = None,
        z: Union[int, str, None] = None,
        format: Optional[str] = None,
        dtype_out_vector: Optional[str] = None,
        dtype_out_raster: Optional[str] = None,
    ) -> str:
        query_params = _make_dtype_query_params(
            format=format,
            dtype_out_vector=dtype_out_vector,
            dtype_out_raster=dtype_out_raster,
        )
        if x is None and y is None and z is None:
            x = "{x}"
            y = "{y}"
            z = "{z}"
        elif x is None or y is None or z is None:
            raise ValueError("All of x, y, and z must be specified")
        return f"{self._api.shared_udf_base_url}/{self.token}/run/tiles/{z}/{x}/{y}{query_params}"

    def _repr_html_(self) -> str:
        return fused_udf_access_token_repr(self)


class UdfAccessTokenList(list):
    def _repr_html_(self) -> str:
        return fused_udf_access_token_list_repr(self)
