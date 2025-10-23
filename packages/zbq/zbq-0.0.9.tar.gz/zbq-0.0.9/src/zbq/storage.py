from typing import List, Dict, Optional, Union, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from polars.exceptions import PolarsError
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from zbq.base import ZbqOperationError, BaseClientManager
from dataclasses import dataclass
from pathlib import Path
from tqdm import tqdm
import os
import fnmatch
import re
import time
import polars as pl
import io


@dataclass
class UploadResult:
    """Result of upload operations"""

    total_files: int
    uploaded_files: int
    skipped_files: int
    failed_files: int
    total_bytes: int
    duration: float
    errors: List[str]


@dataclass
class DownloadResult:
    """Result of download operations"""

    total_files: int
    downloaded_files: int
    failed_files: int
    total_bytes: int
    duration: float
    errors: List[str]


@dataclass
class ReadResult:
    """Result of read operations"""

    total_files: int
    read_files: int
    failed_files: int
    total_bytes: int
    total_rows: int
    duration: float
    errors: List[str]


class ProgressBarWrapper:
    """Wrapper for combining tqdm progress bar with custom callbacks"""

    def __init__(
        self,
        total: int,
        show_progress: bool = True,
        description: str = "Processing",
        unit: str = "files",
        custom_callback: Optional[Callable[[int, int], None]] = None,
    ):
        self.total = total
        self.show_progress = show_progress
        self.custom_callback = custom_callback
        self.completed = 0

        if self.show_progress and total > 1:  # Only show for multiple files
            self.pbar = tqdm(
                total=total,
                desc=description,
                unit=unit,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            )
        else:
            self.pbar = None

    def update(self, completed: int, total: int):
        """Update progress bar and call custom callback"""
        self.completed = completed

        if self.pbar:
            # Update progress bar to current completion
            self.pbar.n = completed
            self.pbar.refresh()

        if self.custom_callback:
            self.custom_callback(completed, total)

    def close(self):
        """Close progress bar"""
        if self.pbar:
            self.pbar.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class StorageHandler(BaseClientManager):
    """Enhanced Google Cloud Storage handler with pattern matching and progress tracking"""

    def __init__(
        self, project_id: str = "", log_level: str = "INFO", max_workers: int = 4
    ):
        super().__init__(project_id, log_level)
        self.max_workers = max_workers

    def upload(
        self,
        local_dir: str | Path,
        bucket_path: str,
        include_patterns: Optional[Union[str, List[str]]] = None,
        exclude_patterns: Optional[Union[str, List[str]]] = None,
        case_sensitive: bool = True,
        use_regex: bool = False,
        dry_run: bool = False,
        parallel: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        show_progress: Optional[bool] = None,  # Auto-detect if None
        max_retries: int = 3,
    ) -> UploadResult:
        """
        Upload files or a single file to Google Cloud Storage bucket with enhanced pattern matching

        Args:
            local_dir: Local directory path OR single file path to upload from
            bucket_path: GCS bucket path (e.g., "my-bucket" or "my-bucket/folder/subfolder")
            include_patterns: Pattern(s) to include (e.g., "*.xlsx", ["*.csv", "*.json"]) - ignored for single files
            exclude_patterns: Pattern(s) to exclude (e.g., "temp_*", ["*.tmp", "*.log"]) - ignored for single files
            case_sensitive: Whether pattern matching is case sensitive - ignored for single files
            use_regex: Use regex patterns instead of glob patterns - ignored for single files
            dry_run: Preview operation without actual upload
            parallel: Use parallel uploads for better performance - ignored for single files
            progress_callback: Optional callback function for progress updates
            show_progress: Show progress bar (None=auto-detect, True=always, False=never)
            max_retries: Number of retry attempts for failed uploads

        Returns:
            UploadResult with detailed statistics
        """

        # Parse bucket path into bucket name and prefix
        bucket_name, prefix = self.parse_bucket_path(bucket_path)

        start_time = time.time()
        local_path = Path(local_dir)

        if not local_path.exists():
            raise ZbqOperationError(f"Local path does not exist: {local_dir}")

        # Handle single file upload
        if local_path.is_file():
            self.logger.info(f"Single file detected: {local_dir}")
            return self.upload_file(
                local_file_path=local_path,
                bucket_path=bucket_path,
                max_retries=max_retries,
            )

        # Handle directory upload
        self.logger.info(f"Starting upload from {local_dir} to {bucket_path}")

        # Collect files to upload
        files_to_upload = []
        total_bytes = 0

        for root, _, files in os.walk(local_dir):
            for file in files:
                if self.match_patterns(
                    file, include_patterns, exclude_patterns, case_sensitive, use_regex
                ):
                    local_file_path = Path(root) / file
                    relative_path = local_file_path.relative_to(local_path)
                    file_size = local_file_path.stat().st_size

                    # Prepend prefix to blob path if specified
                    blob_path = (
                        f"{prefix}{relative_path}" if prefix else str(relative_path)
                    )

                    files_to_upload.append(
                        {
                            "local_path": local_file_path,
                            "blob_path": blob_path,
                            "size": file_size,
                        }
                    )
                    total_bytes += file_size

        result = UploadResult(
            total_files=len(files_to_upload),
            uploaded_files=0,
            skipped_files=0,
            failed_files=0,
            total_bytes=total_bytes,
            duration=0.0,
            errors=[],
        )

        if dry_run:
            self.logger.info(
                f"DRY RUN: Would upload {len(files_to_upload)} files ({total_bytes:,} bytes)"
            )
            for file_info in files_to_upload:
                self.logger.info(
                    f"  Would upload: {file_info['blob_path']} ({file_info['size']:,} bytes)"
                )
            result.duration = time.time() - start_time
            return result

        if not files_to_upload:
            self.logger.info("No files found matching the specified patterns")
            result.duration = time.time() - start_time
            return result

        # Auto-detect progress bar display
        if show_progress is None:
            show_progress = len(files_to_upload) > 1 and not dry_run

        # Upload files with progress tracking
        with ProgressBarWrapper(
            total=len(files_to_upload),
            show_progress=show_progress,
            description="Uploading",
            custom_callback=progress_callback,
        ) as progress:
            if parallel and len(files_to_upload) > 1:
                result = self._upload_parallel(
                    bucket_name, files_to_upload, result, progress.update, max_retries
                )
            else:
                result = self._upload_sequential(
                    bucket_name, files_to_upload, result, progress.update, max_retries
                )

        result.duration = time.time() - start_time
        self.logger.info(
            f"Upload completed: {result.uploaded_files}/{result.total_files} files "
            f"in {result.duration:.2f}s"
        )

        return result

    def match_patterns(
        self,
        filename: str,
        include_patterns: Optional[Union[str, List[str]]] = None,
        exclude_patterns: Optional[Union[str, List[str]]] = None,
        case_sensitive: bool = True,
        use_regex: bool = False,
    ) -> bool:
        """
        Check if filename matches include patterns and doesn't match exclude patterns

        Args:
            filename: Name of file to check
            include_patterns: Pattern(s) to include (None means include all)
            exclude_patterns: Pattern(s) to exclude (None means exclude none)
            case_sensitive: Whether pattern matching is case sensitive
            use_regex: Whether to use regex instead of glob patterns

        Returns:
            True if file should be processed, False otherwise
        """
        if not case_sensitive:
            filename = filename.lower()

        # Convert single patterns to lists
        if isinstance(include_patterns, str):
            include_patterns = [include_patterns]
        if isinstance(exclude_patterns, str):
            exclude_patterns = [exclude_patterns]

        # Apply case insensitivity to patterns
        if not case_sensitive:
            if include_patterns:
                include_patterns = [p.lower() for p in include_patterns]
            if exclude_patterns:
                exclude_patterns = [p.lower() for p in exclude_patterns]

        # Check include patterns
        if include_patterns:
            included = False
            for pattern in include_patterns:
                if use_regex:
                    if re.match(pattern, filename):
                        included = True
                        break
                else:
                    if fnmatch.fnmatch(filename, pattern):
                        included = True
                        break
            if not included:
                return False

        # Check exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                if use_regex:
                    if re.match(pattern, filename):
                        return False
                else:
                    if fnmatch.fnmatch(filename, pattern):
                        return False

        return True

    def retry_operation(
        self,
        operation: Callable,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> Any:
        """Retry an operation with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay * (backoff_factor**attempt))
        return None

    def _upload_sequential(
        self,
        bucket_name: str,
        files_to_upload: List[Dict],
        result: UploadResult,
        progress_callback: Optional[Callable],
        max_retries: int,
    ) -> UploadResult:
        """Upload files sequentially"""
        with self._fresh_client() as client:
            bucket = client.bucket(bucket_name)

            for i, file_info in enumerate(files_to_upload):
                try:

                    def upload_operation():
                        blob = bucket.blob(file_info["blob_path"])
                        blob.upload_from_filename(str(file_info["local_path"]))
                        return True

                    self.retry_operation(upload_operation, max_retries)
                    result.uploaded_files += 1
                    self.logger.debug(f"Uploaded: {file_info['blob_path']}")

                except Exception as e:
                    result.failed_files += 1
                    error_msg = f"Failed to upload {file_info['blob_path']}: {str(e)}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)

                if progress_callback:
                    progress_callback(i + 1, len(files_to_upload))

        return result

    def parse_bucket_path(self, bucket_path: str) -> tuple[str, str]:
        """
        Parse a bucket path into bucket name and prefix

        Args:
            bucket_path: Either "bucket-name" or "bucket-name/path/to/folder"

        Returns:
            Tuple of (bucket_name, prefix)

        Examples:
            "my-bucket" -> ("my-bucket", "")
            "my-bucket/folder" -> ("my-bucket", "folder/")
            "my-bucket/path/to/folder" -> ("my-bucket", "path/to/folder/")
        """
        # Remove gs:// prefix if present
        if bucket_path.startswith("gs://"):
            bucket_path = bucket_path[5:]

        # Split into parts
        parts = bucket_path.split("/", 1)
        bucket_name = parts[0]

        if len(parts) > 1 and parts[1]:
            # Ensure prefix ends with /
            prefix = parts[1]
            if not prefix.endswith("/"):
                prefix += "/"
        else:
            prefix = ""

        return bucket_name, prefix

    def _upload_parallel(
        self,
        bucket_name: str,
        files_to_upload: List[Dict],
        result: UploadResult,
        progress_callback: Optional[Callable],
        max_retries: int,
    ) -> UploadResult:
        """Upload files in parallel using ThreadPoolExecutor"""
        completed_files = 0

        def upload_file(file_info):
            try:
                with self._fresh_client() as client:
                    bucket = client.bucket(bucket_name)

                    def upload_operation():
                        blob = bucket.blob(file_info["blob_path"])
                        blob.upload_from_filename(str(file_info["local_path"]))
                        return True

                    self.retry_operation(upload_operation, max_retries)
                    return {"success": True, "file_info": file_info, "error": None}

            except Exception as e:
                return {"success": False, "file_info": file_info, "error": str(e)}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(upload_file, file_info): file_info
                for file_info in files_to_upload
            }

            for future in as_completed(future_to_file):
                upload_result = future.result()
                completed_files += 1

                if upload_result["success"]:
                    result.uploaded_files += 1
                    self.logger.debug(
                        f"Uploaded: {upload_result['file_info']['blob_path']}"
                    )
                else:
                    result.failed_files += 1
                    error_msg = f"Failed to upload {upload_result['file_info']['blob_path']}: {upload_result['error']}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)

                if progress_callback:
                    progress_callback(completed_files, len(files_to_upload))

        return result

    def download(
        self,
        bucket_path: str,
        local_dir: str,
        include_patterns: Optional[Union[str, List[str]]] = None,
        exclude_patterns: Optional[Union[str, List[str]]] = None,
        case_sensitive: bool = True,
        use_regex: bool = False,
        dry_run: bool = False,
        parallel: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        show_progress: Optional[bool] = None,  # Auto-detect if None
        max_retries: int = 3,
        max_results: int = 1000,
    ) -> DownloadResult:
        """
        Download files from Google Cloud Storage bucket with enhanced pattern matching

        Args:
            bucket_path: GCS bucket path (e.g., "my-bucket" or "my-bucket/folder/subfolder")
            local_dir: Local directory to download files to
            include_patterns: Pattern(s) to include (e.g., "*.xlsx", ["*.csv", "*.json"])
            exclude_patterns: Pattern(s) to exclude (e.g., "temp_*", ["*.tmp", "*.log"])
            case_sensitive: Whether pattern matching is case sensitive
            use_regex: Use regex patterns instead of glob patterns
            dry_run: Preview operation without actual download
            parallel: Use parallel downloads for better performance
            progress_callback: Optional callback function for progress updates
            show_progress: Show progress bar (None=auto-detect, True=always, False=never)
            max_retries: Number of retry attempts for failed downloads
            max_results: Maximum number of blobs to list from bucket

        Returns:
            DownloadResult with detailed statistics
        """
        # Parse bucket path
        bucket_name, combined_prefix = self.parse_bucket_path(bucket_path)

        start_time = time.time()
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Starting download from {bucket_path} to {local_dir}")

        # List and filter blobs
        blobs_to_download = []
        total_bytes = 0

        with self._fresh_client() as client:
            bucket = client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=combined_prefix, max_results=max_results)

            for blob in blobs:
                if not blob.name or blob.name.endswith("/"):
                    continue  # Skip directory markers

                blob_filename = Path(blob.name).name
                if self.match_patterns(
                    blob_filename,
                    include_patterns,
                    exclude_patterns,
                    case_sensitive,
                    use_regex,
                ):
                    relative_path = (
                        blob.name[len(combined_prefix) :]
                        if combined_prefix
                        else blob.name
                    )
                    local_file_path = local_path / relative_path

                    blobs_to_download.append(
                        {
                            "blob": blob,
                            "local_path": local_file_path,
                            "size": blob.size or 0,
                        }
                    )
                    total_bytes += blob.size or 0

        result = DownloadResult(
            total_files=len(blobs_to_download),
            downloaded_files=0,
            failed_files=0,
            total_bytes=total_bytes,
            duration=0.0,
            errors=[],
        )

        if dry_run:
            self.logger.info(
                f"DRY RUN: Would download {len(blobs_to_download)} files ({total_bytes:,} bytes)"
            )
            for blob_info in blobs_to_download:
                self.logger.info(
                    f"  Would download: {blob_info['blob'].name} -> {blob_info['local_path']}"
                )
            result.duration = time.time() - start_time
            return result

        if not blobs_to_download:
            self.logger.info("No files found matching the specified patterns")
            result.duration = time.time() - start_time
            return result

        # Auto-detect progress bar display
        if show_progress is None:
            show_progress = len(blobs_to_download) > 1 and not dry_run

        # Download files with progress tracking
        with ProgressBarWrapper(
            total=len(blobs_to_download),
            show_progress=show_progress,
            description="Downloading",
            custom_callback=progress_callback,
        ) as progress:
            if parallel and len(blobs_to_download) > 1:
                result = self._download_parallel(
                    blobs_to_download, result, progress.update, max_retries
                )
            else:
                result = self._download_sequential(
                    blobs_to_download, result, progress.update, max_retries
                )

        result.duration = time.time() - start_time
        self.logger.info(
            f"Download completed: {result.downloaded_files}/{result.total_files} files "
            f"in {result.duration:.2f}s"
        )

        return result

    def _download_sequential(
        self,
        blobs_to_download: List[Dict],
        result: DownloadResult,
        progress_callback: Optional[Callable],
        max_retries: int,
    ) -> DownloadResult:
        """Download files sequentially"""
        for i, blob_info in enumerate(blobs_to_download):
            try:
                # Ensure directory exists
                blob_info["local_path"].parent.mkdir(parents=True, exist_ok=True)

                def download_operation():
                    blob_info["blob"].download_to_filename(str(blob_info["local_path"]))
                    return True

                self.retry_operation(download_operation, max_retries)
                result.downloaded_files += 1
                self.logger.debug(f"Downloaded: {blob_info['blob'].name}")

            except Exception as e:
                result.failed_files += 1
                error_msg = f"Failed to download {blob_info['blob'].name}: {str(e)}"
                result.errors.append(error_msg)
                self.logger.error(error_msg)

            if progress_callback:
                progress_callback(i + 1, len(blobs_to_download))

        return result

    def _download_parallel(
        self,
        blobs_to_download: List[Dict],
        result: DownloadResult,
        progress_callback: Optional[Callable],
        max_retries: int,
    ) -> DownloadResult:
        """Download files in parallel using ThreadPoolExecutor"""
        completed_files = 0

        def download_file(blob_info):
            try:
                # Ensure directory exists
                blob_info["local_path"].parent.mkdir(parents=True, exist_ok=True)

                def download_operation():
                    blob_info["blob"].download_to_filename(str(blob_info["local_path"]))
                    return True

                self.retry_operation(download_operation, max_retries)
                return {"success": True, "blob_info": blob_info, "error": None}

            except Exception as e:
                return {"success": False, "blob_info": blob_info, "error": str(e)}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_blob = {
                executor.submit(download_file, blob_info): blob_info
                for blob_info in blobs_to_download
            }

            for future in as_completed(future_to_blob):
                download_result = future.result()
                completed_files += 1

                if download_result["success"]:
                    result.downloaded_files += 1
                    self.logger.debug(
                        f"Downloaded: {download_result['blob_info']['blob'].name}"
                    )
                else:
                    result.failed_files += 1
                    error_msg = f"Failed to download {download_result['blob_info']['blob'].name}: {download_result['error']}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)

                if progress_callback:
                    progress_callback(completed_files, len(blobs_to_download))

        return result

    def upload_file(
        self,
        local_file_path: str | Path,
        bucket_path: str,
        blob_name: Optional[str] = None,
        max_retries: int = 3,
    ) -> UploadResult:
        """
        Upload a single file to Google Cloud Storage bucket
        
        Args:
            local_file_path: Path to the local file to upload
            bucket_path: GCS bucket path (e.g., "my-bucket" or "my-bucket/folder/")
            blob_name: Optional custom name for the blob (defaults to filename)
            max_retries: Number of retry attempts for failed upload
            
        Returns:
            UploadResult with upload statistics
        """
        start_time = time.time()
        local_path = Path(local_file_path)
        
        if not local_path.exists():
            raise ZbqOperationError(f"File does not exist: {local_file_path}")
            
        if not local_path.is_file():
            raise ZbqOperationError(f"Path is not a file: {local_file_path}")
        
        # Parse bucket path
        bucket_name, prefix = self.parse_bucket_path(bucket_path)
        
        # Determine blob name
        if blob_name is None:
            blob_name = local_path.name
            
        # Construct full blob path
        blob_path = f"{prefix}{blob_name}" if prefix else blob_name
        
        file_size = local_path.stat().st_size
        
        result = UploadResult(
            total_files=1,
            uploaded_files=0,
            skipped_files=0,
            failed_files=0,
            total_bytes=file_size,
            duration=0.0,
            errors=[],
        )
        
        self.logger.info(f"Uploading single file {local_file_path} to {bucket_path}")
        
        try:
            with self._fresh_client() as client:
                bucket = client.bucket(bucket_name)
                
                def upload_operation():
                    blob = bucket.blob(blob_path)
                    blob.upload_from_filename(str(local_path))
                    return True
                
                self.retry_operation(upload_operation, max_retries)
                result.uploaded_files = 1
                self.logger.info(f"Successfully uploaded: {blob_path}")
                
        except Exception as e:
            result.failed_files = 1
            error_msg = f"Failed to upload {local_file_path}: {str(e)}"
            result.errors.append(error_msg)
            self.logger.error(error_msg)
        
        result.duration = time.time() - start_time
        return result

    def read(
        self,
        bucket_path: str,
        include_patterns: Optional[Union[str, List[str]]] = None,
        exclude_patterns: Optional[Union[str, List[str]]] = None,
        case_sensitive: bool = True,
        use_regex: bool = False,
        file_format: str = "auto",
        parallel: bool = True,
        add_source_column: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        show_progress: Optional[bool] = None,
        max_retries: int = 3,
        max_results: int = 1000,
        **reader_options,
    ) -> pl.DataFrame:
        """
        Read files from Google Cloud Storage bucket into a Polars DataFrame

        Args:
            bucket_path: GCS bucket path (e.g., "my-bucket" or "my-bucket/folder/subfolder")
            include_patterns: Pattern(s) to include (e.g., "*.csv", ["*.csv", "*.json"])
            exclude_patterns: Pattern(s) to exclude (e.g., "temp_*", ["*.tmp", "*.log"])
            case_sensitive: Whether pattern matching is case sensitive
            use_regex: Use regex patterns instead of glob patterns
            file_format: File format - "auto" (auto-detect), "csv", "parquet", "json", "ndjson"
            parallel: Use parallel reading for better performance
            add_source_column: Add a column with the source file name
            progress_callback: Optional callback function for progress updates
            show_progress: Show progress bar (None=auto-detect, True=always, False=never)
            max_retries: Number of retry attempts for failed reads
            max_results: Maximum number of blobs to list from bucket
            **reader_options: Additional options to pass to Polars read functions
                             (e.g., separator=";", has_header=True, infer_schema_length=100)

        Returns:
            pl.DataFrame: Combined DataFrame from all matching files

        Raises:
            ZbqOperationError: If read operation fails

        Example:
            # Read all CSV files from a bucket
            df = zstorage.read("my-bucket/data", include_patterns="*.csv")

            # Read with custom CSV options
            df = zstorage.read(
                "my-bucket/data",
                include_patterns="*.csv",
                separator=";",
                has_header=True
            )

            # Read Parquet files with source tracking
            df = zstorage.read(
                "my-bucket/data",
                include_patterns="*.parquet",
                add_source_column=True
            )
        """
        # Parse bucket path
        bucket_name, combined_prefix = self.parse_bucket_path(bucket_path)

        start_time = time.time()

        self.logger.info(f"Starting read from {bucket_path}")

        # List and filter blobs
        blobs_to_read = []
        total_bytes = 0

        with self._fresh_client() as client:
            bucket = client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=combined_prefix, max_results=max_results)

            for blob in blobs:
                if not blob.name or blob.name.endswith("/"):
                    continue  # Skip directory markers

                blob_filename = Path(blob.name).name
                if self.match_patterns(
                    blob_filename,
                    include_patterns,
                    exclude_patterns,
                    case_sensitive,
                    use_regex,
                ):
                    blobs_to_read.append(
                        {
                            "blob": blob,
                            "name": blob.name,
                            "filename": blob_filename,
                            "size": blob.size or 0,
                        }
                    )
                    total_bytes += blob.size or 0

        if not blobs_to_read:
            self.logger.info("No files found matching the specified patterns")
            return pl.DataFrame()

        # Auto-detect progress bar display
        if show_progress is None:
            show_progress = len(blobs_to_read) > 1

        # Read files with progress tracking
        dataframes = []
        read_files = 0
        failed_files = 0
        errors = []
        total_rows = 0

        with ProgressBarWrapper(
            total=len(blobs_to_read),
            show_progress=show_progress,
            description="Reading",
            custom_callback=progress_callback,
        ) as progress:
            if parallel and len(blobs_to_read) > 1:
                dataframes, read_files, failed_files, errors, total_rows = (
                    self._read_parallel(
                        blobs_to_read,
                        file_format,
                        add_source_column,
                        progress.update,
                        max_retries,
                        reader_options,
                    )
                )
            else:
                dataframes, read_files, failed_files, errors, total_rows = (
                    self._read_sequential(
                        blobs_to_read,
                        file_format,
                        add_source_column,
                        progress.update,
                        max_retries,
                        reader_options,
                    )
                )

        duration = time.time() - start_time

        # Combine all dataframes
        if not dataframes:
            self.logger.warning("No data successfully read from files")
            return pl.DataFrame()

        try:
            # Use concat with how="diagonal" to handle schema differences
            combined_df = pl.concat(dataframes, how="diagonal")

            self.logger.info(
                f"Read completed: {read_files}/{len(blobs_to_read)} files, "
                f"{total_rows:,} rows in {duration:.2f}s"
            )

            if errors:
                self.logger.warning(f"Encountered {len(errors)} errors during read")
                for error in errors[:5]:  # Show first 5 errors
                    self.logger.warning(f"  {error}")

            return combined_df

        except Exception as e:
            raise ZbqOperationError(f"Failed to combine dataframes: {str(e)}")

    def _detect_file_format(self, filename: str, specified_format: str) -> str:
        """Detect file format from filename or use specified format"""
        if specified_format != "auto":
            return specified_format.lower()

        # Detect from extension
        ext = Path(filename).suffix.lower()
        format_map = {
            ".csv": "csv",
            ".parquet": "parquet",
            ".pq": "parquet",
            ".json": "json",
            ".jsonl": "ndjson",
            ".ndjson": "ndjson",
        }

        detected = format_map.get(ext)
        if not detected:
            raise ZbqOperationError(
                f"Cannot auto-detect format for {filename}. "
                f"Please specify file_format explicitly."
            )

        return detected

    def _read_blob_to_dataframe(
        self,
        blob_info: Dict,
        file_format: str,
        add_source_column: bool,
        max_retries: int,
        reader_options: Dict,
    ) -> pl.DataFrame:
        """Read a single blob into a Polars DataFrame"""

        def read_operation():
            # Download blob content to memory
            content = blob_info["blob"].download_as_bytes()

            # Detect format
            actual_format = self._detect_file_format(
                blob_info["filename"], file_format
            )

            # Read based on format
            if actual_format == "csv":
                df = pl.read_csv(io.BytesIO(content), **reader_options)
            elif actual_format == "parquet":
                df = pl.read_parquet(io.BytesIO(content), **reader_options)
            elif actual_format == "json":
                df = pl.read_json(io.BytesIO(content), **reader_options)
            elif actual_format == "ndjson":
                df = pl.read_ndjson(io.BytesIO(content), **reader_options)
            else:
                raise ZbqOperationError(f"Unsupported file format: {actual_format}")

            # Add source column if requested
            if add_source_column:
                df = df.with_columns(pl.lit(blob_info["name"]).alias("_source_file"))

            return df

        return self.retry_operation(read_operation, max_retries)

    def _read_sequential(
        self,
        blobs_to_read: List[Dict],
        file_format: str,
        add_source_column: bool,
        progress_callback: Optional[Callable],
        max_retries: int,
        reader_options: Dict,
    ) -> tuple[List[pl.DataFrame], int, int, List[str], int]:
        """Read files sequentially"""
        dataframes = []
        read_files = 0
        failed_files = 0
        errors = []
        total_rows = 0

        for i, blob_info in enumerate(blobs_to_read):
            try:
                df = self._read_blob_to_dataframe(
                    blob_info, file_format, add_source_column, max_retries, reader_options
                )
                dataframes.append(df)
                read_files += 1
                total_rows += len(df)
                self.logger.debug(
                    f"Read: {blob_info['name']} ({len(df):,} rows)"
                )

            except Exception as e:
                failed_files += 1
                error_msg = f"Failed to read {blob_info['name']}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            if progress_callback:
                progress_callback(i + 1, len(blobs_to_read))

        return dataframes, read_files, failed_files, errors, total_rows

    def _read_parallel(
        self,
        blobs_to_read: List[Dict],
        file_format: str,
        add_source_column: bool,
        progress_callback: Optional[Callable],
        max_retries: int,
        reader_options: Dict,
    ) -> tuple[List[pl.DataFrame], int, int, List[str], int]:
        """Read files in parallel using ThreadPoolExecutor"""
        dataframes = []
        read_files = 0
        failed_files = 0
        errors = []
        total_rows = 0
        completed_files = 0

        def read_file(blob_info):
            try:
                df = self._read_blob_to_dataframe(
                    blob_info, file_format, add_source_column, max_retries, reader_options
                )
                return {
                    "success": True,
                    "blob_info": blob_info,
                    "dataframe": df,
                    "error": None,
                }

            except Exception as e:
                return {
                    "success": False,
                    "blob_info": blob_info,
                    "dataframe": None,
                    "error": str(e),
                }

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_blob = {
                executor.submit(read_file, blob_info): blob_info
                for blob_info in blobs_to_read
            }

            for future in as_completed(future_to_blob):
                read_result = future.result()
                completed_files += 1

                if read_result["success"]:
                    dataframes.append(read_result["dataframe"])
                    read_files += 1
                    total_rows += len(read_result["dataframe"])
                    self.logger.debug(
                        f"Read: {read_result['blob_info']['name']} "
                        f"({len(read_result['dataframe']):,} rows)"
                    )
                else:
                    failed_files += 1
                    error_msg = (
                        f"Failed to read {read_result['blob_info']['name']}: "
                        f"{read_result['error']}"
                    )
                    errors.append(error_msg)
                    self.logger.error(error_msg)

                if progress_callback:
                    progress_callback(completed_files, len(blobs_to_read))

        return dataframes, read_files, failed_files, errors, total_rows

    def read_iter(
        self,
        bucket_path: str,
        include_patterns: Optional[Union[str, List[str]]] = None,
        exclude_patterns: Optional[Union[str, List[str]]] = None,
        case_sensitive: bool = True,
        use_regex: bool = False,
        file_format: str = "auto",
        max_retries: int = 3,
        max_results: int = 1000,
        **reader_options,
    ):
        """
        Iterator that yields individual DataFrames from GCS bucket files

        This method allows you to process each file's DataFrame individually
        instead of concatenating them all at once.

        Args:
            bucket_path: GCS bucket path (e.g., "my-bucket" or "my-bucket/folder/subfolder")
            include_patterns: Pattern(s) to include (e.g., "*.csv", ["*.csv", "*.json"])
            exclude_patterns: Pattern(s) to exclude (e.g., "temp_*", ["*.tmp", "*.log"])
            case_sensitive: Whether pattern matching is case sensitive
            use_regex: Use regex patterns instead of glob patterns
            file_format: File format - "auto" (auto-detect), "csv", "parquet", "json", "ndjson"
            max_retries: Number of retry attempts for failed reads
            max_results: Maximum number of blobs to list from bucket
            **reader_options: Additional options to pass to Polars read functions

        Yields:
            Tuple[str, pl.DataFrame]: (filename, dataframe) for each successfully read file

        Example:
            # Collect DataFrames into a list
            dataframes = []
            for filename, df in zstorage.read_iter("my-bucket/data", include_patterns="*.csv"):
                dataframes.append(df)

            # Process each file individually
            for filename, df in zstorage.read_iter("my-bucket/data", include_patterns="*.csv"):
                print(f"{filename}: {len(df)} rows")
                # Custom processing per file

            # Build a dictionary
            dfs = {name: df for name, df in zstorage.read_iter("my-bucket/data", include_patterns="*.csv")}

            # Filter based on content
            large_dfs = []
            for filename, df in zstorage.read_iter("my-bucket/data", include_patterns="*.csv"):
                if len(df) > 1000:
                    large_dfs.append((filename, df))
        """
        # Parse bucket path
        bucket_name, combined_prefix = self.parse_bucket_path(bucket_path)

        self.logger.info(f"Starting iterative read from {bucket_path}")

        # List and filter blobs
        blobs_to_read = []

        with self._fresh_client() as client:
            bucket = client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=combined_prefix, max_results=max_results)

            for blob in blobs:
                if not blob.name or blob.name.endswith("/"):
                    continue  # Skip directory markers

                blob_filename = Path(blob.name).name
                if self.match_patterns(
                    blob_filename,
                    include_patterns,
                    exclude_patterns,
                    case_sensitive,
                    use_regex,
                ):
                    blobs_to_read.append(
                        {
                            "blob": blob,
                            "name": blob.name,
                            "filename": blob_filename,
                            "size": blob.size or 0,
                        }
                    )

        if not blobs_to_read:
            self.logger.info("No files found matching the specified patterns")
            return

        # Yield DataFrames one at a time
        for blob_info in blobs_to_read:
            try:
                df = self._read_blob_to_dataframe(
                    blob_info,
                    file_format,
                    add_source_column=False,  # User can add their own tracking
                    max_retries=max_retries,
                    reader_options=reader_options,
                )
                self.logger.debug(
                    f"Read: {blob_info['name']} ({len(df):,} rows)"
                )
                yield blob_info["name"], df

            except Exception as e:
                error_msg = f"Failed to read {blob_info['name']}: {str(e)}"
                self.logger.error(error_msg)
                # Continue to next file instead of stopping iteration

    def _create_client(self):
        return storage.Client(project=self.project_id)
