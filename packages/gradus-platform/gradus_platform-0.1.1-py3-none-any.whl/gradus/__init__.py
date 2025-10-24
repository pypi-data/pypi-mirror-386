"""Gradus package utilities for AWS S3 interactions and ECS handlers."""

from .ecs import (
    bucket_name,
    MAX_RETRIES,
    ecs_handler,
    generate_file_hash,
    read_file_from_s3,
    upload_file_s3,
    send_callback,
)
from .local_handler import local_handler  # <-- NOVO

__all__ = [
    "bucket_name",
    "MAX_RETRIES",
    "ecs_handler",
    "generate_file_hash",
    "read_file_from_s3",
    "upload_file_s3",
    "send_callback",
    "local_handler"
]
