import json
import os
from abc import ABCMeta, abstractmethod

from google.cloud import storage
from google.cloud.exceptions import NotFound
from six import with_metaclass

from dagster import Field, String, check, resource, seven


class DagsterCloudResourceSDKException(Exception):
    def __init__(self, inner_error):
        check.inst_param(inner_error, 'inner_error', Exception)
        self.inner_error = inner_error
        message = (
            'Recevied error of type {}. Reason: {}.',
            format(type(inner_error), inner_error.message),
        )
        super(DagsterCloudResourceSDKException, self).__init__(message)


class AbstractBucket(with_metaclass(ABCMeta)):
    """
    Done so that we can create a consistent interface across
    different cloud storage abstractions (and local storage)
    """

    @abstractmethod
    def set_object(self, key):
        pass

    @abstractmethod
    def get_object(self, key):
        pass

    @abstractmethod
    def has_key(self, key):
        pass


class LocalBucket(AbstractBucket):
    """Uses a directory to mimic an cloud storage bucket"""

    def __init__(self, bucket_path):
        self.bucket_object = bucket_path
        self.key_storage_path = os.path.join(bucket_path, 'key_storage.json')
        os.makedirs(bucket_path, exist_ok=True)
        with open(self.key_storage_path, 'w+') as fp:
            json.dump({'keys': []}, fp)

    def set_object(self, key):
        with open(self.key_storage_path, 'r') as key_storage_fp:
            key_storage = json.load(key_storage_fp)
        key_storage['keys'].append(key)
        with open(self.key_storage_path, 'w') as key_storage_fp:
            json.dump(key_storage, key_storage_fp)

    def get_object(self, key):
        if not self.has_key(key):
            raise Exception(
                'Unable to find key {key_requested} in bucket of name {bucket}'.format(
                    key_requested=key, bucket=self.bucket_object
                )
            )
        return key

    def has_key(self, key):
        with open(self.key_storage_path, 'r') as key_storage_fp:
            key_storage = json.load(key_storage_fp)
            return key in key_storage['keys']


class GoogleCloudStorageBucket(AbstractBucket):
    """Uses google cloud storage sdk to upload/download objects"""

    def __init__(self, bucket_name):
        # TODO: Eventually support custom authentication so we aren't forcing people to setup their environments
        self.client = storage.Client()
        self.bucket_name = bucket_name
        try:
            self.bucket_obj = self.client.get_bucket(self.bucket_name)
        except NotFound as e:
            raise DagsterCloudResourceSDKException(e)

    def get_object(self, key):
        return self.bucket_obj.get_blob(key)

    def set_object(self, key):
        '''Given a filename on your filesystem upload it to the bucket'''
        blob = self.bucket_obj.blob(key)
        try:
            blob.upload_from_filename(key)
        except Exception as e:
            raise DagsterCloudResourceSDKException(e)

    def has_key(self, key):
        return True if self.bucket_obj.get_blob(key) else False


@resource(config={'bucket_path': Field(String)})
def local_bucket_resource(context):
    return LocalBucket(context.resource_config['bucket_path'])


@resource(config={'bucket_name': Field(String)})
def production_bucket_resource(context):
    return GoogleCloudStorageBucket(context.resource_config['bucket_name'])


@resource
def temporary_directory_mount(_):
    with seven.TemporaryDirectory() as tmpdir_path:
        yield tmpdir_path


@resource(config={'mount_location': Field(String)})
def mount(context):
    mount_location = context.resource_config['mount_location']
    if os.path.exists(mount_location):
        return context.resource_config['mount_location']
    raise NotADirectoryError("Cant mount files on this resource. Make sure it exists!")
