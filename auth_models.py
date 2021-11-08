from typing import List, Optional, Union
from pydantic import BaseModel, validator

COPY_PASTE_URI = 'urn:ietf:wg:oauth:2.0:oob'


class InstalledPortal(BaseModel):
    client_id: str
    project_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_secret: str
    redirect_uris: List[str]


class WebPortal(BaseModel):
    client_id: str
    project_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_secret: str
    redirect_uris: List[str]


class Portal(BaseModel):
    portal_type: str
    portal_config: Union[InstalledPortal, WebPortal]

    @classmethod
    def from_json(cls, f):
        from json import load
        with open(f) as json_file:
            portal = load(json_file)
            for key, val in portal.items():
                portal_type = key
                portal_config = val
        return cls(portal_type=portal_type, portal_config=portal_config)


class OAuthRequest(BaseModel):
    client_id: str
    client_secret: str
    auth_uri: str
    token_uri: str
    redirect_uri: str
    response_type: str = 'code'
    access_type: str = 'offline'
    scope: Optional[Union[str, List[str]]]
    include_granted_scopes: str = 'true'
    code_verifier: Optional[str]
    code_challenge: Optional[str]
    code_challenge_method: Optional[str] = 'S256'
    # See here for a guide on how to generate a state token
    # https://developers.google.com/identity/protocols/oauth2/openid-connect#python
    state: Optional[str]
    login_hint: Optional[str]
    grant_type: str = 'authorization_code'

    @validator('code_verifier', always=True, pre=True)
    def _code_verifier(cls, v):
        from secrets import SystemRandom
        from string import ascii_letters, digits
        chars = ascii_letters + digits + "-._~"
        picker = SystemRandom()
        return ''.join(picker.choice(chars) for _ in range(128))

    @validator('code_challenge', always=True)
    def _code_challenge(cls, v, values):
        from hashlib import sha256
        from base64 import urlsafe_b64encode
        code_hash = sha256()
        code_hash.update(str.encode(values['code_verifier']))
        unencoded_challenge = code_hash.digest()
        b64_challenge = urlsafe_b64encode(unencoded_challenge)
        return b64_challenge.decode().split("=")[0]

    @validator('scope')
    def _scope(cls, scopes):
        if isinstance(scopes, list):
            scope = ' '.join(scopes)
        elif isinstance(scopes, str):
            scope = scopes
        return scope


    @classmethod
    def from_portal_config(cls, portal_config, scopes, redirect_uri='urn:ietf:wg:oauth:2.0:oob', state=None):
        if not isinstance(portal_config, (WebPortal, InstalledPortal)):
            # add validation based on portal type
            print('It aint gonna work, Joe...')
        # add validation for redirect_uri
        scope = ' '.join(scopes)        
        return cls(
            client_id=portal_config.client_id,
            client_secret=portal_config.client_secret,
            auth_uri=portal_config.auth_uri,
            token_uri=portal_config.token_uri,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state
        )
    
    def authorization_url(self):
        from urllib.parse import urlunparse, urlparse, urlencode
        url = self.auth_uri
        _query = dict(
            client_id=self.client_id,
            response_type=self.response_type,
            redirect_uri=COPY_PASTE_URI,
            scope=self.scope,
            access_type=self.access_type,
            include_granted_scopes=self.include_granted_scopes,
            state=self.state,
            code_challenge=self.code_challenge,
            code_challenge_method=self.code_challenge_method
        )

        for key in list(_query):
            if not _query[key]:
                del _query[key]
        
        scheme, netloc, path, params, query, fragment = urlparse(url)
        query = urlencode(_query)
        return urlunparse((scheme, netloc, path, params, query, fragment))

    def __call__(self, code):
        from httpx import Request
        body = dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code,
            code_verifier=self.code_verifier,
            grant_type=self.grant_type,
            redirect_uri=self.redirect_uri
        )
        url = self.token_uri
        return Request(
            'POST',
            url,
            data=body
        )


class OAuthTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    scope: str
    scopes: Optional[str]
    token_type: str
    id_token: Optional[str]
    issued_at: Optional[int]
    expires_at: Optional[int]

    @validator('issued_at', always=True, pre=True)
    def _issued_at(cls, iat):
        import time
        return int(time.time())

    @validator('expires_at', always=True)
    def _expires_at(cls, exp, values):
        return values['issued_at'] + values['expires_in']

    @classmethod
    def from_response(cls, response):
        data = response.json()
        return cls(**data)

    def get_token(self, token_type):
        if token_type == 'access':
            token = self.access_token
        elif token_type == 'identity':
            token = self.id_token
        else:
            ...
        return token 

    @property
    def valid(self):
        import time
        return time.time() <= self.expires_at

# Review this class.  I dislike from_config_response method.  
class OAuthTokenRefreshRequest(BaseModel):
    token_uri: str
    client_id: str	                    #The client ID obtained from the API Console.
    client_secret: str	                #The client secret obtained from the API Console. (The client_secret is not applicable to requests from clients registered as Android, iOS, or Chrome applications.)
    grant_type: str = 'refresh_token'	#As defined in the OAuth 2.0 specification, this field's value must be set to refresh_token.
    refresh_token: str	                #The refresh token returned from the authorization code exchange.

    @classmethod
    def from_config_response(cls, portal_config, oauth_response):
        return cls(
            token_uri=portal_config.token_uri,
            client_id=portal_config.client_id,
            client_secret=portal_config.client_secret,
            refresh_token=oauth_response.refresh_token
        )

    def __call__(self):
        from httpx import Request
        refresh_request = self.dict()
        return Request(
            'POST',
            refresh_request.pop('token_uri'),
            data=refresh_request
        )

if __name__ == '__main__':
    from rich import print
    from urllib.parse import urlencode

    scopes = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/cloud-platform'
    ]
    model = Portal.from_json('oauth_portal.json')
    print(model.dict(exclude_none=True))
    oauth_request = OAuthRequest.from_portal_config(model.portal_config, scopes)
    url = oauth_request.authorization_url()
    print(url)

# https://accounts.google.com/o/oauth2/auth?
    # response_type=code&
    # client_id=1035334686051-tsr40fofegvks46alpo2b9okeiutra1g.apps.googleusercontent.com&
    # redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&
    # scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform&state=0DjI9GiRrndDf0qBjNuvfBtRCHEhfJ&
    # access_type=offline&
    # include_granted_scopes=true