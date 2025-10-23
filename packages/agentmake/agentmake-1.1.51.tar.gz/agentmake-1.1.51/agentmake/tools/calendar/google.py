"""
ToolMate AI Plugin - add calender event

supported calendars:
* google calendar
* outlook calendar

[TOOL_CALL]
"""

"""
# Information gathered for plugin creation

Example: Google Calendar URL
```https://calendar.google.com/calendar/render?action=TEMPLATE
&text=Event%20Title
&dates=START_DATE/TIME/END_DATE/TIME
&details=Event%20Description%20with%20URL:%20URL_HERE
&location=Event%20Location
```

Replace the following placeholders in the URL:

- `Event%20Title`: The title or name of the event. If the title contains spaces, replace the spaces with `%20`.
- `START_DATE/TIME`: The start date and time of the event in the format `YYYYMMDDTHHmmss`. For example, `20220101T100000` represents January 1, 2022, at 10:00 AM.
- `END_DATE/TIME`: The end date and time of the event in the same format as the start date and time.
- `Event%20Description%20with%20URL:%20URL_HERE`: The description of the event, including the URL. Replace `URL_HERE` with the actual URL you want to include. If the description contains spaces, replace the spaces with `%20`.
- `Event%20Location`: The location or venue of the event. If the location contains spaces, replace the spaces with `%20`.
"""

"""
Example: Outlook Calendar URL
To add a calendar event to Microsoft Outlook web version using a single URL, you can use the following format:

https://outlook.office.com/owa/?path=/calendar/action/compose&rru=addevent&subject=Title&location=Location&body=Description&startdt=StartDateTime&enddt=EndDateTime

You need to replace the parameters with the values you want, such as:

Title: The title of the event (URL encoded format).
Location: The location of the event (URL encoded format).
Description: The description of the event (URL encoded format).
StartDateTime: The start date and time of the event in ISO 8601 format (YYYY-MM-DDTHH:MM:SS+/-HH:MM).
EndDateTime: The end date and time of the event in ISO 8601 format (YYYY-MM-DDTHH:MM:SS+/-HH:MM).
For example, if you want to create an event with the following details:

Title: Meeting with John
Location: Office
Description: Discuss project progress and next steps
Start date and time: October 15, 2023 at 10:00 AM GMT
End date and time: October 15, 2023 at 11:00 AM GMT
You can use this URL:

https://outlook.office.com/owa/?path=/calendar/action/compose&rru=addevent
&subject=Meeting%20with%20John
&location=Office
&body=Discuss%20project%20progress%20and%20next%20steps
&startdt=2023-10-15T10%3A00%3A00%2B00%3A00
&enddt=2023-10-15T11%3A00%3A00%2B00%3A00

When you click on this URL, it will open a new window in Outlook web app and fill in the event details for you. You can then save or edit the event as you wish.
"""

import re, datetime

CURRENT_DATETIME = re.sub(r"\..*?$", "", str(datetime.datetime.now()))
CURRENT_DAY = datetime.date.today().strftime("%A")
CONVERT_RELATIVE_DATETIME = f"""Calculate the exact dates and times from the relative ones, if any, based on the reference that the current datetime is {CURRENT_DATETIME} ({CURRENT_DAY})."""

def add_google_calendar_event(title, description, url="", start_time="", end_time="", location="", **kwargs):

    from agentmake.utils.online import openURL
    import datetime, re
    import urllib.parse

    calendar = calendar = "google" # required

    start_time = f"{re.sub('Z$', '', start_time.replace('-', ''))}000000"[:15]
    end_time = f"{re.sub('Z$', '', end_time.replace('-', ''))}000000"[:15]

    title = urllib.parse.quote(title)
    description = urllib.parse.quote(description)
    location = urllib.parse.quote(location)

    def getGoogleLink():
        link = "https://calendar.google.com/calendar/render?action=TEMPLATE"
        if title:
            link += f"&text={title}"
        if start_time:
            link += f"&dates={start_time}"
        if end_time:
            link += f"/{end_time}"
        if description:
            link += f"&details={description}"
        if url:
            link += f"%20with%20URL:%20{url}"
        if location:
            link += f"&location={location}"
        return link

    def getOutlookLink():

        def datetime_to_ISO8601(datetime_str):
            # Parse the input string using the specified format
            datetime_obj = datetime.datetime.strptime(datetime_str, '%Y%m%dT%H%M%S')
            # ISO8601
            formatted_str = datetime_obj.strftime('%Y-%m-%dT%H%%3A%M%%3A%S')
            return formatted_str

        link = "https://outlook.office.com/owa/?path=/calendar/action/compose&rru=addevent"
        if title:
            link += f"&subject={title}"
        if start_time:
            link += f"&startdt={datetime_to_ISO8601(start_time)}%2B00%3A00"
        if end_time:
            link += f"&enddt={datetime_to_ISO8601(end_time)}%2B00%3A00"
        if description:
            link += f"&body={description}"
        if url:
            link += f"%20with%20URL:%20{url}"
        if location:
            link += f"&location={location}"
        return link

    openURL(getOutlookLink() if calendar == "outlook" else getGoogleLink())

    return ""

TOOL_SCHEMA = {
    "name": "add_google_calendar_event",
    "description": "Add a Google calendar event",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the event.",
            },
            "description": {
                "type": "string",
                "description": "The detailed description of the event, including the people involved and their roles, if any.",
            },
            "url": {
                "type": "string",
                "description": "Event url",
            },
            "start_time": {
                "type": "string",
                "description": f"The start date and time of the event in the format `YYYYMMDDTHHmmss`. For example, `20220101T100000` represents January 1, 2022, at 10:00 AM. {CONVERT_RELATIVE_DATETIME}",
            },
            "end_time": {
                "type": "string",
                "description": f"The end date and time of the event in the format `YYYYMMDDTHHmmss`. For example, `20220101T100000` represents January 1, 2022, at 10:00 AM. {CONVERT_RELATIVE_DATETIME} If not given, return 1 hour later than the start_time",
            },
            "location": {
                "type": "string",
                "description": "The location or venue of the event.",
            },
        },
        "required": ["title", "description"],
    },
}

TOOL_FUNCTION = add_google_calendar_event