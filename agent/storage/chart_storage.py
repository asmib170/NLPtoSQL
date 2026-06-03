"""Abstract interface and implementations for chart image storage.

Implementations:
  - LocalChartStorage: saves to local filesystem (development)
  - S3ChartStorage: saves to S3 with CloudFront URL (production) — to be implemented
"""

import os
import time
from abc import ABC, abstractmethod
from pathlib import Path


class ChartStorage(ABC):
    """Abstract interface for storing and retrieving chart images.

    Implementations must handle:
      - Saving a PNG file and returning a URL/path to access it
      - Retrieving the file content for serving
      - Checking if a chart exists
      - Deleting old charts (TTL cleanup)
    """

    @abstractmethod
    def save(self, filename: str, data: bytes) -> str:
        """Save chart image data. Returns the URL/path to access it.

        Args:
            filename: The filename (e.g. "chart_123456.png")
            data: The raw PNG bytes

        Returns:
            The URL or path where the chart can be accessed
        """
        ...

    @abstractmethod
    def get_path(self, filename: str) -> str | None:
        """Get the local file path for a chart (for serving via FileResponse).

        Returns None if the chart doesn't exist or if storage is remote (use get_url instead).
        """
        ...

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """Get the URL to access a chart image.

        For local storage: /api/charts/{filename}
        For S3+CloudFront: https://d1234.cloudfront.net/charts/{filename}
        """
        ...

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """Check if a chart file exists."""
        ...

    @abstractmethod
    def get_save_path(self, filename: str) -> str:
        """Get the full path where a chart should be saved.

        Used by the chart generation code to know where to write the file.
        For local: returns a filesystem path
        For S3: returns a temp path (file is uploaded after generation)
        """
        ...

    @abstractmethod
    def cleanup(self, ttl_days: int) -> int:
        """Delete charts older than ttl_days. Returns count of deleted files."""
        ...


class LocalChartStorage(ChartStorage):
    """Store charts on the local filesystem.

    Charts are saved as PNG files in the configured directory (default: data/charts/).
    Suitable for local development; swap to S3ChartStorage for production.
    """

    def __init__(self, directory: str = ""):
        """Initialize local chart storage.

        Args:
            directory: Path to the directory for chart files.
                       Defaults to agent/data/charts/.
        """
        if not directory:
            from utils import CHARTS_DIR
            directory = CHARTS_DIR
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, data: bytes) -> str:
        filepath = self._directory / filename
        filepath.write_bytes(data)
        return f"/api/charts/{filename}"

    def get_path(self, filename: str) -> str | None:
        filepath = self._directory / filename
        if filepath.exists():
            return str(filepath)
        return None

    def get_url(self, filename: str) -> str:
        return f"/api/charts/{filename}"

    def exists(self, filename: str) -> bool:
        return (self._directory / filename).exists()

    def get_save_path(self, filename: str) -> str:
        return str(self._directory / filename)

    def cleanup(self, ttl_days: int) -> int:
        deleted = 0
        cutoff = time.time() - (ttl_days * 86400)
        for f in self._directory.iterdir():
            if f.is_file() and f.suffix == ".png" and os.path.getmtime(f) < cutoff:
                f.unlink()
                deleted += 1
        return deleted


# class S3ChartStorage(ChartStorage):
#     """Store charts in S3 with CloudFront distribution. For production.
#
#     def __init__(self, bucket: str, prefix: str = "charts/", cloudfront_domain: str = ""):
#         self._bucket = bucket
#         self._prefix = prefix
#         self._cloudfront_domain = cloudfront_domain
#         self._s3 = boto3.client("s3")
#
#     def save(self, filename: str, data: bytes) -> str:
#         key = f"{self._prefix}{filename}"
#         self._s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType="image/png")
#         return self.get_url(filename)
#
#     def get_path(self, filename: str) -> str | None:
#         return None  # Remote storage — use get_url instead
#
#     def get_url(self, filename: str) -> str:
#         if self._cloudfront_domain:
#             return f"https://{self._cloudfront_domain}/{self._prefix}{filename}"
#         return f"https://{self._bucket}.s3.amazonaws.com/{self._prefix}{filename}"
#
#     def exists(self, filename: str) -> bool:
#         try:
#             self._s3.head_object(Bucket=self._bucket, Key=f"{self._prefix}{filename}")
#             return True
#         except self._s3.exceptions.ClientError:
#             return False
#
#     def get_save_path(self, filename: str) -> str:
#         # Save to temp, then upload in save()
#         import tempfile
#         return os.path.join(tempfile.gettempdir(), filename)
#
#     def cleanup(self, ttl_days: int) -> int:
#         # Use S3 lifecycle rules instead — more efficient
#         return 0
#     """
#     pass
