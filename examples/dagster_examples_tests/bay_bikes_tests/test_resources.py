from dagster_examples.bay_bikes.resources import LocalBucket


def test_local_bucket_resource(tmpdir):
    tmp_file_to_upload = tmpdir.mkdir('files_to_upload').join('foo.txt')
    with open(str(tmp_file_to_upload), 'w+') as tmp_fp:
        tmp_fp.write('hello')
    fake_bucket_directory = tmpdir.mkdir('bucket')
    bucket_resource = LocalBucket('fake_bucket', fake_bucket_directory)
    assert not bucket_resource.has_key('foo.txt')
    bucket_resource.set_object(tmp_file_to_upload)
    assert bucket_resource.has_key('foo.txt')
    with open(bucket_resource.get_object('foo.txt'), 'r') as fp:
        assert fp.read() == 'hello'
