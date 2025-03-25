import requests, json, csv, varname, os, traceback
from dateutil import parser as time_parser
import datetime as dt
import pytz
import pandas as pd
from dateutil.relativedelta import relativedelta
from auth_code_req import get_access_token
from team_upload import upload_file_to_teams_channel
from secretmanager import get_secret
import time
import logging
from helpers import html_to_text, get_replies,valid_excel_title, get_credentials,excel_date,post_message_to_teams

def handler(event,context):
    try:
        secret_name = os.environ.get('SecretName')
        region = os.environ.get('Region')
        base_url = 'https://graph.microsoft.com/v1.0/'
        secret = get_secret(secret_name,region)
        
        access_token = get_access_token(secret)
        headers = {
            'Authorization': 'Bearer ' + access_token[0]
        }

        channels_to_query,channels_to_post, DATA_IO_URL = get_credentials(secret)
        
        first_day_current_month = dt.datetime.now().replace(day=1)

        last_day_previous_month = first_day_current_month - dt.timedelta(days=1)

        days_in_last_month = last_day_previous_month.day
        
        query_time_ago = dt.datetime.now() - dt.timedelta(days=days_in_last_month)
        
        cutoff_date = query_time_ago.astimezone(pytz.timezone('America/Los_Angeles'))
        #fields = ['message_id', 'requester', 'content', 'response time', '1st response', 'first responder', '1st response text', 'last response', 'last responder', 'last response text']

        last_month_date = dt.datetime.now() - relativedelta(months=1)
        output_xlsx = f'/tmp/dataio_iqc_result_{last_month_date.year}{last_month_date.month}.xlsx'
        output_name = f'dataio_iqc_result_{last_month_date.year}{last_month_date.month}.xlsx'
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(output_xlsx, engine="xlsxwriter")

        count = 0
        for row in channels_to_query:
            try:
                team_id = row["team_id"]
                channel_id = row["channel_id"]
                title = row["name"]
                
                title = valid_excel_title(title)

                df = pd.DataFrame(
                    {
                        'id': [],
                        'time': [],
                        'requester': [],
                        'message': [],
                        'response time': [],
                        '1st response': [],
                        '1st responder': [],
                        '1st response text': [],
                        'last response': [],
                        'last responder': [],
                        'last response text': []
                    }
                )
                endpoint = base_url + 'teams/' + team_id + '/channels/' + channel_id + '/messages'
                section_count = 0

                start_time_before_while = time.time()
                while endpoint:
                    response = requests.get(endpoint, headers=headers)
                    start_time_for_end_point = time.time()
                    response.raise_for_status() 

                    messages = json.loads(response.content)
                    completed = False
                    for m in messages['value']:
                        data = get_replies(team_id, channel_id, m['id'],secret)
                        start_time = time_parser.parse(m['createdDateTime'])
                        if start_time < cutoff_date or section_count > 2000:
                            print(f'{count} records found in {title}')
                            completed = True
                            break

                        if len(data) > 0:
                            response_time = time_parser.parse(data[-1]['createdDateTime'])
                            delay = response_time - start_time
                            new_row = {
                                'id': m['id'], 
                                'time': excel_date(start_time),
                                'requester':  m['from']['user']['displayName'] if m['from'] and m['from']['user'] else '',
                                'message':  html_to_text(m['body']['content']),
                                'response time':  excel_date(delay),
                                '1st response':  excel_date(response_time),
                                '1st responder':  data[-1]['from']['user']['displayName'] if data[-1]['from'] and  data[-1]['from']['user'] else '',
                                '1st response text':  html_to_text(data[-1]['body']['content']),
                                'last response':  excel_date(time_parser.parse(data[0]['createdDateTime'])),
                                'last responder':  data[0]['from']['user']['displayName'] if data[0]['from'] and data[0]['from']['user'] else '',
                                'last response text':  html_to_text(data[0]['body']['content'])
                            }
                            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        else:
                            new_row = {
                                'id': m['id'], 
                                'time': excel_date(start_time),
                                'requester':  m['from']['user']['displayName'] if m['from'] and m['from']['user'] else '',
                                'message':  m['body']['content'] if m['body'] else '',
                                'response time':  '',
                                '1st response':  '',
                                '1st responder':  '',
                                '1st response text':  '',
                                'last response':  '',
                                'last responder':  '',
                                'last response text':  ''
                            }
                            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        count += 1
                        section_count += 1
                    if not completed and '@odata.nextLink' in messages:
                        endpoint = messages['@odata.nextLink']
                        elapsed_time_in_endpoint = time.time() - start_time_for_end_point
                        logging.info(f"endpoint took {elapsed_time_in_endpoint:.2f} seconds.")
                    else:
                        endpoint = None

                elapsed_time_after_while = time.time() - start_time_before_while
                logging.info(f"endpoint loop took {elapsed_time_after_while:.2f} seconds.")
                # Convert the dataframe to an XlsxWriter Excel object.
                df.to_excel(writer, sheet_name=title, index=False)
                # Get the xlsxwriter workbook and worksheet objects.
                workbook = writer.book
                worksheet = writer.sheets[title]

                # Add some cell formats.
                format1 = workbook.add_format({"num_format": "#,##0"})
                format2 = workbook.add_format({"num_format": "mm/dd/yy hh:mm:ss"})

                # Note: It isn't possible to format any cells that already have a format such
                # as the index or headers or any cells that contain dates or datetimes.

                # Set the column width and format.
                worksheet.set_column('A:A', 18, format1)
                worksheet.set_column('B:B', 18, format2)
                worksheet.set_column('C:C', 12, format2)
                worksheet.set_column('D:D', 36, format2)
                worksheet.set_column('F:F', 18, format2)
                worksheet.set_column('G:G', 12, format2)
                worksheet.set_column('H:H', 36, format2)
                worksheet.set_column('I:I', 18, format2)
                worksheet.set_column('J:J', 12, format2)
                worksheet.set_column('K:K', 36, format2)
            except Exception as error:
                print(f"Failed this table: {title} + with stacktrace {traceback.format_exc()}" )
                pass
        # Close the Pandas Excel writer and output the Excel file.
        writer.close()


        #team id and channel id for Data IO iQC Analytics (output)
        TEAM_ID = channels_to_post['team_id']
        CHANNEL_ID = channels_to_post['channel_id']
        
        # Upload the file to Teams channel "Data IO iQC Analytics"
        url = upload_file_to_teams_channel(TEAM_ID, CHANNEL_ID, output_xlsx, output_name,secret)

        post_message_to_teams(DATA_IO_URL,
                            f'Here is analytics result for last month: [{output_name}]({url})\n')
        
        return {
            'statusCode': 200,
            'body': url
        }
        
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_message})
        }
