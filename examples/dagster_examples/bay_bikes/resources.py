import os

from dagster import Field, String, resource


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


@resource(config={'bucket_name': Field(String), 'bucket_obj': Field(String)})
def local_bucket_resource(context):
    return LocalBucket(
        context.resource_config['bucket_name'], context.resource_config['bucket_obj']
    )
