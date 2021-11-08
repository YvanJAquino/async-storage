import warnings
from typing import Union, List
from httpx import Request, Auth
from metadata_v2 import Metadata

from auth_models import Portal, OAuthRequest, OAuthTokenResponse

TOKEN_TYPES = (
        'access',
        'identity'
    )

IDENTITY_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'


class TokenTypeError(Exception):
    ...


class MetadataAuth(Auth):

    requires_response_body = True

    def __init__(self, token_type='access', audience=None, service_account='default'):
        if token_type not in TOKEN_TYPES:
            raise TokenTypeError('token_type must be set to "access" or "identity"') 
        self.token = None
        self.token_type = token_type
        self.audience = audience
        self.service_account = service_account
        self.metadata = Metadata()

    def auth_flow(self, request):
        request.headers['Authorization'] = f'Bearer {self.token}'
        response = yield request
        
        if response.status_code == 401:
            if self.token_type == 'access':
                refresh_response = yield self.metadata.service_account_token_request()
                self.token = refresh_response.json()['access_token']
            elif self.token_type == 'identity':
                refresh_response = yield self.metadata.service_account_id_token_request(self.audience)
                self.token = refresh_response.content.decode()


class UserAuth(Auth):

    requires_response_body = True

    def __init__(self, 
        oauth_portal: Union[str, dict], scopes: Union[List[str], str], 
        token_type='access', audience: str=None):
        if token_type not in TOKEN_TYPES:
            raise TokenTypeError('token_type must be set to "access" or "identity"') 
        if token_type == 'identity' and audience is None:
            warnings.warn("When no audience is provided, your OAuth portal's client ID is the audience.")
        if token_type == 'identity':
            # if this is a id_token request, make sure the identity scopes are
            # in the list of scopes, else add them.  
            for scope in IDENTITY_SCOPES:
                if scope not in scopes:
                    scopes.append(scope)

        self.token = None
        self.token_type = token_type
        self.oauth_portal = oauth_portal
        self.scopes = scopes
        self.audience = audience
        self.portal_config = None
        self.portal_type = None
        self.oauth_request = None
        self.oauth_response = None

        self.portal_to_config()

    def portal_to_config(self):
        # Converts the portal file or portal dict into a Portal model.  
        if isinstance(self.oauth_portal, dict):
            for portal_type, portal_config in self.oauth_portal.items():
                oauth_portal = Portal(portal_type=portal_type, portal_config=portal_config)
        if isinstance(self.oauth_portal, str):
            oauth_portal = Portal.from_json(self.oauth_portal)
        self.portal_type = oauth_portal.portal_type
        self.portal_config = oauth_portal.portal_config

    def oauth_flow(self):
        # Scopes checked during initialization.  
        self.oauth_request = OAuthRequest.from_portal_config(self.portal_config, self.scopes)
        url = self.oauth_request.authorization_url()
        print(f'Please review, consent, and copy the auth code: {url}')
        code = input('Paste the auth code here:')
        return self.oauth_request(code)

    def auth_flow(self, request):
        
        request.headers['Authorization'] = f'Bearer {self.token}'
        response = yield request
        
        if response.status_code == 401:
            if self.oauth_response and not self.oauth_response.valid:
                # Refresh flow.  
                ...
            else:
                refresh_response = yield self.oauth_flow()
                self.oauth_response = OAuthTokenResponse.from_response(refresh_response)
                self.token = self.oauth_response.get_token(self.token_type)

    def pickle(self, fpath='UserAuth.pkl'):
        import pickle
        with open(fpath, 'wb') as dest:
            pickle.dump(self, dest)
                   
    def __del__(self):
        self.pickle()

    @staticmethod
    def from_pickle(fpath='UserAuth.pkl'):
        import pickle
        with open(fpath, 'rb') as src:
            user_auth = pickle.load(src)
        return user_auth


# if __name__ == '__main__':
#     from httpx import Client
#     from rich import print

#     url = 'https://storage.googleapis.com/storage/v1/b'
#     oauth_portal = 'oauth_portal.json'
#     scopes = [
#     'openid',
#     'https://www.googleapis.com/auth/userinfo.email',
#     'https://www.googleapis.com/auth/userinfo.profile',
#     'https://www.googleapis.com/auth/cloud-platform'
#     ]

#     auth = UserAuth(oauth_portal, scopes)
#     with Client(auth=auth) as client:
#         request = client.build_request('GET', url, params={'project': 'holy-diver-297719'})
#         response = client.send(request)
#         print(response)


    # with Client(auth=MetadataAuth()) as client:
    #     request = client.build_request('GET', url, params={'project': 'holy-diver-297719'})
    #     # request = client.build_request('GET', 'https://www.icanhazdadjoke.com', headers={'accept': 'application/json'})
    #     print(vars(request))
    #     response = client.send(request)
    #     print(response)
    #     request = client.build_request('GET', url, params={'project': 'holy-diver-297719'})
    #     # request = client.build_request('GET', 'https://www.icanhazdadjoke.com', headers={'accept': 'application/json'})
    #     print(vars(request))
    #     response = client.send(request)
    #     print(response)


    # https://accounts.google.com/o/oauth2/approval/v2/approvalnativeapp?
        # auto=false&
        # response=code%3D4%2F1AX4XfWgoVrx_KKI24mB1MNJCJaQusGwZ3fyZBhtxXgek30dJANbFPK8QaHo%26scope%3Demail%2520profile%2520openid%2520https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email%2520https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile%2520https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform%26authuser%3D0%26hd%3Dcloud-colosseum.net%26prompt%3Dconsent&
        # hl=en&
        # approvalCode=4%2F1AX4XfWgoVrx_KKI24mB1MNJCJaQusGwZ3fyZBhtxXgek30dJANbFPK8QaHo