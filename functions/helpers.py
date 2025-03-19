import requests, json
import html.parser
import datetime as dt
from auth_code_req import get_access_token

class HTMLTextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super(HTMLTextExtractor, self).__init__()
        self.result = [ ]

    def handle_data(self, d):
        self.result.append(d)

    def get_text(self):
        return ''.join(self.result)

def html_to_text(html):
    """Converts HTML to plain text (stripping tags and converting entities).
    >>> html_to_text('<a href="#">Demo<!--...--> <em>(&not; \u0394&#x03b7;&#956;&#x03CE;)</em></a>')
    'Demo (\xac \u0394\u03b7\u03bc\u03ce)'

    "Plain text" doesn't mean result can safely be used as-is in HTML.
    >>> html_to_text('&lt;script&gt;alert("Hello");&lt;/script&gt;')
    '<script>alert("Hello");</script>'

    Always use html.escape to sanitize text before using in an HTML context!

    HTMLParser will do its best to make sense of invalid HTML.
    >>> html_to_text('x < y &lt z <!--b')
    'x < y < z '

    Named entities are handled as per HTML 5.
    >>> html_to_text('&nosuchentity; &apos; ')
    "&nosuchentity; ' "
    """
    if html == None:
        return ''
    
    s = HTMLTextExtractor()
    s.feed(html)
    return s.get_text()

def get_replies(team_id, channel_id, message_id,secret) :
    base_url = 'https://graph.microsoft.com/v1.0/'
    access_token = get_access_token(secret)
    headers = {
        'Authorization': 'Bearer ' + access_token[0]
    }

    endpoint = base_url + 'teams/' + team_id + '/channels/' + channel_id + f'/messages/{message_id}/replies'
    response = requests.get(endpoint, headers=headers)
    data = json.loads(response.content)
    if 'value' in data:
        return data['value']
    else:
        return []

def format_timedelta(time):
    s = int(time.total_seconds())
    # hours
    hours = s // 3600 
    # remaining seconds
    s = s - (hours * 3600)
    # minutes
    minutes = s // 60
    # remaining seconds
    seconds = s - (minutes * 60)
    # total time
    # return str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
    return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

def excel_date(date1):
    if isinstance(date1, dt.timedelta):
        return format_timedelta(date1)
    else:
        temp = dt.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
        delta = date1.replace(tzinfo=None) - temp
        return float(delta.days) + (float(delta.seconds) / 86400)

def valid_excel_title(title):
    invalid_chars = ["/", "*", "?", "[", "]", ":"]
    valid_list = []
    for char in title:
        if char in invalid_chars:
            valid_list.append("_")
        else:
            valid_list.append(char)
    valid_title = "".join(valid_list)
    return valid_title[:32]

def post_message_to_teams(webhook_url, message, title=None):
    """
    Posts a message to a Microsoft Teams channel using an Incoming Webhook.

    Parameters:
    webhook_url (str): The webhook URL for the Teams channel.
    message (str): The message to send.
    title (str, optional): The title of the message (default is None).

    Returns:
    dict: The response from the Teams webhook API.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "text": message
    }
    
    if title:
        payload = {
            "title": title,
            "text": message
        }

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        print("Message posted successfully!")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to post message: {e}")
        return {"error": str(e)}

def get_credentials(secret):
    
    data_io_channels = json.loads(secret.get("data_io_channels_to_query","[]"))  

    channels_to_query = data_io_channels[0]['readfrom']

    teams_channel = data_io_channels[0]['writeto'][0]

    DATA_IO_URL = secret.get('data_io_channel_url')
    

    channels_to_post = {'team_id':teams_channel['team_id'],'channel_id':teams_channel['channel_id']}
    
    return channels_to_query,channels_to_post, DATA_IO_URL
