import datetime
import uuid
import jwt
import requests
from urllib.parse import urlparse

def generate_jwt_token(secret_id, secret_value, client_id, username, token_expiry_minutes=1):
    scopes = [
        "tableau:views:embed",
        "tableau:views:embed_authoring",
        "tableau:insights:embed",
        "tableau:viz_data_service:read",
    ]
    
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=token_expiry_minutes)
    
    payload = {
        "iss": client_id,
        "exp": exp,
        "jti": str(uuid.uuid4()),
        "aud": "tableau",
        "sub": username,
        "scp": scopes,
    }
    
    token = jwt.encode(
        payload,
        secret_value,
        algorithm="HS256",
        headers={
            "kid": secret_id,
            "iss": client_id,
        },
    )
    
    return token

def signin_with_jwt(server, jwt_token, site_content_url, api_version="3.26"):
    url = f"{server}/api/{api_version}/auth/signin"
    headers = {"Content-Type": "application/xml", "Accept": "application/json"}
    body = f"""
<tsRequest>
<credentials jwt="{jwt_token}">
    <site contentUrl="{site_content_url}"/>
</credentials>
</tsRequest>
""".strip()
    r = requests.post(url, headers=headers, data=body)
    r.raise_for_status()
    return r.json()["credentials"]["token"]

def extract_server_url(embed_url):
    if "/t/" in embed_url:
        return embed_url.split("/t/")[0]
    else:
        parsed = urlparse(embed_url)
        return f"{parsed.scheme}://{parsed.netloc}"