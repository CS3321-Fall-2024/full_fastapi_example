from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from full_fastapi_example.main import (
    MY_MOVIES,
    MovieLookupRequest,
    list_movies,
    lookup_movie,
    run,
)


def test_list_movies_returns_static_list():
    assert list_movies() == MY_MOVIES
    assert list_movies() == [
        {"name": "Chinatown"},
        {"name": "One Battle After Another"},
    ]


@pytest.mark.parametrize(
    ("tmdb_id", "response_json", "expected_title"),
    [
        pytest.param(829, {"title": "Chinatown"}, "Chinatown", id="chinatown"),
        pytest.param(238, {"title": "The Godfather"}, "The Godfather", id="godfather"),
        pytest.param(550, {"title": "Fight Club"}, "Fight Club", id="fight-club"),
    ],
)
def test_lookup_movie_success(mocker, tmdb_id, response_json, expected_title):
    mocker.patch.dict("os.environ", {"TMDB_API_KEY": "fake-key"})
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = response_json
    mock_get = mocker.patch(
        "full_fastapi_example.main.httpx.get",
        return_value=mock_response,
    )

    result = lookup_movie(MovieLookupRequest(tmdb_id=tmdb_id))

    assert result == {"title": expected_title}
    mock_get.assert_called_once_with(
        f"https://api.themoviedb.org/3/movie/{tmdb_id}",
        params={"api_key": "fake-key"},
        timeout=10.0,
    )


@pytest.mark.parametrize(
    ("status_code", "text"),
    [
        pytest.param(404, "Not Found", id="not-found"),
        pytest.param(401, "Invalid API key", id="unauthorized"),
        pytest.param(500, "Server Error", id="server-error"),
    ],
)
def test_lookup_movie_raises_on_non_200(mocker, status_code, text):
    mocker.patch.dict("os.environ", {"TMDB_API_KEY": "fake-key"})
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text
    mocker.patch(
        "full_fastapi_example.main.httpx.get",
        return_value=mock_response,
    )

    with pytest.raises(HTTPException) as exc_info:
        lookup_movie(MovieLookupRequest(tmdb_id=1))

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == text


@pytest.mark.parametrize(
    ("env", "expected_host", "expected_port"),
    [
        pytest.param({}, "127.0.0.1", 8000, id="defaults"),
        pytest.param({"HOST": "0.0.0.0"}, "0.0.0.0", 8000, id="host-override"),
        pytest.param({"PORT": "9000"}, "127.0.0.1", 9000, id="port-override"),
        pytest.param(
            {"HOST": "0.0.0.0", "PORT": "9000"},
            "0.0.0.0",
            9000,
            id="host-and-port-override",
        ),
    ],
)
def test_run_reads_host_and_port_from_env(
    mocker, env, expected_host, expected_port
):
    mocker.patch.dict("os.environ", env, clear=True)
    mock_uvicorn_run = mocker.patch("full_fastapi_example.main.uvicorn.run")

    run()

    mock_uvicorn_run.assert_called_once_with(
        "full_fastapi_example.main:app",
        host=expected_host,
        port=expected_port,
    )
