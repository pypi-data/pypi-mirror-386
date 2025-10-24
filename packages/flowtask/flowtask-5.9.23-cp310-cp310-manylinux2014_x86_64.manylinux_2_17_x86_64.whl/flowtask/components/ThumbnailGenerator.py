from typing import Callable
import asyncio
import os
from pathlib import Path
import aiofiles
from io import BytesIO
import pyheif
from PIL import Image, UnidentifiedImageError
import filetype
import pandas as pd
from .flow import FlowComponent
from ..interfaces.Boto3Client import Boto3Client
from ..conf import  THUMBNAIL_LOCAL_BASE_URL


class ThumbnailGenerator(Boto3Client, FlowComponent):
    """
    ThumbnailGenerator.

        Overview
        This component generates thumbnails for images stored in a DataFrame. It takes an image column, resizes the images
        to a specified size, and saves them in a specified directory with a given filename format. The generated thumbnail
        paths are added to a new column in the DataFrame.
        .. table:: Properties
        :widths: auto
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | Name                      | Required | Summary                                                                   |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | data_column               |   Yes    | The name of the column containing the image data.                         |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | thumbnail_column          |  Yes    | The name of the column to store the generated thumbnail paths.             |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | size                      |   Yes    | The size of the thumbnail. Can be a tuple (width, height) or a single     |
        |                           |          | integer for a square thumbnail.                                           |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | format                    |   Yes    | The format of the thumbnail (e.g., 'JPEG', 'PNG').                        |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | directory                 |   No     | The directory where the thumbnails will be saved (default: ./thumbnails). |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | filename                  |   Yes    | The filename template for the thumbnails. It can include placeholders     |
        |                           |          | for DataFrame columns (e.g., '{column_name}.jpg').                        |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | use_s3                    |   No     | Flag to save thumbnails in S3 instead of local disk.                      |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | s3_config                 |   No     | S3 configuration when use_s3 is True (default: default).                  |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | s3_prefix                 | Yes*     | S3 prefix/path for thumbnails (required when use_s3=True).                |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | url_thumbnail_column      |  No      | Column name to store the presigned URL of the thumbnail                   |
        |                           |          | (default: url_thumbnail).                                                 |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        | thumbnail_directory_column|  No      | Column name to store the base directory/URL for thumbnails                |
        |                           |          | (default: thumbnail_directory).                                           |
        +---------------------------+----------+-----------+---------------------------------------------------------------+
        Returns
        This component returns a DataFrame with new columns containing the paths and URLs of the generated thumbnails.
        Example:
        ```
        - ThumbnailGenerator:
            data_column: image
            thumbnail_column: thumbnail_photo
            size: (128, 128)
            format: JPEG
            filename: {photo_id}.jpg
            use_s3: true
            s3_prefix: /thumbnails/epson
        ```
    """  # noqa: E501
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        self.data_column = kwargs.pop("data_column", None)
        self.thumbnail_column = kwargs.pop("thumbnail_column", 'thumbnail')
        if not self.data_column:
            raise ValueError("data_column must be specified.")
        self.size = kwargs.pop("size", (128, 128))
        self.size = self.size if isinstance(self.size, tuple) else (self.size, self.size)
        self.image_format = kwargs.pop("format", "JPEG").upper()
        self.directory = kwargs.pop("directory", "./thumbnails")
        self.filename_template = kwargs.pop("filename", "thumbnail_{id}.jpg")
        
        # S3 configuration
        self.use_s3 = kwargs.pop("use_s3", False)
        self.s3_config = kwargs.pop("s3_config", "default")
        self.s3_prefix = kwargs.pop("s3_prefix", None)
        self.url_thumbnail_column = kwargs.pop("url_thumbnail_column", "url_thumbnail")
        self.thumbnail_directory_column = kwargs.pop("thumbnail_directory_column", "thumbnail_directory")
        
        # Validate S3 configuration
        if self.use_s3 and not self.s3_prefix:
            raise ValueError("s3_prefix is required when use_s3=True.")
        
        # Set config for Boto3Client inheritance BEFORE calling super().__init__
        if self.use_s3:
            self._config = self.s3_config
        else:
            self._config = "default"
        
        # Pass config to Boto3Client constructor
        kwargs['config'] = self._config
        
        super(ThumbnailGenerator, self).__init__(loop=loop, job=job, stat=stat, **kwargs)
        self._semaphore = asyncio.Semaphore(10)  # Adjust the limit as needed

    async def start(self, **kwargs) -> bool:
        if self.previous:
            self.data = self.input
            
        if self.use_s3:
            # Process credentials and initialize S3 connection
            self.processing_credentials()
            await self.open()
        else:
            # Local directory setup - skip Boto3Client initialization
            if isinstance(self.directory, str):
                self.directory = Path(self.directory).resolve()
            # check if directory exists
            if self.directory.exists() and not self.directory.is_dir():
                raise ValueError(f"{self.directory} is not a directory.")
            if not self.directory.exists():
                self.directory.mkdir(parents=True, exist_ok=True)
        return True

    async def open(self, **kwargs):
        """Override open method to only process S3 when needed"""
        if self.use_s3:
            return await super().open(**kwargs)
        else:
            # Skip S3 initialization for local storage
            return self

    async def close(self, **kwargs):
        if self.use_s3:
            await super().close(**kwargs)
        return True

    async def _save_to_s3(self, image, filename: str, content_type: str) -> str:
        """Save thumbnail to S3 and return the S3 key"""
        try:
            # Convert image to bytes
            img_buffer = BytesIO()
            image.save(img_buffer, format=self.image_format)
            img_buffer.seek(0)
            image_data = img_buffer.getvalue()
            
            # Create S3 key
            s3_key = f"{self.s3_prefix.strip('/')}/{filename}"
            
            # Upload to S3
            self._connection.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=image_data,
                ContentType=content_type
            )
            
            return s3_key
        except Exception as e:
            self._logger.error(f"Error saving to S3: {e}")
            raise

    async def _generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for the S3 object"""
        try:
            url = self._connection.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            self._logger.error(f"Error generating presigned URL: {e}")
            raise

    async def run(self) -> pd.DataFrame:
        # check for duplicates
        async def handle(idx):
            async with self._semaphore:
                row = self.data.loc[idx].to_dict()
                file_obj = row[self.data_column]
                if not file_obj:
                    self.logger.error(f"Row {idx}: No file object found.")
                    return None
                stream = file_obj.getvalue() if isinstance(file_obj, BytesIO) else file_obj
                # Detect MIME type first
                kind = filetype.guess(stream)
                if kind is None:
                    self.logger.error(
                        f"Row {idx}: Cannot detect MIME type. Please check the file, skipping"
                    )
                    return None
                filename = self.filename_template.format(**row)
                filename = self.mask_replacement(filename)
                if self.use_s3:
                    # For S3, we don't need filepath
                    pass
                else:
                    # For local storage, convert directory to Path
                    if isinstance(self.directory, str):
                        self.directory = Path(self.directory)
                    filepath = self.directory.joinpath(filename)
                try:
                    if kind == 'image/heic':
                        try:
                            i = pyheif.read_heif(stream)
                            image = Image.frombytes(mode=i.mode, size=i.size, data=i.data)
                        except Exception as e:
                            self._logger.error(
                                f"Unable to parse Apple Heic Photo at row {row}"
                            )
                            return None
                    else:
                        image = Image.open(BytesIO(stream))
                    image.thumbnail(self.size)
                    
                    if self.use_s3:
                        # Save to S3
                        content_type = f"image/{self.image_format.lower()}"
                        s3_key = await self._save_to_s3(image, filename, content_type)
                        
                        # Set only the filename in the DataFrame (not the full path)
                        self.data.at[idx, self.thumbnail_column] = filename
                        
                        # Set the base directory/URL for S3
                        self.data.at[idx, self.thumbnail_directory_column] = self.s3_prefix
                        
                        # Generate presigned URL
                        presigned_url = await self._generate_presigned_url(s3_key)
                        self.data.at[idx, self.url_thumbnail_column] = s3_key
                        
                    else:
                        # Local file handling
                        filepath = self.directory.joinpath(filename)
                        
                        # Set the thumbnail path in the DataFrame (relative path)
                        relative_path = str(filepath.relative_to(self.directory))
                        self.data.at[idx, self.thumbnail_column] = relative_path
                        
                        # Set the base directory/URL for local
                        self.data.at[idx, self.thumbnail_directory_column] = THUMBNAIL_LOCAL_BASE_URL
                        
                        # check if file exists
                        if filepath.exists():
                            return filepath
                        try:
                            # Save file into disk
                            image.save(filepath, self.image_format)
                        except OSError as e:
                            self._logger.error(
                                f"Row {idx}: Unable to save image {filepath}, error: {e}"
                            )
                            
                except UnidentifiedImageError:
                    self._logger.error(
                        f"Row {idx}: PIL cannot identify image file. MIME: {kind.mime}"
                    )
                    if self.use_s3:
                        # For S3, we'll skip bad images
                        return None
                    else:
                        # Local bad image handling
                        bad_folder = self.directory.joinpath('bad_images')
                        if not bad_folder.exists():
                            bad_folder.mkdir(parents=True, exist_ok=True)
                        try:
                            # Save bad file into disk:
                            bad_file = bad_folder.joinpath(filename)
                            async with aiofiles.open(bad_file, "wb") as fp:
                                await fp.write(stream)
                        except Exception as e:
                            self._logger.warning(
                                f"Unable to save {bad_file} on disk, error: {e}"
                            )
                    return
                except Exception as e:
                    self._logger.exception(
                        f"Row {idx}: Unexpected error processing image: {e}"
                    )
                    return

        await asyncio.gather(*(handle(i) for i in self.data.index))

        self._result = self.data
        return self._result
