from azure.identity import UsernamePasswordCredential
from datetime import datetime

# SCOPES = ['User.Read', 'Files.ReadWrite.All', 'ChannelSettings.Read.All', 'Channel.ReadBasic.All', 'ChannelMessage.Read.All', 'Sites.Read.All', 'Sites.ReadWrite.All']
def get_secrets_for_access_token(secret):
    
    SCOPES = ['https://graph.microsoft.com/.default']
    
    account_username = secret.get('msgraph_username',None)
    account_password = secret.get('msgraph_password',None)
    tenant_id = secret.get('tenant_id',None)
    client_id = secret.get('client_id',None)
    
    if not all([account_username, account_password, tenant_id, client_id]):
        raise ValueError("Missing required keys in secret for access token.")
    
    return account_username,account_password,tenant_id,client_id,SCOPES


access_token = None

def is_token_expired(access_token):

    expires_on = datetime.utcfromtimestamp(access_token[1])
    current_time = datetime.utcnow()
    
    return current_time > expires_on

def get_access_token(secret):

    global access_token

    if not access_token or is_token_expired(access_token):
        account_username,account_password,tenant_id,client_id,SCOPES = get_secrets_for_access_token(secret)
        credential = UsernamePasswordCredential(
        username=account_username,
        password=account_password,
        client_id=client_id,
        tenant_id=tenant_id
        )
        access_token = credential.get_token(*SCOPES)

    return access_token or None

