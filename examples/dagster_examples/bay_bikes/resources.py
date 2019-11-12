import os

from abc import ABCMeta, abstractmethod
from dagster import Field, String, resource, check

from shutil import copyfile
from six import with_metaclass

from google.cloud import storage
from google.cloud.exceptions import NotFound


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
    def set_object(self, obj):
        pass

    @abstractmethod
    def get_object(self, key):
        pass

    @abstractmethod
    def has_key(self, key):
        pass


class LocalBucket(AbstractBucket):
    """Uses a directory to mimic an cloud storage bucket"""

    def __init__(self, bucket_name, bucket_obj):
        self.bucket_name = bucket_name
        self.bucket_object = bucket_obj

    def set_object(self, obj):
        destination = os.path.join(self.bucket_object, os.path.basename(obj))
        copyfile(obj, destination)
        return destination

    def get_object(self, key):
        return os.path.join(self.bucket_object, key)

    def has_key(self, key):
        return os.path.exists(os.path.join(self.bucket_object, key))


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

    def set_object(self, obj):
        '''Given a filename on your filesystem upload it to the bucket'''
        blob = self.bucket_obj.blob(obj)
        try:
            blob.upload_from_filename(obj)
        except Exception as e:
            raise DagsterCloudResourceSDKException(e)

    def has_key(self, key):
        return True if self.bucket_obj.get_blob(key) else False


@resource(config={'bucket_name': Field(String), 'bucket_obj': Field(String)})
def local_bucket_resource(context):
    return LocalBucket(
        context.resource_config['bucket_name'], context.resource_config['bucket_obj']
    )


@resource(config={'bucket_name': Field(String)})
def production_bucket_resource(context):
    return GoogleCloudStorageBucket(context.resource_config['bucket_name'])
