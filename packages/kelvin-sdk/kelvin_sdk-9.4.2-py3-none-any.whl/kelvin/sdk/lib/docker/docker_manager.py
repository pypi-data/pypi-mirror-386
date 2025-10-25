"""
Copyright 2021 Kelvin Inc.

Licensed under the Kelvin Inc. Developer SDK License Agreement (the "License"); you may not use
this file except in compliance with the License.  You may obtain a copy of the
License at

http://www.kelvininc.com/developer-sdk-license

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OF ANY KIND, either express or implied.  See the License for the
specific language governing permissions and limitations under the License.
"""

import tarfile
from pathlib import PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Union

from docker import APIClient  # type: ignore
from docker.errors import DockerException, NotFound
from docker.types import CancellableStream
from jinja2 import Template
from packaging.version import parse as parse_version
from python_on_whales import docker as docker_buildx

from kelvin.sdk.lib.configs.click_configs import color_formats
from kelvin.sdk.lib.configs.docker_configs import DockerConfigs
from kelvin.sdk.lib.configs.emulation_configs import EmulationConfigs
from kelvin.sdk.lib.configs.general_configs import GeneralConfigs, GeneralMessages
from kelvin.sdk.lib.docker.docker_utils import (
    assess_docker_connection_exception,
    display_docker_progress,
    ensure_docker_is_running,
)
from kelvin.sdk.lib.exceptions import DependencyNotRunning, InvalidApplicationConfiguration, KDockerException, KSDKFatal
from kelvin.sdk.lib.models.apps.common import ApplicationLanguage, Mqtt
from kelvin.sdk.lib.models.apps.ksdk_app_configuration import Environment, ProjectType
from kelvin.sdk.lib.models.apps.ksdk_app_setup import (
    DockerAppBuildingObject,
    KelvinAppBuildingObject,
    ProjectBuildingObject,
    ProjectEmulationObject,
)
from kelvin.sdk.lib.models.generic import KPath, OSInfo
from kelvin.sdk.lib.models.ksdk_docker import (
    DockerContainer,
    DockerImage,
    DockerImageName,
    DockerNetwork,
    KSDKDockerAuthentication,
    KSDKNetworkConfiguration,
)
from kelvin.sdk.lib.models.types import EmbeddedFiles, VersionStatus
from kelvin.sdk.lib.session.session_manager import session_manager
from kelvin.sdk.lib.templates.templates_manager import get_embedded_file
from kelvin.sdk.lib.utils.display_utils import pretty_colored_content
from kelvin.sdk.lib.utils.general_utils import get_iec_to_si_format_as_human_readable, get_random_hex_string
from kelvin.sdk.lib.utils.logger_utils import logger
from kelvin.sdk.lib.utils.version_utils import assess_version_status

HOST_GATEWAY_SUPPORT_START = parse_version("24.0.3")
HOST_GATEWAY_SUPPORT_END = parse_version("25.0.0")


class DockerManager:
    _docker_client: APIClient

    def __init__(self) -> None:
        self._reset_docker_client()

    def login_to_docker_registry(self, registry_url: str, username: str, password: str) -> None:
        logger.info(f'Attempting to log on "{registry_url}" Docker registry')

        self._docker_client.login(
            username=username,
            password=password,
            registry=registry_url,
        )

        docker_buildx.login(
            server=registry_url,
            username=username,
            password=password,
        )

    def _reset_docker_client(self) -> APIClient:
        """
        Resets the client to its original state.

        Returns
        -------
        APIClient
            the internal Docker API Client in its new state.

        """
        try:
            self._docker_client = APIClient(timeout=DockerConfigs.docker_client_timeout)
        except Exception as exc:
            raise assess_docker_connection_exception(exc=exc)
        return self._docker_client

    @ensure_docker_is_running
    def _validate_docker_version(self, minimum_docker_version: Optional[str]) -> bool:
        """
        Sets up the minimum accepted docker version and matches it against the current docker version of the system.

        Parameters
        ----------
        minimum_docker_version : Optional[str]
             the minimum accepted docker version, externally injected.

        Returns
        -------
        bool
            a boolean indicating whether the current docker version is supported and able to run with ksdk

        """
        version_status = VersionStatus.UP_TO_DATE
        if minimum_docker_version:
            system_docker_version = ""
            try:
                docker_version_object = self._docker_client.version() if self._docker_client else None
            except (DockerException, Exception):
                docker_version_object = None

            if docker_version_object:
                system_docker_version = docker_version_object.get("Version", "").rsplit("-", 1)[0]

            if not system_docker_version:
                raise DependencyNotRunning(message=DockerConfigs.docker_dependency)

            version_status = assess_version_status(
                minimum_version=minimum_docker_version,
                current_version=system_docker_version,
                latest_version=system_docker_version,
            )

            if version_status == VersionStatus.UNSUPPORTED:
                docker_version_unsupported: str = """\n
                        {red}Docker version is no longer supported!{reset} \n
                        {red}Current: {current_version}{reset} → {yellow}Minimum: {minimum_version}{reset} \n
                        {green}For more information{reset}: https://docs.docker.com/engine/install/ \n
                        Please update Docker in order to proceed.
                """.format_map(
                    {
                        **color_formats,
                        "current_version": system_docker_version,
                        "minimum_version": minimum_docker_version,
                    }
                )
                raise KDockerException(message=docker_version_unsupported)

        return version_status == VersionStatus.UP_TO_DATE

    # 2 - DOCKERFILES
    @staticmethod
    def build_kelvin_app_dockerfile(kelvin_app_building_object: KelvinAppBuildingObject) -> bool:
        """
        Build the docker file used in the creation of the docker image.

        Parameters
        ----------
        kelvin_app_building_object : KelvinAppBuildingObject
            the KelvinAppBuildingObject with all the required variables to build an app.

        Returns
        -------
        bool
            a boolean indicating whether the dockerfile was successfully built.

        """
        # 1 - Make sure the kelvin app configuration is available
        kelvin_app = kelvin_app_building_object.app_config_model.app.app_type_configuration  # type: ignore
        if kelvin_app is None:
            raise InvalidApplicationConfiguration(message=str(kelvin_app_building_object.app_config_file_path))

        if kelvin_app.language is None:
            raise InvalidApplicationConfiguration(
                message=GeneralMessages.invalid_name.format(reason="Language is missing")
            )

        # 2 - if there is an image configuration that provides a valid system packages list, collect it.
        system_packages: str = ""
        if kelvin_app.system_packages:
            system_packages = " ".join(kelvin_app.system_packages)

        # 3 - Verify compatibility between for python apps.
        docker_entrypoint: Optional[str] = None
        docker_cmd: Optional[str] = None
        requirements_file = None
        app_language = kelvin_app.language.type

        if app_language == ApplicationLanguage.python:
            docker_entrypoint, docker_cmd = kelvin_app_building_object.get_dockerfile_run_command()
            python_app_config = kelvin_app.language.python
            if python_app_config:
                # extract file path from entrypoint point
                requirements_available, requirements_file_path = python_app_config.requirements_available(
                    app_dir_path=kelvin_app_building_object.app_dir_path
                )
                if requirements_available and requirements_file_path:
                    requirements_file = requirements_file_path.name

        # 4 - Retrieve the appropriate docker template for the language the app is building for.
        template: EmbeddedFiles = kelvin_app_building_object.get_dockerfile_template()

        # check if there are any wheels
        wheels_dir = kelvin_app_building_object.get_wheels_dir()

        dockerfile_template: Template = get_embedded_file(embedded_file=template)
        if not dockerfile_template:
            raise KDockerException(f"No template available for {app_language.value_as_str} kelvin_app_lang")

        # 5 - Prepare the dockerfile parameters and finally render the template with them as arguments.
        dockerfile_parameters: Dict[str, Any] = {
            "build_for_upload": kelvin_app_building_object.build_for_upload,
            "build_for_datatype_compilation": kelvin_app_building_object.build_for_datatype_compilation,
            "kelvin_app_builder_image": kelvin_app_building_object.kelvin_app_builder_image,
            "kelvin_app_runner_image": kelvin_app_building_object.kelvin_app_runner_image,
            "app_configuration_file": kelvin_app_building_object.app_config_file_path.name,
            "requirements_file": requirements_file,
            "system_packages": system_packages,
            "app_language": app_language.name,
            "wheels_dir": wheels_dir,
        }
        if docker_entrypoint:
            dockerfile_parameters.update({"docker_entrypoint": docker_entrypoint})
        if docker_cmd:
            dockerfile_parameters.update({"docker_cmd": docker_cmd})

        dockerfile_content = dockerfile_template.render(dockerfile_parameters)
        kelvin_app_building_object.dockerfile_path.write_text(dockerfile_content)
        logger.debug(f"Build Dockerfile:\n\n{dockerfile_content}")

        return True

    # 3 - IMAGES
    @ensure_docker_is_running
    def get_docker_images(
        self,
        labels: Optional[dict] = None,
        image_ids: Optional[List[str]] = None,
        image_parent_ids: Optional[List[str]] = None,
        image_names: Optional[List[str]] = None,
    ) -> List[DockerImage]:
        """
        Obtain a list of all docker images available in the system.

        This image list can be narrowed down by using labels or an image name.
        By default, includes the standard: {'source': 'ksdk'} labels.

        Parameters
        ----------
        image_names : Optional[List[str]]
            the names of the docker images to filter.
        image_ids : Optional[List[str]]
            the ids of the docker images to filter.
        image_parent_ids : Optional[List[str]]
            the ids of the parents
             to filter.
        labels : Optional[dict]
            the labels used to selectively get containers.

        Returns
        -------
        List[DockerImage]
            a list of DockerImage items.

        """
        docker_images = self._docker_client.images()
        all_docker_images: List[DockerImage] = [
            DockerImage.get_docker_image_object(raw_image_object=image) for image in docker_images
        ]

        if not any([labels, image_ids, image_parent_ids, image_names]):
            return all_docker_images
        else:
            images_to_return: List[DockerImage] = []
            provided_image_names: List[str] = image_names or []
            provided_image_ids: List[str] = image_ids or []
            provided_image_parent_ids: List[str] = image_parent_ids or []

            for image in all_docker_images:
                # 1 - check if there is a match on image tags
                internal_image_tags: List[str] = image.tags
                if bool(set(provided_image_names) & set(internal_image_tags)):
                    images_to_return.append(image)
                    continue
                # 2 - check the image ids
                if provided_image_ids:
                    image_id = image.id.replace("sha256:", "")
                    if image_id in provided_image_ids:
                        images_to_return.append(image)
                        continue
                # 3 - check the image parent ids
                if provided_image_parent_ids:
                    image_parent_id = image.parent_id.replace("sha256:", "")
                    if image_parent_id in provided_image_parent_ids:
                        images_to_return.append(image)
                        continue
                # 4 - check if there is a match on labels
                if labels:
                    if "name" in labels:
                        labels.pop("name", "")
                    internal_image_labels: Dict[Any, Any] = image.labels or {}
                    if labels.items() <= internal_image_labels.items():
                        images_to_return.append(image)
                        continue
            return images_to_return

    @ensure_docker_is_running
    def build_kelvin_app_docker_image(self, kelvin_app_building_object: KelvinAppBuildingObject) -> bool:
        """
        Build the docker image from the provided KelvinAppBuildingObject.

        An exception is expected should any step of the process fail.

        Parameters
        ----------
        kelvin_app_building_object : KelvinAppBuildingObject
            an object that contains the necessary variables to build a kelvin-type app.

        Returns
        -------
        bool
            a boolean indicating whether the image was successfully built
        """
        # 1 - Both *builder* and *runner* images are required so we ensure their existence

        kelvin_app_building_object.kelvin_app_builder_image = self.ensure_docker_image_exists(
            docker_image=kelvin_app_building_object.kelvin_app_builder_image
        )
        kelvin_app_building_object.kelvin_app_runner_image = self.ensure_docker_image_exists(
            docker_image=kelvin_app_building_object.kelvin_app_runner_image
        )
        # 1.1 - The yielded application images will be further used to be set in the Dockerfile

        # 2 - Build the Dockerfile
        self.build_kelvin_app_dockerfile(kelvin_app_building_object=kelvin_app_building_object)

        # 3 - Build the application
        return self._build_engine_step(
            base_build_object=kelvin_app_building_object,
            dockerfile_path=kelvin_app_building_object.dockerfile_path,
            docker_build_context_path=kelvin_app_building_object.docker_build_context_path,
            build_args=kelvin_app_building_object.build_args,
        )

    @ensure_docker_is_running
    def build_docker_app_image(self, docker_build_object: DockerAppBuildingObject) -> bool:
        """
        Build the docker image from the provided DockerAppBuildingObject.

        An exception is expected should any step of the process fail.

        Parameters
        ----------
        docker_build_object : DockerAppBuildingObject
            an object that contains the necessary variables to build a docker-type app.

        Returns
        -------
        bool
            a boolean indicating whether the image was successfully built.

        """

        # 1 - Make sure the kelvin app configuration is available
        docker_app = docker_build_object.app_config_model.app.docker  # type: ignore
        if not docker_app:
            raise InvalidApplicationConfiguration(message=str(docker_build_object.app_config_file_path))

        dockerfile_path: KPath = docker_build_object.app_dir_path / docker_app.dockerfile
        docker_build_context_path: KPath = (dockerfile_path / KPath(docker_app.context)).expanduser().absolute().parent

        build_args = {}

        if docker_app.args:
            split_args = (arg.split("=") for arg in docker_app.args)
            build_args = {key: value for key, value in split_args}

        return self._build_engine_step(
            base_build_object=docker_build_object,
            dockerfile_path=dockerfile_path,
            docker_build_context_path=docker_build_context_path,
            build_args=build_args,
        )

    @ensure_docker_is_running
    def build_kelvin_v2_app_image(self, build_object: ProjectBuildingObject) -> bool:
        """
        Build the docker image from the provided DockerAppBuildingObject.

        An exception is expected should any step of the process fail.

        Parameters
        ----------
        docker_build_object : DockerAppBuildingObject
            an object that contains the necessary variables to build a docker-type app.

        Returns
        -------
        bool
            a boolean indicating whether the image was successfully built.

        """

        dockerfile_path: KPath = build_object.app_dir_path / "Dockerfile"
        docker_build_context_path: KPath = dockerfile_path.expanduser().absolute().parent

        return self._build_engine_step(
            base_build_object=build_object,
            dockerfile_path=dockerfile_path,
            docker_build_context_path=docker_build_context_path,
            build_args=build_object.build_args,
        )

    def _build_engine_step(
        self,
        base_build_object: ProjectBuildingObject,
        dockerfile_path: KPath,
        docker_build_context_path: KPath,
        build_args: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Internal method shared by both kelvin and docker apps in order to build.

        Parameters
        ----------
        base_build_object : ProjectBuildingObject
            the base building object with the necessary inputs.
        dockerfile_path : KPath
            the path to the dockerfile
        docker_build_context_path : KPath
            the path to where the docker build should be executed (context).
        build_args : Optional[Dict[str, str]]
            additional build arguments to be passed to the build operation.

        Returns
        -------
        bool
            A boolean indicating the build step was successfully executed.

        """
        # 1 - Setup the required variables for the build engine
        docker_image_name = base_build_object.full_docker_image_name  # name of the docker image
        docker_image_labels = base_build_object.docker_image_labels  # ksdk identification labels
        PurePosixPath(dockerfile_path.relative_to(docker_build_context_path))

        # 2.1 - If its an 'appregistry upload', or a 'fresh run' purge any previous instance and start from scratch
        if base_build_object.fresh_build:
            self.remove_docker_image(docker_image_name=docker_image_name)
            self.prune_docker_containers()
            self.prune_docker_images()
        # 2.2 - If its a 'rebuild', stop all existing containers of this same app
        else:
            self.stop_containers(image_names=[docker_image_name])

        # 3 - build the image using the buildkit
        buildx_builder = docker_buildx.buildx.inspect()
        driver = buildx_builder.driver
        version = HOST_GATEWAY_SUPPORT_END
        server_version = docker_buildx.info().server_version
        if server_version:
            version = parse_version(server_version)

        # map common architecture names to Docker platforms
        platform_map = {
            "amd64": "linux/amd64",
            "arm64": "linux/arm64",
            "arm32": "linux/arm/v7",
        }

        platforms = {platform_map.get(arch, arch) for arch in base_build_object.archs}
        if not platforms:
            platforms = {"linux/amd64"}

        buildx_platforms = {p.strip("*") for p in buildx_builder.platforms}
        missing_platforms = platforms - buildx_platforms
        if missing_platforms:
            raise KDockerException(message=f"Missing platforms: {missing_platforms}. Please enable them in buildx.")

        docker_load = len(platforms) == 1
        docker_push = False
        if base_build_object.build_for_upload:
            docker_load = False
            docker_push = True
            if base_build_object.docker_registry:
                docker_image_name = base_build_object.docker_registry + "/" + docker_image_name

        docker_buildx.buildx.build(
            str(docker_build_context_path),
            build_args=build_args or {},
            cache=not base_build_object.fresh_build,
            file=str(dockerfile_path),
            labels=docker_image_labels,
            progress="auto",
            load=docker_load,
            push=docker_push,
            secrets=[],  # TODO: explore this
            tags=[docker_image_name],
            platforms=list(platforms),
            add_hosts=(
                {"host.docker.internal": "host-gateway"}
                if driver == "docker" and HOST_GATEWAY_SUPPORT_START <= version < HOST_GATEWAY_SUPPORT_END
                else {}
            ),
        )

        # Remove image from local registry for docker default driver
        if driver == "docker" and base_build_object.build_for_upload:
            try:
                self.remove_docker_image(docker_image_name=docker_image_name)
            except KDockerException:
                logger.info("Failed to remove upload image from local registry. Continuing...")

        return True

    @ensure_docker_is_running
    def ensure_docker_image_exists(self, docker_image: str) -> str:
        """
        Using the base logged client, ensure that the provided image is valid either in the currently logged registry
        or the in the public one (DockerHub).

        Parameters
        ----------
        docker_image : str
            the docker image to be checked and downloaded.

        Returns
        -------
        str
            a boolean indicating whether the images are valid in the currently logged registry or the public one.

        """
        image_exists_locally = self.check_if_docker_image_exists(docker_image_name=docker_image)
        if image_exists_locally:
            logger.debug(f'Application "{docker_image}" found on the local registry.')
            return docker_image
        else:
            image_name = DockerImageName.parse(docker_image)
            try:
                # 1 - Public registry
                return self.pull_docker_image_from_registry(
                    docker_image_name=image_name,
                )
            except NotFound:
                try:
                    # 2 - Logged registry
                    image_name.hostname = session_manager.get_docker_current_url()

                    return self.pull_docker_image_from_registry(
                        docker_image_name=image_name,
                    )
                except NotFound:
                    raise KDockerException("The provided image was not found in any registry.")

    @ensure_docker_is_running
    def pull_docker_image_from_registry(
        self,
        docker_image_name: DockerImageName,
        auth_config: Optional[dict] = None,
        tag_local_name: bool = False,
    ) -> str:
        """
        Pull the specified docker image from the currently logged registry.

        Parameters
        ----------
        docker_image_name : DockerImageName
            the name of the docker image to pull.
        auth_config : Optional[dict]
            if set, will indicate whether the pulled image should be pulled from a public registry.

        Returns
        -------
        str
            the name of the docker image pulled from the remote registry.

        """
        try:
            logger.info(f'Attempting to pull "{docker_image_name.repository_image_name}"')
            self._pull_docker_image(
                docker_image_name=docker_image_name,
                auth_config=auth_config,
            )

            image_final_name = docker_image_name.repository_image_name
            if tag_local_name:
                self._docker_client.tag(
                    docker_image_name.repository_image_name,
                    docker_image_name.name_with_version,
                )
                image_final_name = docker_image_name.name_with_version

            logger.relevant(f'"{image_final_name}" successfully downloaded to the local registry.')
            return docker_image_name.repository_image_name
        except DockerException:
            error_message: str = f'Unable to pull docker image "{docker_image_name.repository_image_name}"'
            logger.warning(error_message)
            raise NotFound(message=error_message)

    @ensure_docker_is_running
    def _pull_docker_image(self, docker_image_name: DockerImageName, auth_config: Optional[dict] = None) -> bool:
        """Pull the specified docker image from the provided docker image registry."""
        try:
            stream_contents = self._docker_client.pull(
                repository=docker_image_name.repository_image_name, auth_config=auth_config, stream=True
            )
            progress_successfully_displayed: bool = display_docker_progress(stream=stream_contents)

            logger.debug(f'Successfully pulled "{docker_image_name}"')

            return progress_successfully_displayed
        except NotFound as e:
            raise KSDKFatal(
                f"""\n
                The provided app is not available in the registry: \"{docker_image_name.repository_image_name}\". \n
                Please provide a valid combination of image and version. E.g \"hello-world:0.0.1\"
            """
            ) from e

    @ensure_docker_is_running
    def remove_docker_image(self, docker_image_name: str) -> bool:
        """
        Remove the specified docker image from the local system.

        Raise an exception if the docker image was not successfully removed.

        Parameters
        ----------
        docker_image_name : str
            the name of the docker image to be removed.

        Returns
        -------
        bool
            a boolean indicating whether the image was successfully removed.

        """
        # 1 - Find all docker images that match the provided argument
        matching_images = self.get_docker_images(image_names=[docker_image_name])

        if matching_images:
            for image in matching_images:
                # 2 - Stop the containers for the provided image
                self.stop_containers(image_names=image.tags)
                for tag in image.tags:
                    # 3 - attempt to remove the image
                    docker_image_was_removed = self._docker_client.remove_image(tag, force=True)
                    # 4 - transform the docker image result to a string
                    removed_result_str = str(docker_image_was_removed) if docker_image_was_removed else None
                    # 5 - verify if the success string is part of the result
                    docker_image_was_removed = removed_result_str is not None and tag in removed_result_str
                    if not docker_image_was_removed:
                        raise KDockerException(f'Error removing "{tag}"')
                    logger.info(f'Image "{tag}" successfully removed')
            return True
        else:
            logger.warning(f'Application "{docker_image_name}" not found on the local registry')
            return False

    @ensure_docker_is_running
    def prune_docker_images(self, filters: Optional[dict] = None) -> bool:
        """
        A simple wrapper around the client to prune dangling docker images.

        Parameters
        ----------
        filters : dict
            the keywords used to filter out the prune operation.

        Returns
        -------
        bool
             a bool indicating the images were successfully pruned.

        """
        try:
            self._docker_client.prune_images(filters=filters)
            logger.debug("Images successfully pruned")
            return True
        except Exception:
            raise KDockerException("Error pruning images")

    @ensure_docker_is_running
    def check_if_docker_image_exists(
        self, docker_image_name: str, silent: bool = False, raise_exception: bool = False
    ) -> bool:
        """
        Check whether the specified docker image exists on the local system.

        Parameters
        ----------
        docker_image_name : str
            the name of the docker image to be checked.
        silent : bool
            indicates whether logs should be displayed.
        raise_exception : bool
            indicates whether or not it should raise if the provided image is not found.

        Returns
        -------
        bool
            a boolean indicating whether the image exists on the local docker list.

        """
        docker_images = self.get_docker_images(image_names=[docker_image_name])
        image_exists = bool(docker_images)

        # 1 - log if set to
        if not silent:
            if image_exists:
                message = f'Image "{docker_image_name}" already exists'
            else:
                message = f'Image "{docker_image_name}" does not exist'
            logger.debug(message)

        # 2 - raise if set to
        if not image_exists and raise_exception:
            raise KDockerException(f'Provided application "{docker_image_name}" not found on the local registry')

        return image_exists

    @ensure_docker_is_running
    def extract_dir_from_docker_image(
        self,
        app_name: str,
        output_dir: str,
        container_dir: str = DockerConfigs.container_app_dir_path,
    ) -> bool:
        """
        Extract the content of the specified built application to the provided output directory.

        Parameters
        ----------
        app_name : str
            the name of the application to unpack.
        container_dir: str
            The directory to extract from the container.
        output_dir: str
            the output directory to output the extracted content.
        clean_dir : str
            clean the directory before extracting into it.

        Returns
        -------
            a boolean flag indicating the image was successfully unpacked.

        """
        # 1 - Setup the output dir
        default_unpack_app_name = DockerConfigs.default_unpack_app_name
        output_dir_path = KPath(output_dir)

        try:
            output_dir_path.raise_if_has_files()
        except Exception as exc:
            raise exc

        output_dir_path.create_dir()

        # 2 - Remove any existent default unpack container
        self.remove_container(container_name=default_unpack_app_name)

        # 3 - Create the dummy container of the image subject to extraction
        container = self._docker_client.create_container(
            image=app_name,
            stdin_open=True,
            name=default_unpack_app_name,
            entrypoint="tail",
            command=["-f", "/dev/null"],
        )
        container_object = DockerContainer(id=container.get("Id", ""), image_name=default_unpack_app_name)

        # 4 - Extract the contents
        app_folder_extracted: bool = self._extract_folder_from_container(
            container_id=container_object.id, container_dir=container_dir, output_dir=output_dir
        )

        # 5 - Remove the temporary container
        self._docker_client.remove_container(container=default_unpack_app_name)

        return app_folder_extracted

    def _extract_folder_from_container(self, container_id: str, container_dir: str, output_dir: str) -> bool:
        """
        Assist function to extract a folder from a container.

        Parameters
        ----------
        container_id : str
            the id of the container to extract
        container_dir : str
            the path of the directory to extract from the container
        output_dir : str
            the output directory into which the folder should be extracted

        Returns
        -------
        bool
            a boolean indicating whether the folder was successfully extracted.

        """
        try:
            unpack_temp_file: str = DockerConfigs.app_unpack_temp_file
            stream, stat = self._docker_client.get_archive(container=container_id, path=container_dir)
            with TemporaryDirectory(dir=OSInfo.temp_dir) as temp_dir:
                app_tar_file = KPath(temp_dir) / unpack_temp_file
                with open(app_tar_file, "wb") as f:
                    for item in stream:
                        f.write(item)
                with tarfile.TarFile(app_tar_file) as tf:
                    app_container_app_dir = DockerConfigs.app_container_app_dir
                    for member in tf.getmembers():
                        if member.name.startswith(f"{app_container_app_dir}/"):
                            member.name = str(KPath(member.name).relative_to(app_container_app_dir))
                    tf.extractall(
                        path=output_dir,
                        members=[
                            member
                            for member in tf.getmembers()
                            if not (member.name.startswith("/") or ".." in member.name) and member.isfile()
                        ],
                    )  # nosec

            return True
        except DockerException:
            return False

    # 5 - CONTAINERS
    @ensure_docker_is_running
    def get_docker_containers(
        self,
        target_all_containers: bool = False,
        image_names: Optional[List[str]] = None,
        container_names: Optional[List[str]] = None,
        labels: Optional[dict] = None,
    ) -> List[DockerContainer]:
        """
        Obtain a list of all docker containers available in the system.

        This image list can be narrowed down by using labels or an image name.
        By default, includes the standard: {'source': 'ksdk'} labels.

        Parameters
        ----------
        target_all_containers : bool
            if set to 'True', will target all containers, running or stopped alike.
        image_names : Optional[List[str]]
            the name of the docker image to filters the containers.
        container_names : Optional[List[str]]
            the name of the docker container to filter.
        labels : Optional[dict]
            the labels used to selectively get containers.

        Returns
        -------
        List[DockerContainer]
            a list of DockerContainer items.

        """
        docker_containers = self._docker_client.containers(all=target_all_containers)
        all_docker_containers: List[DockerContainer] = [
            DockerContainer.get_docker_container_object(raw_container_object=container)
            for container in docker_containers
        ]
        # 1 - If not filter is provided, yield back all the containers
        if not any([image_names, container_names, labels]):
            return all_docker_containers
        # 2 - Else, filter them
        else:
            containers_to_return: List[DockerContainer] = []
            provided_container_names: List[str] = container_names or []
            for container in all_docker_containers:
                # 2.1 - check if there is a match on containers
                internal_container_names: List[str] = container.container_names or []
                if bool(set(provided_container_names) & set(internal_container_names)):
                    containers_to_return.append(container)
                    continue
                # 2.2 - check if there is a match on images
                if image_names is not None and container.image_name in image_names:
                    containers_to_return.append(container)
                    continue
                # 2.3 - check if there is a match on labels
                if labels:
                    if "name" in labels:
                        labels.pop("name", "")
                    internal_container_labels: Dict[Any, Any] = container.labels or {}
                    if labels.items() <= internal_container_labels.items():
                        containers_to_return.append(container)
                        continue
            return containers_to_return

    @ensure_docker_is_running
    def stop_containers(
        self, container_names: Optional[List[str]] = None, image_names: Optional[List[str]] = None
    ) -> bool:
        """
        Internal function for stopping containers by either container name or image name.

        Parameters
        ----------
        container_names : Optional[List[str]]
            the name of the docker container to filter.
        image_names : Optional[List[str]]
            the name of the docker image to filters the containers.
        Returns
        -------
        bool
            a bool indicating whether the container(s) was(were) successfully stopped

        """
        # Prune containers before advancing
        matching_containers = self.get_docker_containers(container_names=container_names, image_names=image_names)
        running_containers = [container for container in matching_containers if container.running]

        if not running_containers:
            return False

        for container in running_containers:
            logger.info(f'Stopping containers "{", ".join(container.container_names)}" ({container.image_name})')
            self._docker_client.stop(container=container.id)

        return True

    @ensure_docker_is_running
    def remove_container(self, container_name: str) -> bool:
        """
        Remove the provided container from the system.

        Parameters
        ----------
        container_name : str
            the id of the container to be removed.

        Returns
        -------
        bool
            a default boolean indicating the container was successfully removed.

        """
        matching_containers = self.get_docker_containers(container_names=[container_name], target_all_containers=True)
        for container in matching_containers:
            for container_name in container.container_names:
                self._docker_client.remove_container(container=container_name, force=True)
                logger.debug(f'Container "{container_name}" successfully removed')
        return True

    @ensure_docker_is_running
    def prune_docker_containers(self, filters: Optional[dict] = None) -> bool:
        """
        A simple wrapper around the client to prune dangling docker containers.

        Parameters
        ----------
        filters : dict
            the keywords used to filter out the prune operation.

        Returns
        -------
        bool
            a symbolic return flag.

        """
        try:
            self._docker_client.prune_containers(filters=filters)
            logger.debug("Containers successfully pruned")
            return True
        except (DockerException, Exception):
            raise KDockerException("Error pruning docker containers. Proceeding.")


def get_docker_manager() -> DockerManager:
    return DockerManager()
