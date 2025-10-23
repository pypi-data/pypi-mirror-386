import typing
import datetime as dt
from json.decoder import JSONDecodeError

from ..core.api_error import ApiError
from ..core.client_wrapper import SyncClientWrapper
from ..core.jsonable_encoder import jsonable_encoder
from ..core.pydantic_utilities import pydantic_v1
from ..core.request_options import RequestOptions
from ..types.game import Game

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


class GameClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._client_wrapper = client_wrapper

    def get(
        self, id: int, *, request_options: typing.Optional[RequestOptions] = None
    ) -> Game:
        """
        Examples
        --------
        from vaapi.client import Vaapi

        client = Vaapi(
            base_url='https://vat.berlin-united.com/',
            api_key="YOUR_API_KEY",
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"api/games/{jsonable_encoder(id)}/",
            method="GET",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Game, _response.json())  # type: ignore
            _response_json = _response.json()

        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def delete(
        self, id: int, *, request_options: typing.Optional[RequestOptions] = None
    ) -> None:
        """
        Delete a Log., this will also delete all images and representations

        <Warning>This action can't be undone!</Warning>

        You will need to supply the logs's unique ID. You can find the ID in
        the django admin panel or in the log settings in the UI.
        Parameters
        ----------
        id : int
            A unique integer value identifying this annotation.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        None

        Examples
        --------
        from vaapi.client import Vaapi

        client = Vaapi(
            base_url='https://vat.berlin-united.com/',
            api_key="YOUR_API_KEY",
        )
        client.annotations.delete(
            id=1,
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"api/games/{jsonable_encoder(id)}/",
            method="DELETE",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def update(
        self,
        id: int,
        *,
        event: typing.Optional[int] = OMIT,
        team1: typing.Optional[str] = OMIT,
        team2: typing.Optional[str] = OMIT,
        half: typing.Optional[str] = OMIT,
        is_testgame: typing.Optional[bool] = OMIT,
        head_ref: typing.Optional[str] = OMIT,
        assistent_ref: typing.Optional[str] = OMIT,
        field: typing.Optional[str] = OMIT,
        start_time: typing.Optional[dt.datetime] = OMIT,
        score: typing.Optional[str] = OMIT,
        comment: typing.Optional[str] = OMIT,
        game_folder: typing.Optional[str] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> Game:
        """ """
        _response = self._client_wrapper.httpx_client.request(
            f"api/games/{jsonable_encoder(id)}/",
            method="PATCH",
            json={
                "event": event,
                "team1": team1,
                "team2": team2,
                "half": half,
                "is_testgame": is_testgame,
                "head_ref": head_ref,
                "assistent_ref": assistent_ref,
                "field": field,
                "start_time": start_time,
                "score": score,
                "game_folder": game_folder,
                "comment": comment,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Game, _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def list(
        self,
        *,
        request_options: typing.Optional[RequestOptions] = None,
        **filters: typing.Any,
    ) -> typing.List[Game]:
        """ """
        query_params = {k: v for k, v in filters.items() if v is not None}
        _response = self._client_wrapper.httpx_client.request(
            "api/games/",
            method="GET",
            request_options=request_options,
            params=query_params,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(typing.List[Game], _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def create(
        self,
        *,
        event: typing.Optional[int] = OMIT,
        team1: typing.Optional[str] = OMIT,
        team2: typing.Optional[str] = OMIT,
        half: typing.Optional[str] = OMIT,
        is_testgame: typing.Optional[bool] = OMIT,
        head_ref: typing.Optional[str] = OMIT,
        assistent_ref: typing.Optional[str] = OMIT,
        field: typing.Optional[str] = OMIT,
        start_time: typing.Optional[dt.datetime] = OMIT,
        score: typing.Optional[str] = OMIT,
        game_folder: typing.Optional[str] = OMIT,
        comment: typing.Optional[str] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> Game:
        """ """
        _response = self._client_wrapper.httpx_client.request(
            "api/games/",
            method="POST",
            json={
                "event": event,
                "team1": team1,
                "team2": team2,
                "half": half,
                "is_testgame": is_testgame,
                "head_ref": head_ref,
                "assistent_ref": assistent_ref,
                "field": field,
                "start_time": start_time,
                "score": score,
                "game_folder": game_folder,
                "comment": comment,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Game, _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)
