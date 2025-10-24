# gradus/local_handler.py
import sys
import json
import io
import boto3
import requests
import os
import traceback
from datetime import datetime
import time
from hashlib import md5

# Imports Windows opcionais (não usados neste fluxo; mantenha se precisar futuramente)
try:
    import win32con  # noqa: F401
    import win32event  # noqa: F401
    import win32process  # noqa: F401
    import win32profile  # noqa: F401
except Exception:
    pass

# Globals
bucket_name = "bucket-ppr"
MAX_RETRIES = 5


def generate_file_hash(file: io.BytesIO) -> str:
    return str(md5(file.getbuffer()).hexdigest())


def read_file_from_s3(file_path: str, aws_access_key_id: str, aws_secret_access_key: str) -> io.BytesIO:
    s3 = boto3.client("s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    obj = s3.get_object(Bucket=bucket_name, Key=file_path)
    file_data = obj["Body"].read()
    return io.BytesIO(file_data)


def upload_file_s3(file: io.BytesIO, object_name: str, aws_access_key_id: str, aws_secret_access_key: str):
    try:
        s3 = boto3.client("s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=file.getvalue())
        print("File uploaded successfully.")
        return object_name
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None


def send_callback(callback_url: str, data: dict):
    """Envia callback com múltiplas tentativas de formato (JSON -> form -> GET)"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pinheirinhos-Tool/1.0",
        "Accept": "application/json",
    }

    if not callback_url.endswith("/"):
        callback_url = callback_url + "/"

    print(f"Sending callback to: {callback_url}")
    print(f"Data to send: {data}")

    # 1) POST JSON
    try:
        response = requests.post(callback_url, json=data, headers=headers, timeout=30)
        print(f"POST JSON attempt - Status: {response.status_code}")
        if response.status_code == 200:
            return response
    except Exception as e:
        print(f"POST JSON failed: {e}")

    # 2) POST form
    try:
        response = requests.post(callback_url, data=data, timeout=30)
        print(f"POST form data attempt - Status: {response.status_code}")
        if response.status_code == 200:
            return response
    except Exception as e:
        print(f"POST form data failed: {e}")

    # 3) GET
    try:
        response = requests.get(callback_url, params=data, timeout=30)
        print(f"GET query params attempt - Status: {response.status_code}")
        return response
    except Exception as e:
        print(f"GET query params failed: {e}")
        return None


def _normalize_bools(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, str) and v.lower() == "true":
            out[k] = True
        elif isinstance(v, str) and v.lower() == "false":
            out[k] = False
        else:
            out[k] = v
    return out


def local_handler(extras: dict[str, str] | None = None) -> None:
    """
    Executa localmente (via CLI ou chamado programático).
    - Aceita `extras` como dicionário {nome_variavel: caminho_s3} para inputs adicionais.
    - Também aceita 'extras' dentro do payload JSON passado via argv[1].
    """
    if len(sys.argv) >= 2:
        # CLI: payload JSON no argv[1]
        try:
            data_dict = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(f"Erro ao desserializar payload JSON: {e}")
            sys.exit(1)
    else:
        # Programático: se não veio argv, inicializa vazio e espera que chamem com extras/params
        data_dict = {}

    toolname = data_dict.get("toolname")
    executionID = data_dict.get("execution_id")
    aws_access_key_id = data_dict.get("aws_access_key_id")
    aws_secret_access_key = data_dict.get("aws_secret_access_key")
    callbackURL = data_dict.get("callback_url")

    OUTPUT_PATH = f"tools/{toolname}/{executionID}/output/"

    # 1) Inputs e files
    try:
        inputs = _normalize_bools(data_dict.get("inputs", {}))

        files = data_dict.get("files", {})
        for key, name in files.items():
            inputs[key] = read_file_from_s3(name, aws_access_key_id, aws_secret_access_key)

        # 1b) Extras vindos via parâmetro (prioridade)
        if extras:
            for var_name, s3_key in extras.items():
                print(f"Lendo arquivo extra (param): {var_name} <- {s3_key}")
                inputs[var_name] = read_file_from_s3(s3_key, aws_access_key_id, aws_secret_access_key)

        # 1c) Extras vindos dentro do payload JSON (fallback)
        extras_json = data_dict.get("extras", {})
        for var_name, s3_key in extras_json.items():
            # Só carrega se ainda não veio pelo parâmetro `extras` (prioridade)
            if var_name not in inputs:
                print(f"Lendo arquivo extra (JSON): {var_name} <- {s3_key}")
                inputs[var_name] = read_file_from_s3(s3_key, aws_access_key_id, aws_secret_access_key)

    except Exception as e:
        response = {
            "status": "error",
            "status_text": "Erro no processamento dos inputs " + str(e),
            "message": str(traceback.format_exc()),
        }
        print(response)
        if callbackURL:
            send_callback(callbackURL, response)
        return

    # 2) Status running
    current_datetime_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    response = {
        "status": "running",
        "status_text": f"Execução iniciada em: {current_datetime_str} UTC0",
        "message": f"Execution initiated at {current_datetime_str} UTC0",
    }
    print(response)
    if callbackURL:
        send_callback(callbackURL, response)

    # 3) Execução
    try:
        exec("from " + toolname + " import main as main_tool", globals())
        output_execucao = main_tool(**inputs)
    except Exception as e:
        response = {
            "status": "error",
            "status_text": "Erro na execução das rotinas: " + str(e),
            "message": str(traceback.format_exc()),
        }
        print(response)
        if callbackURL:
            send_callback(callbackURL, response)
        return

    # 4) Saída + upload
    try:
        for key, value in list(output_execucao.items()):
            if isinstance(value, io.IOBase):
                filename = output_execucao.get(f"{key}__nome", key)
                base, dot, ext = filename.partition(".")
                ext = ext or "bin"
                file_output = f"{OUTPUT_PATH}{base}_{generate_file_hash(value)[:5]}.{ext}"
                object_s3 = upload_file_s3(value, file_output, aws_access_key_id, aws_secret_access_key)
                output_execucao[key] = object_s3
                print(object_s3)

        output_execucao["status"] = "success"
        output_execucao["status_text"] = "Execução bem sucedida!"
        print(output_execucao)

        tries = 0
        status = 0
        while (status != 200) and (tries < MAX_RETRIES) and callbackURL:
            r = send_callback(callbackURL, output_execucao)
            status = r.status_code if r else 500
            print(f"Callback attempt {tries + 1}: Status {status}")
            if status == 200:
                print(f"SUCCESS! Final callback response: {getattr(r, 'content', b'')}")
                break
            time.sleep(2)
            tries += 1

    except Exception as e:
        response = {
            "status": "error",
            "status_text": "Erro enviando retorno: " + str(e),
            "message": str(traceback.format_exc()),
        }
        print(response)
        if callbackURL:
            send_callback(callbackURL, response)
