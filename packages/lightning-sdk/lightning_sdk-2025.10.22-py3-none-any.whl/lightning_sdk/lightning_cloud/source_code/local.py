from contextlib import contextmanager
import os
from pathlib import Path
from shutil import rmtree
from typing import Optional, List

from lightning_sdk.lightning_cloud.source_code.copytree import copytree
from lightning_sdk.lightning_cloud.source_code.hashing import get_hash
from lightning_sdk.lightning_cloud.source_code.tar import tar_path
from lightning_sdk.lightning_cloud.source_code.uploader import FileUploader


class LocalSourceCodeDir:
    """Represents the source code directory and provide the utilities to manage it"""
    cache_location: Path = Path.home(
    ) / ".lightning" / "cache" / "repositories"

    def __init__(self, path: Path):
        self.path = path

        # cache checksum version
        self._version: Optional[str] = None
        self._non_ignored_files: Optional[List[str]] = None

        # create global cache location if it doesn't exist
        if not self.cache_location.exists():
            self.cache_location.mkdir(parents=True, exist_ok=True)

        # clean old cache entries
        self._prune_cache()

    @property
    def files(self) -> List[str]:
        """
        Returns a set of files that are not ignored by .lightningignore.
        """
        if self._non_ignored_files is None:
            self._non_ignored_files = copytree(self.path, "", dry_run=True)
        return self._non_ignored_files

    @property
    def version(self):
        """
        Calculates the checksum of a local path.
        """
        # cache value to prevent doing this over again
        if self._version is not None:
            return self._version

        # stores both version and a set with the files used to generate the checksum
        self._version = get_hash(files=self.files, algorithm="blake2")
        return self._version

    @property
    def package_path(self):
        """Location to tarball in local cache."""
        filename = f"{self.version}.tar.gz"
        return self.cache_location / filename

    @contextmanager
    def packaging_session(self) -> Path:
        """Creates a local directory with source code that is used for creating a local source-code package."""
        session_path = self.cache_location / "packaging_sessions" / self.version
        try:
            rmtree(session_path, ignore_errors=True)
            copytree(self.path, session_path)
            yield session_path
        finally:
            rmtree(session_path, ignore_errors=True)

    def _prune_cache(self) -> None:
        """Prunes cache; only keeps the 10 most recent items."""
        packages = sorted(self.cache_location.iterdir(), key=os.path.getmtime)
        for package in packages[10:]:
            if package.is_file():
                package.unlink()

    def package(self) -> Path:
        """Packages local path using tar."""
        if self.package_path.exists():
            return self.package_path
        # create a packaging session if not available
        with self.packaging_session() as session_path:
            tar_path(source_path=session_path,
                     target_file=str(self.package_path),
                     compression=True)
        return self.package_path

    def upload(self, url: str) -> None:
        """Uploads package to URL, usually pre-signed URL.

        Notes
        -----
        Since we do not use multipart uploads here, we cannot upload any
        packaged repository files which have a size > 2GB.

        This limitation should be removed during the datastore upload redesign
        """
        if self.package_path.stat().st_size > 2e9:
            raise OSError(
                "cannot upload directory code whose total fize size is greater than 2GB (2e9 bytes)"
            ) from None
        uploader = FileUploader(presigned_url=url,
                                source_file=str(self.package_path),
                                name=self.package_path.name,
                                total_size=self.package_path.stat().st_size)
        uploader.upload()
