import logging
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Callable, Union

from beartype import beartype
from requests import Response
from requests.exceptions import InvalidJSONError

from picsellia import exceptions as exceptions
from picsellia.decorators import exception_handler

logger = logging.getLogger("picsellia")


print_section_handler = os.getenv("PICSELLIA_SDK_SECTION_HANDLER", "0")


def zip_file(path: Union[str, Path]):
    zip_filepath = os.path.splitext(path)[0] + ".zip"
    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(path, path)

    return zip_filepath


def zip_dir(path: Union[str, Path]):
    if not os.path.isdir(path):
        return zip_file(path)

    zip_filepath = os.path.join(os.path.dirname(path), os.path.basename(path) + ".zip")
    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filepath in os.listdir(path):
            zipf.write(os.path.join(path, filepath), filepath)

            if os.path.isdir(os.path.join(path, filepath)):
                for inside_file in os.listdir(os.path.join(path, filepath)):
                    zipf.write(
                        os.path.join(path, filepath, inside_file),
                        os.path.join(filepath, inside_file),
                    )

    return zip_filepath


@exception_handler
@beartype
def unzip(filename: str, target_dir: Union[str, Path] = "./"):
    shutil.unpack_archive(filename, target_dir)


def handle_response(f):
    def decorated(*args, **kwargs):
        response = f(*args, **kwargs)
        check_status_code(response)
        return response

    return decorated


# No exception handling: exception needs to be raised
def check_status_code(response: Response):  # noqa: C901
    status = int(response.status_code)
    if status == 200:
        logger.debug("OK.")
    elif status == 201:
        logger.debug("Resource created.")
    elif status == 202:
        logger.debug("Accepted.")
    elif status == 203:
        logger.debug("OK.")
    elif status == 204:
        logger.debug("No content.")
    elif status != 208 and status <= 299:
        logger.debug(f"Request done : {status}")
    else:
        try:
            data = response.json()
            if "message" not in data:
                data["message"] = f"No message ({status})"

            message = data["message"]
            if "detail" in data and data["detail"] is not None and data["detail"] != []:
                if isinstance(data["detail"], list):
                    message += ". Detail: \n"
                    for item in data["detail"]:
                        message += " > " + str(item) + "\n"
                else:
                    message = message + ". Detail: " + str(data["detail"])
        except (KeyError, InvalidJSONError):
            message = response.text

        logger.debug(
            f"Platform returned an error (status code: {status}). Message : {message}"
        )

        if status == 208:
            raise exceptions.DistantStorageError(
                "An object has already this name in S3."
            )
        if status == 400:
            raise exceptions.BadRequestError(message)
        if status == 401:
            raise exceptions.UnauthorizedError(message)
        if status == 402:
            raise exceptions.InsufficientResourcesError(message)
        if status == 403:
            raise exceptions.ForbiddenError(message)
        if status == 404:
            raise exceptions.ResourceNotFoundError(message)
        if status == 405:
            raise exceptions.PicselliaError(f"Method not allowed: {message}")
        if status == 409:
            raise exceptions.ResourceConflictError(message)
        if status == 413:
            raise exceptions.RequestTooLargeError(
                "There is too much data in your request."
            )
        if status == 422:
            raise exceptions.BadRequestError(message)
        if status == 429:
            raise exceptions.TooManyRequestError(message)
        if status == 500:
            raise exceptions.InternalServerError(message)
        if status == 502:
            raise exceptions.BadGatewayError("Picsellia is unavailable at the moment.")
        raise exceptions.PicselliaError(f"[{status}] Something went wrong, {message}")


@exception_handler
@beartype
def generate_requirements_json(requirements_path: Union[str, Path]) -> list[dict]:
    """Generate a json file with the requirements from the requirements.txt file

    Arguments:
        requirements_path ([str]): [absolute path to requirements.txt file]

    Raises:
        exceptions.ResourceNotFoundError: [Filepath does match]
        Exception: [Wrong requirements file]

    Returns:
        [dict]: {
            'requirements': []{
                'package': (str) package name,
                'version': (str) package version
            }
        }
    """
    requirements = []
    try:
        with open(requirements_path) as f:
            lines = f.readlines()
    except Exception:
        raise exceptions.ResourceNotFoundError(f"{requirements_path} does not exists")
    try:
        for line in lines:
            if line[0] != "#":
                try:
                    package, version = line.split("==")
                except Exception:
                    package, version = line, ""
                tmp = {"package": package.rstrip(), "version": version.rstrip()}
                requirements.append(tmp)
    except Exception:  # pragma: no cover
        raise Exception("Malformed requirements file")
    return requirements


def print_line_return():
    if print_section_handler == "1":
        sys.stdout.write("\n")


def print_start_section():
    if print_section_handler == "1":
        sys.stdout.write("-----")


def print_stop_section():
    if print_section_handler == "1":
        sys.stdout.write("--*--")


def print_start_chapter_name(name: str):
    if print_section_handler == "1":
        sys.stdout.write(f"--#--{name}")


def print_logging_buffer(length: int):
    if print_section_handler == "1":
        sys.stdout.write(f"--{length}--")


def filter_payload(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if v is not None}


def str_to_payload(items):
    return ",".join([f'"{str(item)}"' for item in items])


def convert_tag_list_to_query_language(tags, intersect_tags: bool, prefix: str = ""):
    if tags is None:
        return None

    if not isinstance(tags, list):
        tags = [tags]
    computed_tags = []
    for tag in tags:
        if isinstance(tag, str):
            computed_tags.append(tag)
        else:
            # tag is a Tag, cannot be imported here
            computed_tags.append(tag.name)

    if not computed_tags:
        return None

    if intersect_tags:
        return " and ".join([f'{prefix}tags.name = "{tag}"' for tag in computed_tags])
    else:
        return prefix + "tags.name in (" + str_to_payload(computed_tags) + ")"


def combine_two_ql(q1, q2):
    if q1 is None:
        if q2 is None:
            return None
        else:
            return q2
    else:
        if q2 is None:
            return q1
        else:
            return q1 + " and " + q2


def chunk_list(items: list, chunk_size: int):
    return [(items[i : i + chunk_size], i) for i in range(0, len(items), chunk_size)]


def flatten(items: list[list]) -> list:
    return [item for sublist in items for item in sublist]


def flatten_dict(items: list[dict], filter_value: Callable = lambda _: True) -> dict:
    final_results = {}
    for res in items:
        for key, value in res.items():
            if key not in final_results:
                final_results[key] = value
            elif filter_value(value):
                final_results[key] += value
    return final_results
