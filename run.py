from __future__ import print_function
from asyncio import events
from calendar import calendar
from apiclient.discovery import build

import datetime
import os.path
from httplib2 import Http
from oauth2client import file, client, tools
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/meetings')
def main():
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

    except HttpError as error:
        print('An error occurred: %s' % error)
    return jsonify({"data": events_result})


@app.route('/schedule')
def info():
    store = file.Storage('storage.json')
    creds = store.get()
    try:
        import argparse

        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store, flags) \
            if flags else tools.run(flow, store)

    CAL = build('calendar', 'v3', http=creds.authorize(Http()))

    GMT_OFF = '+05:30'
    EVENT = {
        'summary': 'Team Dinner',
        'location': 'FML, Pune',
        'start': {'dateTime': '2022-08-27T19:00:00%s' % GMT_OFF},
        'end': {'dateTime': '2022-08-27T22:00:00%s' % GMT_OFF},
        'attendees': [
            {'email': 'apoorv@rapidinnovation.dev'},
            {'email': 'reshmasadhu@rapidinnovation.dev'},
            {'email': 'abhisheknegi@rapidinnovation.dev'},
            {'email': 'pravin@rapidinnovation.dev'},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    event = CAL.events().insert(calendarId='primary', sendNotifications=True, body=EVENT).execute()
    print(event)
    return jsonify({'info': event})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
