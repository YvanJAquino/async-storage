import asyncio
from httpx import AsyncClient, Request, Client, Auth
from sniffio import AsyncLibraryNotFoundError
from auth import MetadataAuth
from metadata import MetadataServer
from models import Buckets, Bucket, Blobs, Blob


class StorageBucket:

    def __init__(self, client: AsyncClient, bucket: Bucket):
        self.client = client
        self.bucket = bucket


class AsyncHttpxClient:

    def __init__(self, 
        base_url=None, 
        headers=None, 
        params=None, 
        service_account='default'
    ):
        self.client = AsyncClient(
            auth=MetadataAuth(service_account=service_account),
            base_url=base_url,
            headers=headers,
            params=params
        )
        self.loop = asyncio.get_event_loop()

    async def close(self):
        return await self.client.aclose()

    def __del__(self):
        try:
            self.loop.run_until_complete(self.close())
        except AsyncLibraryNotFoundError:
            pass
        self.loop.close()

    def build_request(self, method, url, **kwargs):
        return self.client.build_request(method, url, **kwargs)

    async def send(self, request: Request):
        return await self.client.send(request)

    async def send_many(self, requests: list[Request]):
        awaitables = [
            self.send(request)
            for request in requests
        ]
        return await asyncio.gather(awaitables)

    def execute(self, coro):
        return self.loop.run_until_complete(coro)

    def execute_send(self, request):
        return self.execute(
            self.send(request)
        )


class AsyncStorageClient(AsyncHttpxClient):

    BASE_URL = 'https://storage.googleapis.com/storage/v1'
    HEADERS = {}
    PARAMS = {}
    LIST_BUCKETS = '/b'
    GET_BUCKET = '/b/{bucket}'
    LIST_BLOBS = '/b/{bucket}/o'

    def __init__(self, 
        project_id=None,
        service_account='default'
    ):
        self.metadata = MetadataServer()
        self.project = self.metadata.get_project_id() if not project_id else project_id

        super().__init__(
            base_url=self.BASE_URL,
            headers=self.HEADERS,
            params=self.PARAMS,
            service_account=service_account
        )
    
    def list_buckets(self, output='model'):
        request = self.build_request('GET', self.LIST_BUCKETS, params={'project': self.project})
        response = self.execute_send(request).json() 
        if output == 'model':
            return (
                Bucket(**bucket.dict())
                for bucket in Buckets(**response).items 
            )
        elif output in ('response','dict'):
           return response
    
    def get_bucket(self, bucket, output='model'):
        request = self.build_request('GET', self.GET_BUCKET.format(bucket=bucket))
        response = self.execute_send(request).json()
        if output == 'model':
            return Bucket(**response, client=self.client)
        elif output in ('response', 'dict'):
            return response

    def list_blobs(self, bucket, output='model'):
        request = self.build_request('GET', self.LIST_BLOBS.format(bucket=bucket))
        response = self.execute_send(request).json()
        if output == 'model':
            return (
                Blob(**blob.dict())
                for blob in Blobs(**response).items
            )
        elif output in ('response', 'dict'):
            return response

    def get_blob(self):
        # implement get blob
        # Using Range header - can we replace this with an iterator / lazy approach instead for streaming?
        pass

    def get_blobs(self):
        # implement get blobs.  Asynchronous Blob getting ... :-p
        pass


if __name__ == '__main__':
    import json
    gcs = AsyncStorageClient()
    buckets = gcs.list_buckets()
    blobs = gcs.list_blobs('holy-diver-297719-input')
    bucket = gcs.get_bucket('holy-diver-297719-input')
    print(bucket)