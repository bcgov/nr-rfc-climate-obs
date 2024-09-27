"""
demo code on how to recover files using boto3

shamelessly copied from:
https://www.slsmk.com/use-boto3-to-recover-deleted-files-in-aws-s3-bucket/
"""

import datetime

import boto3
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
from dateutil.tz import tzutc


class S3Recovery:
    boto_client: boto3.client

    def __init__(self):
        # using the wrapper lib, for loading envs and creating boto client
        self.ostore = NRObjStoreUtil.ObjectStoreUtil()
        self.ostore.createBotoClient()
        self.boto_client = self.ostore.boto_client

        # versions require a resource object vs s3 client.
        self.s3resource = boto3.resource('s3',
                            aws_access_key_id=self.ostore.obj_store_user,
                            aws_secret_access_key=self.ostore.obj_store_secret,
                            endpoint_url=f"https://{self.ostore.obj_store_host}")


    def recover_deletes(self, prefix):
        """
        _summary_: This method will recover all the deleted files that can be matched
                   with the prefix provided.  The prefix needs to either be a directory
                   or a file name.

        :param prefix: a directory or a file name to recover.  If it is a directory,
                          then all files in that directory will be recovered.  If it is
                          a file name, only that file will be recovered.
        :type prefix: str
        """

        paginator = self.boto_client.get_paginator('list_object_versions')
        pageresponse = paginator.paginate(
            Bucket=self.ostore.obj_store_bucket, Prefix=prefix)
        all_cnt = 0
        for pageobject in pageresponse:
            # Find if there are any delmarkers
            if 'DeleteMarkers' in pageobject.keys():
                for each_delmarker in pageobject['DeleteMarkers']:
                    print(f'delete marker {each_delmarker}')
                    self.undo_delete(each_delmarker)
            if all_cnt % 1000 == 0:
                print(f'All count: {all_cnt}')
            all_cnt += 1

    def undo_delete(self, del_obj):
        """
        _summary_: This method will recover a deleted file.  it recieves a
                     list_object_versions response object and will use the information
                     in that object to recover the actual file.

        The following are some examples of the structure of a sample del_obj:

        `del_obj = {'Owner': {'DisplayName': 'nr-rfc-data', 'ID': 'nr-rfc-data'}, 'Key': 'dischargeOBS/', 'VersionId': '1727294411960', 'IsLatest': True, 'LastModified': datetime.datetime(2024, 9, 25, 20, 0, 11, 960000, tzinfo=tzutc())}`
        `del_obj =  {'Owner': {'DisplayName': 'nr-rfc-data', 'ID': 'nr-rfc-data'}, 'Key': 'cmc/MB012_P4.csv', 'VersionId': '1723767525113', 'IsLatest': True, 'LastModified': datetime.datetime(2024, 8, 16, 0, 18, 45, 113000, tzinfo=tzutc())}`
        """
        self.boto_client.list_object_versions(Bucket=self.ostore.obj_store_bucket)
        print(f"undeleting the s3 resource, {del_obj['Key']}")
        fileobjver = self.s3resource.ObjectVersion(
                self.ostore.obj_store_bucket,
                del_obj['Key'],
                del_obj['VersionId']
            )
        fileobjver.delete()

    def test_case_upload_multiple_create_versions(self):
        """
        _summary_: uploads a file multiple times, creating a bunch of
                   different versions for the same file, then it will delete the file.

                   Used to configure a quick test case to create a
                   versioned file and experiment with the recovery process.
        """
        src_file = 'data/asp_env/20240618/PC.csv'
        dest_file = 'test/PC.csv'
        self.ostore.put_object(local_path=src_file, ostore_path=dest_file)
        self.ostore.put_object(local_path=src_file, ostore_path=dest_file)
        self.ostore.put_object(local_path=src_file, ostore_path=dest_file)
        self.ostore.put_object(local_path=src_file, ostore_path=dest_file)
        self.ostore.put_object(local_path=src_file, ostore_path=dest_file)
        self.ostore.put_object(local_path=src_file, ostore_path=dest_file)
        self.ostore.delete_directory(ostore_dir='test/')


if __name__ == '__main__':
    rec = S3Recovery()
    # this sets up a quick and dirty test condition in object storage
    #rec.test_case_upload_multiple_create_versions()
    file2Recover = 'test/PC.csv'
    rec.recover_deletes(prefix=file2Recover)
