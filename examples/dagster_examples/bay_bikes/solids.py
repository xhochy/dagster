import csv
import os
import zipfile
from typing import List

import pandas as pd
import requests

from dagster import solid, Field, String, Int, Bool


def _write_chunks_to_fp(response, output_fp, chunk_size):
    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            output_fp.write(chunk)


def _download_zipfile_from_url(url: str, target: str, chunk_size=8192) -> str:
    with requests.get(url, stream=True) as response, open(target, 'wb+') as output_fp:
        response.raise_for_status()
        _write_chunks_to_fp(response, output_fp, chunk_size)
    return target


@solid
def download_zipfiles_from_urls(
    _, base_url: str, file_names: List[str], target_dir: str, chunk_size=8192
) -> List[str]:
    for file_name in file_names:
        if not os.path.exists(os.path.join(target_dir, file_name)):
            _download_zipfile_from_url(
                "/".join([base_url, file_name]), os.path.join(target_dir, file_name), chunk_size
            )
    return file_names


def _unzip_file(zipfile_path: str, target: str) -> str:
    with zipfile.ZipFile(zipfile_path, 'r') as zip_fp:
        zip_fp.extractall(target)
        return zip_fp.namelist()[0]


@solid
def unzip_files(_, file_names: List[str], source_dir: str, target_dir: str) -> List[str]:
    return [
        _unzip_file(os.path.join(source_dir, file_name), target_dir) for file_name in file_names
    ]


@solid(
    config={
        'delimiter': Field(
            String,
            default_value=',',
            is_optional=True,
            description=('A one-character string used to separate fields.'),
        )
    }
)
def consolidate_csv_files(
    context, input_file_names: List[str], source_dir: str, target: str
) -> str:
    # There must be a header in all of these dataframes or pandas won't know how to concatinate dataframes.
    dataset = pd.concat(
        [
            pd.read_csv(os.path.join(source_dir, file_name), sep=context.solid_config['delimiter'], header=0)
            for file_name in input_file_names
        ]
    )
    dataset.to_csv(target, sep=context.solid_config['delimiter'])
    return target


@solid(required_resource_keys={'bucket'})
def upload_file_to_bucket(context, file_path: str):
    if not context.resources.bucket.has_key(os.path.basename(file_path)):
        context.resources.bucket.set_object(file_path)
