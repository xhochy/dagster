import os

from dagster import Field, String, resource, check

from google.cloud import storage
from google.cloud.exceptions import NotFound


class DagsterCloudResourceSDKException(object):

    def __init__(self, inner_error):
        check.inst_param(inner_error, 'inner_error', Exception)
        self.inner_error = inner_error
        self.message = 'Recevied error of type {}. Reason: {}.',format(type(inner_error), inner_error.message)






class AbstractBucket(object):
    """
    Done so that we can create a consistent interface across
    different cloud storage abstractions (and local storage)
    """

    # Went with this instead of ABC because of python cross-version compatibility issues
    def set_object(self, obj):
        raise NotImplementedError("Override this function")

    def get_object(self, key):
        raise NotImplementedError("Override this function")

    def has_key(self, key):
        raise NotImplementedError("Override this function")


class LocalBucket(AbstractBucket):
    """Uses a directory to mimic an cloud storage bucket"""

    def __init__(self, bucket_name, bucket_obj):
        self.bucket_name = bucket_name
        self.bucket_object = bucket_obj

    def set_object(self, obj):
        destination = os.path.join(self.bucket_object, os.path.basename(obj))
        os.symlink(obj, destination)
        return destination

    def get_object(self, key):
        return os.path.join(self.bucket_object, key)

    def has_key(self, key):
        return os.path.islink(os.path.join(self.bucket_object, key))


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


@resource(config={'bucket_name': Field(String), 'bucket_obj': Field(String)})
def local_bucket_resource(context):
    return LocalBucket(
        context.resource_config['bucket_name'], context.resource_config['bucket_obj']
    )


@resource(config={'bucket_name': Field(String)})
def production_bucket_resource(context):
    return GoogleCloudStorageBucket(context.resource_config['bucket_name'])
