from azure.identity import UsernamePasswordCredential, ClientSecretCredential
from datetime import datetime

# SCOPES = ['User.Read', 'Files.ReadWrite.All', 'ChannelSettings.Read.All', 'Channel.ReadBasic.All', 'ChannelMessage.Read.All', 'Sites.Read.All', 'Sites.ReadWrite.All']

access_token = None

def is_token_expired(access_token):

    expires_on = datetime.utcfromtimestamp(access_token[1])
    current_time = datetime.utcnow()
    
    return current_time > expires_on

def get_secrets_for_client_credentials(secret):
    
    SCOPES = ['https://graph.microsoft.com/.default']
    

    tenant_id = secret.get('tenant_id',None)
    client_id = secret.get('client_id',None)
    client_secret = secret.get('client_secret',None)
        
    if not all([client_secret, tenant_id, client_id]):
        raise ValueError("Missing required keys in secret for access token.")
    
    return client_secret,tenant_id,client_id,SCOPES

def get_access_token(secret):
    global access_token
    if not access_token or is_token_expired(access_token):
        client_secret,tenant_id,client_id,SCOPES = get_secrets_for_client_credentials(secret)
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        access_token = credential.get_token(*SCOPES)

    return access_token or None

