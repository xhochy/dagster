# pylint: disable=redefined-outer-name
import os

import pandas as pd
import pytest
from dagster_examples.bay_bikes.pipelines import download_csv_pipeline

from dagster import RunConfig, execute_pipeline


@pytest.fixture
def file_names():
    return ['foo', 'bar', 'baz']


@pytest.fixture
def base_url():
    return 'http://foo.com'


@pytest.fixture
def chunk_size():
    return 8192


@pytest.fixture
def pipeline_config_dict(file_names, base_url, chunk_size):
    return {
        "resources": {"bucket": {"config": {"bucket_name": "test_bucket", "bucket_obj": ""}}},
        "solids": {
            "download_zipfiles_from_urls": {
                "inputs": {
                    "base_url": {"value": base_url},
                    "chunk_size": {"value": chunk_size},
                    "file_names": [
                        {"value": "{}.zip".format(file_name)} for file_name in file_names
                    ],
                    "target_dir": {"value": ""},
                }
            },
            "unzip_files": {"inputs": {"source_dir": {"value": ""}, "target_dir": {"value": ""}}},
            "consolidate_csv_files": {
                "inputs": {"source_dir": {"value": ""}, "target": {"value": ""}}
            },
        },
    }


def mock_unzip_csv(zipfile_path, target):
    target = '{}/{}'.format(target, zipfile_path.split('/')[-1].replace('.zip', ''))
    mock_data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    mock_data.to_csv(target)
    return target


def test_download_csv_locally_pipeline(mocker, tmpdir, pipeline_config_dict):
    # Setup download mocks
    mocker.patch('dagster_examples.bay_bikes.solids.requests')
    mocker.patch('dagster_examples.bay_bikes.solids._write_chunks_to_fp')
    mocker.patch('dagster_examples.bay_bikes.solids._unzip_file', side_effect=mock_unzip_csv)

    # Setup tempdirs and configure input config dict
    download_target_directory = tmpdir.mkdir('zip_target')
    csv_target_directory = tmpdir.mkdir('csv_target')
    final_csv = csv_target_directory.join('consolidated.csv')

    # Setup fake bucket
    test_bucket = tmpdir.mkdir("test_bucket")
    pipeline_config_dict['resources']['bucket']['config']['bucket_obj'] = str(test_bucket)

    pipeline_config_dict['solids']['download_zipfiles_from_urls']['inputs']['target_dir'][
        'value'
    ] = str(download_target_directory)
    pipeline_config_dict['solids']['unzip_files']['inputs']['source_dir']['value'] = str(
        download_target_directory
    )
    pipeline_config_dict['solids']['unzip_files']['inputs']['target_dir']['value'] = str(
        csv_target_directory
    )

    pipeline_config_dict['solids']['consolidate_csv_files']['inputs']['source_dir']['value'] = str(
        download_target_directory
    )
    pipeline_config_dict['solids']['consolidate_csv_files']['inputs']['target']['value'] = str(
        final_csv
    )

    # execute tests
    result = execute_pipeline(
        download_csv_pipeline,
        environment_dict=pipeline_config_dict,
        run_config=RunConfig(mode='local'),
    )
    target_files = set(os.listdir(csv_target_directory.strpath))
    assert result.success
    assert len(target_files) == 4
    consolidated = pd.read_csv(os.path.join(str(test_bucket), 'consolidated.csv'))
    assert list(consolidated.A) == [1, 2, 3, 1, 2, 3, 1, 2, 3]
    assert os.listdir(str(test_bucket)) == ['consolidated.csv']
