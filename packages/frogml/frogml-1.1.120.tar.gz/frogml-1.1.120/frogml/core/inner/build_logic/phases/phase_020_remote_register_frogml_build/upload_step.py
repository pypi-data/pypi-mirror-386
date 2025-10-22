from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import joblib
import requests
from retrying import retry

from frogml._proto.qwak.builds.build_url_pb2 import BuildVersioningTagsType
from frogml._proto.qwak.builds.builds_orchestrator_service_pb2 import (
    GetBuildVersioningUploadURLResponse,
    GetBuildVersioningUploadUrlsResponse,
)
from frogml.core.clients.build_orchestrator.client import (
    UrlInfo,
    BuildVersioningTagsTypeEnum,
)
from frogml.core.exceptions import FrogmlException, FrogmlGeneralBuildException
from frogml.core.inner.build_logic.constants.temp_dir import TEMP_LOCAL_MODEL_DIR
from frogml.core.inner.build_logic.constants.upload_tag import (
    BUILD_CONFIG_TAG,
    FROGML_BUILT_MODEL_TAG,
    FROGML_CORE_WHEEL_TAG,
    FROGML_RUNTIME_WHEEL_TAG,
    FROGML_CLI_VERSION_TAG,
    MODEL_CODE_TAG,
    SKINNY_MODEL_CODE_TAG,
)
from frogml.core.inner.build_logic.interface.step_inteface import Step
from frogml.core.inner.build_logic.tools.files import (
    FROGML_IGNORE_FILE_NAME,
    IGNORED_PATTERNS_FOR_UPLOAD,
    UploadInChunks,
    zip_model,
)
from frogml.core.inner.build_logic.tools.ignore_files import (
    load_patterns_from_ignore_file,
)

_MAX_FILE_SIZE_BYTES = 10000000


def should_retry(frogml_exception: FrogmlException) -> bool:
    # when Got 403 from Jfrog it means that the reposity doesn't exist. It may happen when in the first build in the project
    return "403" in str(frogml_exception.message)


class UploadStep(Step):
    STEP_DESCRIPTION = "Saving FrogML Model"

    def description(self) -> str:
        return self.STEP_DESCRIPTION

    def execute(self) -> None:
        files_by_tags: dict[str, Path] = self.create_files_to_upload()
        files_total_size: int = sum(
            file.stat().st_size for _, file in files_by_tags.items()
        )

        upload_urls_response: GetBuildVersioningUploadUrlsResponse = (
            self._get_upload_urls(files_by_tags)
        )

        upload_so_far = 0
        for tag, upload_info in upload_urls_response.upload_url_infos.items():
            file: Optional[Path] = files_by_tags.get(tag, None)
            if file is None:
                raise FrogmlGeneralBuildException(f"No file found for tag {tag}")

            self.upload_file(
                file=file,
                all_files_size_to_upload=files_total_size,
                read_so_far=upload_so_far,
                upload_url=upload_info.upload_url,
                headers=upload_info.headers,
            )
            upload_so_far += file.stat().st_size

            if tag == MODEL_CODE_TAG:
                self.context.model_code_remote_url = str(upload_info.upload_url).split(
                    "?"
                )[0]

    def _get_upload_urls(
        self, files_by_tags: dict[str, Path]
    ) -> GetBuildVersioningUploadUrlsResponse:
        url_infos: list[UrlInfo] = [
            UrlInfo(
                build_id=self.context.build_id,
                model_id=self.context.model_id,
                tag=tag,
                tag_type=BuildVersioningTagsTypeEnum.from_proto(
                    BuildVersioningTagsType.FILE_TAG_TYPE
                ),
            )
            for tag, file_path in files_by_tags.items()
        ]
        upload_urls_response: GetBuildVersioningUploadUrlsResponse = (
            self.context.client_builds_orchestrator.get_build_versioning_upload_urls(
                url_infos=url_infos
            )
        )

        tags_with_no_url: list[str] = [
            tag
            for tag, upload_info in upload_urls_response.upload_url_infos.items()
            if not upload_info.upload_url
        ]

        if tags_with_no_url:
            raise FrogmlGeneralBuildException(
                f"Missing upload url for tags: {tags_with_no_url!r}"
            )

        expected_keys: set[str] = set(files_by_tags.keys())
        actual_keys: set[str] = set(upload_urls_response.upload_url_infos.keys())

        if expected_keys != actual_keys:
            raise FrogmlGeneralBuildException(
                f"Mismatch between requested tags {expected_keys} and response tags {actual_keys}"
            )

        return upload_urls_response

    def create_files_to_upload(self) -> dict[str, Path]:
        ignored_patterns = (
            load_patterns_from_ignore_file(
                build_logger=self.build_logger,
                ignore_file_path=self.context.host_temp_local_build_dir
                / TEMP_LOCAL_MODEL_DIR
                / self.config.build_properties.model_uri.main_dir
                / FROGML_IGNORE_FILE_NAME,
            )
            + IGNORED_PATTERNS_FOR_UPLOAD
        )

        # copy 'main' and 'tests' directories
        dirs_to_include = [self.config.build_properties.model_uri.main_dir, "tests"]
        deps_folders = []
        for (
            folder
        ) in self.config.build_properties.model_uri.dependency_required_folders:
            destination_folder = folder
            while destination_folder.startswith(".."):
                destination_folder = re.sub(r"^\.\./", "", destination_folder)
            deps_folders.append(destination_folder)
        if deps_folders:
            self.build_logger.debug(
                f"Adding dependency folders to model code: {deps_folders}"
            )
            dirs_to_include += deps_folders

        self.build_logger.debug("Zipping skinny model code")
        skinny_size_zip_file = zip_model(
            build_dir=self.context.host_temp_local_build_dir,
            dependency_file=self.context.model_relative_dependency_file,
            deps_lock_file=self.context.model_relative_dependency_lock_file,
            dirs_to_include=dirs_to_include,
            zip_name="skinny_size_model_code",
            ignored_patterns=ignored_patterns,
            max_bytes=_MAX_FILE_SIZE_BYTES,
        )

        # Full size model
        self.build_logger.debug("Zipping full model code")
        full_size_zip_file = zip_model(
            build_dir=self.context.host_temp_local_build_dir,
            dependency_file=self.context.model_relative_dependency_file,
            deps_lock_file=self.context.model_relative_dependency_lock_file,
            dirs_to_include=dirs_to_include,
            zip_name="full_size_model_code",
            ignored_patterns=ignored_patterns,
        )

        # Dump config file for upload
        config_file_temp = self.context.host_temp_local_build_dir / "build.conf"
        config_file_temp.write_text(self.config.to_yaml())

        # Dump frogml-sdk version for upload
        frogml_cli_version_temp_file_path: Path = (
            self.context.host_temp_local_build_dir / "VERSION"
        )
        frogml_cli_version_temp_file_path.write_text(self.context.frogml_cli_version)

        files_by_tags: dict[str, Path] = {
            MODEL_CODE_TAG: full_size_zip_file,
            SKINNY_MODEL_CODE_TAG: skinny_size_zip_file,
            FROGML_CLI_VERSION_TAG: frogml_cli_version_temp_file_path,
            BUILD_CONFIG_TAG: config_file_temp,
        }

        if self.context.custom_runtime_wheel:
            files_by_tags[FROGML_RUNTIME_WHEEL_TAG] = self.context.custom_runtime_wheel

        if self.context.custom_core_wheel:
            files_by_tags[FROGML_CORE_WHEEL_TAG] = self.context.custom_core_wheel

        if self.config.pre_built_model:
            temp_model_file = (
                self.context.host_temp_local_build_dir / FROGML_BUILT_MODEL_TAG
            )
            joblib.dump(self.config.pre_built_model, temp_model_file, compress=3)
            files_by_tags[FROGML_BUILT_MODEL_TAG] = temp_model_file

        return files_by_tags

    def upload_file(
        self,
        file: Path,
        all_files_size_to_upload: int,
        read_so_far: int,
        upload_url: str,
        headers: dict,
    ):
        self.build_logger.debug(f"Uploading file {file}")

        self.upload_file_to_remote_storge(
            upload_url=upload_url,
            file=file,
            all_files_size_to_upload=all_files_size_to_upload,
            read_so_far=read_so_far,
            headers=headers,
        )

        self.build_logger.debug(f"Upload file {file} completed")

    def get_pre_signed_upload_url(
        self, tag: str, tag_type: Optional[BuildVersioningTagsType]
    ) -> GetBuildVersioningUploadURLResponse:
        try:
            self.build_logger.debug(f"Getting pre-signed url for upload - tag {tag}")

            pre_signed_url_response = (
                self.context.client_builds_orchestrator.get_build_versioning_upload_url(
                    build_id=self.context.build_id,
                    model_id=self.context.model_id,
                    tag=tag,
                    tag_type=tag_type,
                )
            )

            self.build_logger.debug("Pre-signed url generated successfully")

            return pre_signed_url_response
        except FrogmlException as e:
            raise FrogmlGeneralBuildException(
                message="Unable to get pre-signed url for uploading model",
                src_exception=e,
            )

    def upload_file_to_remote_storge(
        self,
        upload_url: str,
        file: Path,
        all_files_size_to_upload: int,
        read_so_far: int,
        headers: Optional[dict] = None,
    ):
        if not headers:
            headers = {}

        try:
            self.build_logger.debug(f"Upload file {file} to FrogML storage")

            self.send_request(
                upload_url, file, all_files_size_to_upload, read_so_far, headers
            )
            self.build_logger.debug(
                f"File {file} uploaded to FrogML storage successfully"
            )
        except Exception as e:
            raise FrogmlGeneralBuildException(
                message="Fail uploading model to remote storage.",
                src_exception=e,
            )

    @retry(retry_on_exception=should_retry, wait_fixed=15000, stop_max_delay=60000)
    def send_request(
        self,
        upload_url: str,
        file: Path,
        all_files_size_to_upload: int,
        read_so_far: int,
        headers: Optional[dict],
    ):
        if not headers:
            headers = {}

        # Adding to the current headers the content-type
        headers["content-type"] = "text/plain"

        http_response = requests.put(  # nosec B113
            url=upload_url,
            data=UploadInChunks(
                file=file,
                build_logger=self.build_logger,
                chunk_size_bytes=10,
                all_files_size_to_upload=all_files_size_to_upload,
                read_so_far=read_so_far,
            ),
            headers=headers,
        )

        if http_response.status_code not in [200, 201]:
            raise FrogmlException(
                f"Status: [{http_response.status_code}], "
                f"reason: [{http_response.reason}]"
            )
