import http
import json
import os
from typing import Optional, Tuple, Union, List, cast, Iterable

import requests
from cachetools import cached, LRUCache
from requests import Response, HTTPError
from requests.auth import AuthBase, HTTPBasicAuth

from frogml.storage.artifactory import ArtifactoryApi
from frogml.storage.authentication.models import (
    BearerAuth,
    EmptyAuth,
    AuthConfig,
    LoginArguments,
)
from frogml.storage.constants import (
    CONFIG_FILE_PATH,
    FROG_ML_CONFIG_ACCESS_TOKEN,
    FROG_ML_CONFIG_ARTIFACTORY_URL,
    FROG_ML_CONFIG_PASSWORD,
    FROG_ML_CONFIG_USER,
    JF_ACCESS_TOKEN,
    JF_URL,
    JFROG_CLI_CONFIG_ACCESS_TOKEN,
    JFROG_CLI_CONFIG_ARTIFACTORY_URL,
    JFROG_CLI_CONFIG_FILE_PATH,
    JFROG_CLI_CONFIG_URL,
    JFROG_CLI_CONFIG_USER,
    SERVER_ID,
)
from frogml.storage.logging import logger
from frogml.storage.utils import join_url


def read_jfrog_cli_config() -> Union[dict, None]:
    try:
        with open(JFROG_CLI_CONFIG_FILE_PATH, "r") as file:
            config_data = json.load(file)
            return config_data
    except FileNotFoundError:
        logger.debug("JFrog cli config file was not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"JFrog cli config file is not a valid JSON {e}.")
        return None


def read_frogml_config() -> Union[dict, None]:
    try:
        with open(CONFIG_FILE_PATH, "r") as file:
            config_data = json.load(file)
            return config_data
    except FileNotFoundError:
        logger.debug("FrogMl config file was not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"FrogMl config file is not a valid JSON {e}.")
        return None


def parse_cli_config_server(server_config: dict) -> Union[LoginArguments, None]:
    login_args = LoginArguments()
    login_args.server_id = server_config.get(SERVER_ID)

    if JFROG_CLI_CONFIG_ARTIFACTORY_URL in server_config:
        login_args.artifactory_url = server_config.get(JFROG_CLI_CONFIG_ARTIFACTORY_URL)
    elif (
        JFROG_CLI_CONFIG_URL in server_config
        and server_config.get(JFROG_CLI_CONFIG_URL) is not None
    ):
        login_args.artifactory_url = join_url(
            server_config[JFROG_CLI_CONFIG_URL], "artifactory"
        )
    else:
        logger.debug(
            "Invalid JFrog CLI file, expected either artifactoryUrl or url in jfrog cli config file"
        )
        return None

    if JFROG_CLI_CONFIG_ACCESS_TOKEN in server_config:
        login_args.access_token = server_config.get(JFROG_CLI_CONFIG_ACCESS_TOKEN)
    elif JFROG_CLI_CONFIG_USER in server_config:
        login_args.username = server_config.get(JFROG_CLI_CONFIG_USER)
        login_args.password = input(f"Enter password for {login_args.username}: ")
    else:
        logger.debug(
            "Expected either accessToken or user/password in jfrog cli config file"
        )
        return None

    return login_args


def get_frogml_configuration() -> Union[LoginArguments, None]:
    frog_ml_config = read_frogml_config()
    if (
        frog_ml_config is not None
        and frog_ml_config.get("servers") is not None
        and len(frog_ml_config["servers"]) > 0
    ):
        server_config = frog_ml_config["servers"][0]
        login_args = LoginArguments()
        if FROG_ML_CONFIG_ARTIFACTORY_URL in server_config:
            login_args.artifactory_url = server_config.get(
                FROG_ML_CONFIG_ARTIFACTORY_URL
            )
        else:
            logger.debug(
                "Invalid FrogMl authentication file, expected either artifactory_url in FrogMl authentication file"
            )
            return None

        if FROG_ML_CONFIG_ACCESS_TOKEN in server_config:
            login_args.access_token = server_config.get(FROG_ML_CONFIG_ACCESS_TOKEN)
        elif (
            FROG_ML_CONFIG_USER in server_config
            and FROG_ML_CONFIG_PASSWORD in server_config
        ):
            login_args.username = server_config.get(FROG_ML_CONFIG_USER)
            login_args.password = server_config.get(FROG_ML_CONFIG_PASSWORD)
        elif (
            FROG_ML_CONFIG_USER in server_config
            and FROG_ML_CONFIG_PASSWORD not in server_config
            or (
                FROG_ML_CONFIG_USER not in server_config
                and FROG_ML_CONFIG_PASSWORD in server_config
            )
        ):
            logger.debug(
                "Invalid FrogMl authentication file, username or password is missing in FrogMl authentication file"
            )
            return None
        elif (
            login_args.username is None
            and login_args.password is None
            and login_args.access_token is None
        ):
            login_args.isAnonymous = True
        return login_args
    else:
        return None


def try_generate_access_token(
    artifactory_url: str, auth_token: HTTPBasicAuth
) -> Optional[str]:
    try:
        logger.info(
            f"Trying to generate access token for artifactory url {artifactory_url}"
        )
        response: Response = ArtifactoryApi(
            artifactory_url, auth_token
        ).generate_access_token()
        response.raise_for_status()
        json_response = response.json()
        access_token: str = json_response.get("access_token")
        if access_token is None:
            logger.error(
                f"Failed to generate access token for {artifactory_url}."
                f"The response is: \n {json.dumps(json_response, indent=2)}"
            )
            return None
        logger.warning(
            f"Successfully generated access token for {artifactory_url}. "
            f"Please note that this token being generated for 30 days. "
            f"After 30 days, please run config again"
        )
        return access_token
    except HTTPError as e:
        logger.error(
            f"Failed to generate access token for {artifactory_url}. "
            f"Please use access token or ask the JFrog Platform to enable generation of access token via REST api. "
            f"For more info please check the following: https://jfrog.com/help/r/jfrog-platform-administration-documentation/generate-scoped-tokens"
        )
        logger.debug(f"Failed to generate access token due to: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error while trying to generate token: {e}.")
        return None
    except ValueError as e:
        logger.error(f"Error while trying to parse returned response for token: {e}.")
        return None


def get_encrypted_password(
    auth_config: AuthConfig, auth_token: AuthBase
) -> Optional[str]:
    try:
        response = ArtifactoryApi(
            auth_config.artifactory_url, auth_token
        ).encrypt_password()
        if response.status_code != http.HTTPStatus.OK:
            logger.debug(
                f"Expected {http.HTTPStatus.OK} status but got {response.status_code} "
                f"when using url {auth_config.artifactory_url}"
            )
            print("Error while trying to encrypt password.")
            return None
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error while trying to encrypt password: {e}.")
        return None


def save_auth_config(login_args: LoginArguments) -> None:
    file_content: dict[str, list] = {}
    auth_config: AuthConfig = AuthConfig(
        artifactory_url=login_args.artifactory_url,
        access_token=login_args.access_token,
        server_id=login_args.server_id,
    )
    file_content.setdefault("servers", []).append(auth_config.to_json())
    os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
    with open(CONFIG_FILE_PATH, "w") as file:
        json.dump(file_content, file, indent=2)


@cached(cache=LRUCache(maxsize=1))
def get_credentials(
    auth_config: Optional[AuthConfig] = None,
) -> Tuple[str, Union[EmptyAuth, BearerAuth]]:
    if not __should_use_file_auth(auth_config):
        return __auth_config_to_auth_tuple(cast(AuthConfig, auth_config))
    logger.debug(
        "Login configuration not supplied, attempting to find environment variables"
    )

    if __should_use_environment_variables():
        return get_environment_variables()

    logger.debug(
        "Environment variables not supplied, attempting to load configuration from file"
    )

    if os.path.exists(CONFIG_FILE_PATH):
        return __read_credentials_from_file(CONFIG_FILE_PATH)

    raise ValueError(
        f"Configuration were not provided and configuration file not found in {CONFIG_FILE_PATH},"
        f" either pass configuration in the constructor, add env variables or create the configuration file by "
        f"running `frogml login`"
    )


def __should_use_environment_variables() -> bool:
    return os.getenv("JF_URL") is not None


def get_environment_variables() -> Tuple[str, AuthBase]:
    auth_config: AuthConfig = AuthConfig(
        artifactory_url=os.getenv(JF_URL),
        access_token=os.getenv(JF_ACCESS_TOKEN),
    )

    return __auth_config_to_auth_tuple(auth_config)


def __should_use_file_auth(credentials: Optional[AuthConfig] = None) -> bool:
    return credentials is None or (
        credentials.artifactory_url is None
        and credentials.user is None
        and credentials.password is None
        and credentials.access_token is None
    )


def __validate_credentials(auth_config: AuthConfig) -> None:
    if auth_config.artifactory_url is None:
        raise ValueError("Credentials must contain artifactory url.")

    return None


def __read_credentials_from_file(
    file_path: str,
) -> Tuple[str, Union[BearerAuth, EmptyAuth]]:
    try:
        with open(file_path, "r") as file:
            config_content: dict = json.load(file)
            servers = config_content.get("servers")
            if servers is None or len(servers) == 0:
                raise ValueError(
                    "Configuration file was found but it's empty, failing authentication"
                )
            server = servers[0]
            return __auth_config_to_auth_tuple(AuthConfig.from_dict(server))
    except json.JSONDecodeError:
        raise ValueError(f"Error when reading {file_path}, please recreate the file.")


def __auth_config_to_auth_tuple(
    auth_config: AuthConfig,
) -> Tuple[str, Union[BearerAuth, EmptyAuth]]:
    __validate_credentials(auth_config)

    artifactory_url: str = auth_config.artifactory_url

    if auth_config.access_token is not None:
        return artifactory_url, BearerAuth(auth_config.access_token)

    return artifactory_url, EmptyAuth()


def get_list_of_servers_from_config(jfrog_cli_config: Optional[dict]) -> List[str]:
    if not jfrog_cli_config or not jfrog_cli_config.get("servers"):
        return []

    servers: Iterable[dict] = jfrog_cli_config["servers"]
    return list(map(__map_server_ids, servers))


def __map_server_ids(server: dict) -> str:
    server_id = str(server.get("serverId"))

    if server.get("isDefault"):
        server_id += " (Default)"

    return server_id
