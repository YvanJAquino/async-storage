from httpx import Client, Request


class Metadata:

    BASE_URL = 'http://metadata.google.internal/computeMetadata/v1/'
    HEADERS = {'Metadata-Flavor': 'Google'}
    PARAMS = {'alt': 'json'}
    PROJECT_ID = 'project/project-id'
    PROJECT_NUMBER = 'project/numeric-project-id'
    TOKEN = 'instance/service-accounts/{service_account}/token'
    IDENTITY = 'instance/service-accounts/{service_account}/identity'
    RECURSIVE = {'recursive': 'true'}

    def __init__(self):
        self.client = Client(
            base_url=self.BASE_URL,
            headers=self.HEADERS,
            params=self.PARAMS
        )

    def __del__(self):
        self.client.close()
    
    def get_project_id(self):
        request = self.client.build_request('GET', self.PROJECT_ID)
        response = self.client.send(request)
        return response.json()

    def get_project_number(self):
        request = self.client.build_request('GET', self.PROJECT_NUMBER)
        response = self.client.send(request)
        return response.json()

    def project_id_request(self):
        return self.client.build_request(
            'GET',
            self.PROJECT_ID
        )

    def project_number_request(self):
        return self.client.build_request(
            'GET',
            self.PROJECT_NUMBER
        )

    def get_service_account_token(self, service_account='default'):
        request = self.client.build_request(
            'GET', 
            self.TOKEN.format(service_account=service_account), 
            params=self.RECURSIVE
        )
        response = self.client.send(request)
        return response.json()['access_token']

    def service_account_token_request(self, service_account='default'):
        return self.client.build_request(
            'GET', 
            self.TOKEN.format(service_account=service_account), 
            params=self.RECURSIVE
        )

    def get_service_account_id_token(self, audience, service_account='default'):
        params = {'audience': audience}
        params.update(self.RECURSIVE)
        request = self.client.build_request(
            'GET',
            self.IDENTITY.format(service_account=service_account),
            params=params
        )
        response = self.client.send(request)
        return response.content.decode()

    def service_account_id_token_request(self, audience, service_account='default'):
        params = {'audience': audience}
        params.update(self.RECURSIVE)
        return self.client.build_request(
            'GET',
            self.IDENTITY.format(service_account=service_account),
            params=params
        )


# if __name__ == '__main__':
#     md = Metadata()
#     print(md.get_project_number())
