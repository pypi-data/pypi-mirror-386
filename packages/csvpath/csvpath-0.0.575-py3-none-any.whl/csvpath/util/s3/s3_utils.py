import os
import boto3
import uuid
from botocore.exceptions import ClientError
from csvpath.util.box import Box
from csvpath.util.config import Config


class S3Utils:
    AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
    _client_count = 0

    @classmethod
    def make_client(cls):
        box = Box()
        client = box.get(Box.BOTO_S3_CLIENT)
        if client is None:
            cls._client_count += 1
            import warnings

            warnings.filterwarnings(
                action="ignore", message=r"datetime.datetime.utcnow"
            )
            #
            # changing this to allow for lookups using the var sub env.json instead
            # of doing an OS env var lookup directly. we'll check the config.ini first
            # do var sub, if needed. fall back to direct env lookup using OS or env.json
            # depending which is configured.
            #
            config = box.get(Box.CSVPATHS_CONFIG)
            if config is None:
                config = Config()
            ak = config.get(section="s3", name=cls.AWS_ACCESS_KEY_ID)
            if ak is None or ak == cls.AWS_ACCESS_KEY_ID:
                ak = config.get(section=None, name=cls.AWS_ACCESS_KEY_ID)
            sk = config.get(section="s3", name=cls.AWS_SECRET_ACCESS_KEY)
            if sk is None or sk == cls.AWS_SECRET_ACCESS_KEY:
                sk = config.get(section=None, name=cls.AWS_SECRET_ACCESS_KEY)
            session = boto3.Session(
                aws_access_key_id=ak,
                aws_secret_access_key=sk,
            )
            """
            session = boto3.Session(
                aws_access_key_id=os.environ[cls.AWS_ACCESS_KEY_ID],
                aws_secret_access_key=os.environ[cls.AWS_SECRET_ACCESS_KEY],
            )
            """
            client = session.client("s3")
            box.add(Box.BOTO_S3_CLIENT, client)
        return client

    @classmethod
    def path_to_parts(self, path) -> tuple[str, str]:
        if path.startswith("s3://"):
            path = path[5:]
        b = path.find("/")
        key = None
        if b > -1:
            bucket = path[0:b]
            key = path[b + 1 :]
        else:
            bucket = path
        if key is None or key.strip() == "":
            key = "/"
        t = (bucket, key)
        return t

    @classmethod
    def exists(self, bucket: str, key: str, client) -> bool:
        if client is None:
            raise ValueError("Client cannot be None")
        try:
            import warnings

            warnings.filterwarnings(
                action="ignore", message=r"datetime.datetime.utcnow"
            )
            client.head_object(Bucket=bucket, Key=key)
        except ClientError as e:
            assert str(e).find("404") > -1
            return False
        except DeprecationWarning:
            ...
        return True

    @classmethod
    def remove(self, bucket: str, key: str, client) -> None:
        #
        # see csvpath.util.Nos.remove() for a remove that deletes all children.
        # s3 children are essentially completely independent of their
        # notionally containing parents.
        #
        if client is None:
            raise ValueError("Client cannot be None")
        client.delete_object(Bucket=bucket, Key=key)

    @classmethod
    def copy(
        self, bucket: str, key: str, new_bucket: str, new_key: str, client
    ) -> None:
        if client is None:
            raise ValueError("Client cannot be None")
        client.copy_object(
            Bucket=new_bucket,
            CopySource={"Bucket": bucket, "Key": key},
            Key=new_key,
            ChecksumAlgorithm="SHA256",
        )

    @classmethod
    def rename(self, bucket: str, key: str, new_key: str, client) -> None:
        if client is None:
            raise ValueError("Client cannot be None")
        S3Utils.copy(bucket, key, bucket, new_key, client=client)
        S3Utils.remove(bucket, key, client=client)
