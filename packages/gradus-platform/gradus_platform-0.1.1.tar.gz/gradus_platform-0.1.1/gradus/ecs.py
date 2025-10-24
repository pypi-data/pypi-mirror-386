"""Core Gradus ECS handler utilities.

This module provides helper functions to interact with AWS S3 and send
status callbacks.  The ``ecs_handler`` function replicates the behaviour of the
legacy script used by the Gradus platform while keeping the logic reusable
within a package.
"""

from __future__ import annotations

import io
import json
import os
import time
import traceback
from datetime import datetime
from hashlib import md5
from typing import Any, Dict, Optional

import boto3
import requests

# Globals
bucket_name = "bucket-ppr"
MAX_RETRIES = 5


def generate_file_hash(file: io.BytesIO) -> str:
    """Generate an MD5 hash for an in-memory file object."""

    return md5(file.getbuffer()).hexdigest()


def read_file_from_s3(
    file_path: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
) -> io.BytesIO:
    """Read a file from S3 and return it as an in-memory buffer."""

    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    obj = s3.get_object(Bucket=bucket_name, Key=file_path)
    file_data = obj["Body"].read()
    return io.BytesIO(file_data)


def upload_file_s3(
    file: io.BytesIO,
    object_name: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
) -> Optional[str]:
    """Upload an in-memory file object to S3."""

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=file.getvalue())
        print("File uploaded successfully.")
        return object_name
    except Exception as exc:  # pragma: no cover - simple logging wrapper
        print(f"Error uploading file to S3 and generating presigned URL: {exc}")
        return None


def send_callback(callback_url: str, data: Dict[str, Any]) -> Optional[requests.Response]:
    """Send a callback request using multiple fallbacks for compatibility."""

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Gradus-Tool/1.0",
        "Accept": "application/json",
    }

    if not callback_url.endswith("/"):
        callback_url = callback_url + "/"

    print(f"Sending callback to: {callback_url}")
    print(f"Data to send: {data}")

    try:
        response = requests.post(callback_url, json=data, headers=headers, timeout=30)
        print(f"POST JSON attempt - Status: {response.status_code}")
        if response.status_code == 200:
            return response
    except Exception as exc:  # pragma: no cover - network interaction
        print(f"POST JSON failed: {exc}")

    try:
        response = requests.post(callback_url, data=data, timeout=30)
        print(f"POST form data attempt - Status: {response.status_code}")
        if response.status_code == 200:
            return response
    except Exception as exc:  # pragma: no cover - network interaction
        print(f"POST form data failed: {exc}")

    try:
        response = requests.get(callback_url, params=data, timeout=30)
        print(f"GET query params attempt - Status: {response.status_code}")
        return response
    except Exception as exc:  # pragma: no cover - network interaction
        print(f"GET query params failed: {exc}")
        return None


def _normalize_boolean_values(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert string boolean values ("true"/"false") to native booleans."""

    normalized = {}
    for key, value in payload.items():
        if isinstance(value, str) and value.lower() in {"true", "false"}:
            normalized[key] = value.lower() == "true"
        else:
            normalized[key] = value
    return normalized


def ecs_handler(extras: dict[str, str] | None = None) -> None:
    """Main entry point executed in the ECS container."""

    try:
        toolname = os.environ.get("toolname")
        execution_id = os.environ.get("execution_id")
        aws_access_key_id = os.environ.get("aws_access_key_id")
        aws_secret_access_key = os.environ.get("aws_secret_access_key")
        callback_url = os.environ.get("callback_url")

        callback_url_formatted = f"{callback_url}"
        output_path = f"tools/{toolname}/{execution_id}/output/"

        valid_json_str = os.environ.get("inputs", "{}").replace("'", '"')
        inputs = _normalize_boolean_values(json.loads(valid_json_str))

        valid_json_str = os.environ.get("files", "{}").replace("'", '"')
        files = json.loads(valid_json_str)

        for key, name in files.items():
            inputs[key] = read_file_from_s3(name, aws_access_key_id, aws_secret_access_key)

        if extras:
            for var_name, s3_key in extras.items():
                inputs[var_name] = read_file_from_s3(
                    s3_key, aws_access_key_id, aws_secret_access_key
                )

    except Exception as exc:
        response = {
            "status": "error",
            "status_text": "Erro no processamento dos inputs " + str(exc),
            "message": str(traceback.format_exc()),
        }
        print(response)
        send_callback(callback_url_formatted, response)
        return

    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    response = {
        "status": "running",
        "status_text": f"Execução iniciada em: {current_datetime_str} UTC0",
        "message": f"Execution initiated at {current_datetime_str} UTC0",
    }
    print(response)
    send_callback(callback_url_formatted, response)

    try:
        exec("from " + toolname + " import main as main_tool", globals())
        output_execucao = globals()["main_tool"](**inputs)
    except Exception as exc:
        response = {
            "status": "error",
            "status_text": "Erro na execução das rotinas: " + str(exc),
            "message": str(traceback.format_exc()),
        }
        print(response)
        send_callback(callback_url_formatted, response)
        return

    try:
        for key, value in list(output_execucao.items()):
            if isinstance(value, io.IOBase):
                filename = output_execucao.get(f"{key}__nome", key)
                name_parts = filename.split(".")
                base = name_parts[0]
                extension = name_parts[-1] if len(name_parts) > 1 else "bin"
                file_output = (
                    f"{output_path}{base}_{generate_file_hash(value)[:5]}.{extension}"
                )
                object_s3 = upload_file_s3(
                    value, file_output, aws_access_key_id, aws_secret_access_key
                )
                output_execucao[key] = object_s3
                print(object_s3)

        output_execucao["status"] = "success"
        output_execucao["status_text"] = "Execução bem sucedida!"
        print(output_execucao)
        print("Posting to: ", callback_url_formatted)
        tries = 0
        status = 0
        while status != 200 and tries < MAX_RETRIES:
            response = send_callback(callback_url_formatted, output_execucao)
            if response:
                status = response.status_code
                print(f"Callback attempt {tries + 1}: Status {status}")
                if status == 200:
                    print(f"SUCCESS! Final callback response: {response.content}")
                    break
                print(f"Response content: {response.content}")
            else:
                status = 500
            time.sleep(2)
            tries += 1

    except Exception as exc:
        response = {
            "status": "error",
            "status_text": "Erro enviando retorno: " + str(exc),
            "message": str(traceback.format_exc()),
        }
        print(response)
        send_callback(callback_url_formatted, response)
