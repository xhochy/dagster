from dagster import ModeDefinition, pipeline

from .resources import local_bucket_resource, production_bucket_resource
from .solids import (
    consolidate_csv_files,
    download_zipfiles_from_urls,
    unzip_files,
    upload_file_to_bucket,
)


local_mode = ModeDefinition(
    name='local',
    resource_defs={'bucket': local_bucket_resource}
)


production_mode = ModeDefinition(
    name='production',
    resource_defs={'bucket': production_bucket_resource}
)


@pipeline(mode_defs=[local_mode, production_mode])
def download_csv_pipeline():
    upload_file_to_bucket(consolidate_csv_files(unzip_files(download_zipfiles_from_urls())))
