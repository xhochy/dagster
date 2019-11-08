from dagster import ModeDefinition, pipeline

from .resources import local_bucket_resource
from .solids import (
    consolidate_csv_files,
    download_zipfiles_from_urls,
    unzip_files,
    upload_file_to_bucket,
)


@pipeline(mode_defs=[ModeDefinition(resource_defs={'bucket': local_bucket_resource})])
def download_csv_pipeline():
    upload_file_to_bucket(consolidate_csv_files(unzip_files(download_zipfiles_from_urls())))
