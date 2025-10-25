import os
import tempfile

from docker.models.images import Image

from svs_core.docker.base import get_docker_client
from svs_core.shared.logger import get_logger


class DockerImageManager:
    """Class for managing Docker images."""

    @staticmethod
    def build_from_dockerfile(
        image_name: str,
        dockerfile_content: str,
        tag: str = "latest",
    ) -> None:
        """Build a Docker image from an in-memory Dockerfile.

        Args:
            image_name (str): Name of the image.
            dockerfile_content (str): Dockerfile contents.
            tag (str): Image tag.
        """
        client = get_docker_client()

        get_logger(__name__).debug(f"Building image {image_name}:{tag} from Dockerfile")

        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = os.path.join(tmpdir, "Dockerfile")
            with open(dockerfile_path, "w", encoding="utf-8") as f:
                f.write(dockerfile_content)

            client.images.build(
                path=tmpdir,
                tag=f"{image_name}:{tag}",
                rm=True,
                forcerm=True,
                labels={"svs": "true"},
            )

    @staticmethod
    def exists(image_name: str, tag: str = "latest") -> bool:
        """Check if a Docker image exists locally.

        Args:
            image_name (str): Name of the image.
            tag (str): Image tag.

        Returns:
            bool: True if the image exists, False otherwise.
        """
        client = get_docker_client()
        try:
            client.images.get(f"{image_name}:{tag}")
            return True
        except Exception:
            return False

    @staticmethod
    def remove(image_name: str, tag: str = "latest") -> None:
        """Remove a Docker image from the local system.

        Args:
            image_name (str): Name of the image.
            tag (str): Image tag.

        Raises:
            Exception: If the image cannot be removed.
        """
        client = get_docker_client()

        get_logger(__name__).debug(f"Removing image {image_name}:{tag}")

        try:
            client.images.remove(f"{image_name}:{tag}", force=True)
        except Exception as e:
            raise Exception(
                f"Failed to remove image {image_name}:{tag}. Error: {str(e)}"
            ) from e

    @staticmethod
    def pull(image_name: str, tag: str = "latest") -> None:
        """Pull a Docker image from a registry.

        Args:
            image_name (str): Name of the image.
            tag (str): Image tag.
        """
        client = get_docker_client()

        get_logger(__name__).debug(f"Pulling image {image_name}:{tag}")

        try:
            client.images.pull(f"{image_name}:{tag}")
        except Exception as e:
            raise Exception(
                f"Failed to pull image {image_name}:{tag}. Error: {str(e)}"
            ) from e

    @staticmethod
    def get_all() -> list[Image]:
        """Get a list of all local Docker images.

        Returns:
            list[Image]: List of Docker Image objects.
        """
        client = get_docker_client()
        return client.images.list()  # type: ignore
