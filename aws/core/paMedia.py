import uuid, base64, boto3, io
from botocore.client import Config

media_types = {"bj": {"ext": "jpg", "type": "image"}, "bm": {"ext": "mp3", "type": "audio"}}


def key2type(k): return media_types.get(k[:2], None)


def ext2media(ext): return [v for k, v in media_types.items() if v['ext'] == ext][0]


def ext2format(ext): return f"{ext2media(ext)['type']}/{ext}"


def file2type(fname): return ext2format(fname.split(".")[1])


def media_fields(doc): return {k: key2type(k) for k in doc.keys() if key2type(k)}


class PAMedia:
    def __init__(self, bucket="promptart-media"):
        self.bucket = bucket
        self.s3 = boto3.client("s3")

    def fetchBytes(self, fname):
        buf = io.BytesIO()
        self.s3.download_fileobj(Bucket=self.bucket, Key=fname, Fileobj=buf)
        return buf

    def saveBytes(self, buf, ext):
        fname = f"{uuid.uuid4()}.{ext}"
        self.s3.put_object(Body=buf, Bucket="promptart-media", Key=fname)
        return fname

    def fetchBase64(self, fname):
        return base64.b64encode(self.fetchBytes(fname).getvalue()).decode('ascii')

    def saveBase64(self, val_str, type):
        fname = f"{uuid.uuid4()}.{type}"
        self.s3.put_object(Body=io.BytesIO(base64.b64decode(val_str)).getvalue(), Bucket="promptart-media", Key=fname)
        return fname

    def fetchDocMedia(self, doc):
        for k in media_fields(doc).keys():  doc[k] = self.fetchBase64(doc[k])
        return doc

    def saveDocMedia(self, doc):
        for k, v in media_fields(doc).items(): doc[k] = self.saveBase64(doc[k], v['ext'])
        return doc

    def deleteDocMedia(self, doc):
        doc_content = doc["content"]
        for k, v in media_fields(doc_content).items(): self.s3.delete_object(Bucket=self.bucket, Key=doc_content[k])
        return doc
