"""Testing the creation, update and deletion of a project."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from numind.models import CreateProjectRequest

from .conftest import EXTRACT_KWARGS, TEST_CASES

if TYPE_CHECKING:
    from numind import NuMind, NuMindAsync


@pytest.fixture(params=TEST_CASES, ids=lambda tc: f"project_{tc[0]}", scope="session")
def test_case(
    request: pytest.FixtureRequest,
) -> tuple[str, dict, list[str], list[Path]]:
    return request.param


@pytest.mark.dependency(name="create_project")
def test_create_project(
    numind_client: NuMind,
    test_case: tuple[
        str, dict, list[str], list[Path], list[tuple[str | Path, dict | str]]
    ],
    request: pytest.FixtureRequest,
) -> None:
    project_name, schema, string_list, file_paths_list, examples = test_case
    # Convert examples Paths to str as needed to be json serializable when saving them
    # to pytest's cache.
    for idx in range(len(examples)):  # convert Path to str
        if isinstance(examples[idx][0], Path):
            examples[idx] = (str(examples[idx][0]), examples[idx][1])
    project_id = numind_client.post_api_projects(
        CreateProjectRequest(name=project_name, description="", template=schema)
    ).id
    request.config.cache.set("project_id", project_id)
    request.config.cache.set("text_cases", string_list)
    request.config.cache.set(
        "file_cases", [str(file_path) for file_path in file_paths_list]
    )
    request.config.cache.set("examples", examples)


@pytest.mark.dependency(depends=["create_project"])
def test_get_existing_projects(
    numind_client: NuMind, request: pytest.FixtureRequest
) -> None:
    project_id = request.config.cache.get("project_id", None)
    projects = numind_client.get_api_projects()
    assert project_id in {project.id for project in projects}


@pytest.mark.dependency(depends=["create_project"])
def test_add_examples_to_project(
    numind_client: NuMind, request: pytest.FixtureRequest
) -> None:
    project_id = request.config.cache.get("project_id", None)
    examples = request.config.cache.get("examples", None)
    for idx in range(len(examples)):  # convert str paths to Path
        try:
            example_path = Path(examples[idx][0])
            if example_path.is_file():
                examples[idx] = (example_path, examples[idx][1])
        except (OSError, RuntimeError):
            continue
    _ = numind_client.add_examples_to_project(project_id, examples)


@pytest.mark.dependency(name="infer_text", depends=["create_project"])
def test_infer_text(numind_client: NuMind, request: pytest.FixtureRequest) -> None:
    project_id = request.config.cache.get("project_id", None)
    text_cases = request.config.cache.get("text_cases", None)
    for input_text in text_cases:
        _ = numind_client.post_api_projects_projectid_extract(
            project_id, input_text.encode()
        )


@pytest.mark.asyncio
@pytest.mark.dependency(name="infer_text_async", depends=["create_project"])
async def test_infer_text_async(
    numind_client_async: NuMindAsync, request: pytest.FixtureRequest
) -> None:
    project_id = request.config.cache.get("project_id", None)
    text_cases = request.config.cache.get("text_cases", None)

    tasks = [
        numind_client_async.post_api_projects_projectid_extract(
            project_id, input_text.encode()
        )
        for input_text in text_cases
    ]
    await asyncio.gather(*tasks)


@pytest.mark.dependency(name="infer_file", depends=["create_project"])
def test_infer_file(numind_client: NuMind, request: pytest.FixtureRequest) -> None:
    project_id = request.config.cache.get("project_id", None)
    file_cases = request.config.cache.get("file_cases", None)
    for file_path in file_cases:
        file_path = Path(file_path)
        with file_path.open("rb") as file:
            intput_file = file.read()
        _ = numind_client.post_api_projects_projectid_extract(
            project_id, intput_file, **EXTRACT_KWARGS
        )


# TODO remove dependency, make it run whether these tests failed or not
@pytest.mark.dependency(depends=["infer_text", "infer_text_async", "infer_file"])
def test_delete_project_and_has_been_deleted(
    numind_client: NuMind, request: pytest.FixtureRequest
) -> None:
    project_id = request.config.cache.get("project_id", None)
    numind_client.delete_api_projects_projectid(project_id)
    projects = numind_client.get_api_projects()
    assert project_id not in {project.id for project in projects}
