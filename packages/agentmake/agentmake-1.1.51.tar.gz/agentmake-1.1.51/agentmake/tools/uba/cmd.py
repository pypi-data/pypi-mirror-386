TOOL_SYSTEM = ""
TOOL_SCHEMA = {}
TOOL_DESCRIPTION = """Run Unique Bible App UBA commands"""

def uba_api(messages, **kwargs):
    from agentmake.utils.online import get_local_ip
    import requests, os
    import urllib.parse

    command = messages[-1].get("content", "")
    command = urllib.parse.quote(command)

    UBA_API_LOCAL_PORT = int(os.getenv("UBA_API_LOCAL_PORT")) if os.getenv("UBA_API_LOCAL_PORT") else 8080
    UBA_API_ENDPOINT = os.getenv("UBA_API_ENDPOINT") if os.getenv("UBA_API_ENDPOINT") else f"http://{get_local_ip()}:{UBA_API_LOCAL_PORT}/plain" # use dynamic local ip if endpoint is not specified
    UBA_API_TIMEOUT = int(os.getenv("UBA_API_TIMEOUT")) if os.getenv("UBA_API_TIMEOUT") else 10
    UBA_API_PRIVATE_KEY = os.getenv("UBA_API_PRIVATE_KEY") if os.getenv("UBA_API_PRIVATE_KEY") else ""

    endpoint = UBA_API_ENDPOINT
    private = f"private={UBA_API_PRIVATE_KEY}&" if UBA_API_PRIVATE_KEY else ""
    url = f"""{endpoint}?{private}cmd={command}"""
    try:
        response = requests.get(url, timeout=UBA_API_TIMEOUT)
        response.encoding = "utf-8"
        print(response.text.strip())
    except Exception as err:
        print(f"An error occurred: {err}")
    
    return ""

TOOL_FUNCTION = uba_api