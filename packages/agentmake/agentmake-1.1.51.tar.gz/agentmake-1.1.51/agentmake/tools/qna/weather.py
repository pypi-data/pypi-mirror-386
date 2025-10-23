import os

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY").split(",") if os.getenv("OPENWEATHERMAP_API_KEY") else [""]

TOOL_SYSTEM = f"""You are a senior python engineer.
Generate python code that use my OpenWeatherMap API key '{OPENWEATHERMAP_API_KEY[0]}' to resolve my query about weather information.
In your code, use Celsius as the unit for temperature.
Remember, you should format the requested weather information into a string that is easily readable by humans.
Use the 'print' function in the last line of your generated code to display the weather information."""

def search_weather(code: str, **kwargs):

    from agentmake.utils.handle_python_code import fineTunePythonCode
    import os

    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY").split(",") if os.getenv("OPENWEATHERMAP_API_KEY") else [""]
    if not OPENWEATHERMAP_API_KEY[0]:
        print("OpenWeatherMap API key is required but not found! Read https://github.com/eliranwong/computemate/blob/main/docs/setup_others/openweather_API.md.")
        return ""

    refined_python_code = fineTunePythonCode(code)
    glob = {}
    loc = {}
    print("```output")
    exec(refined_python_code, glob, loc)
    print("```")
    return ""

TOOL_SCHEMA = {
    "name": "search_weather",
    "description": f'''Answer a query about weather; weather-related query is required.''',
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": f"""Generate python code that use my OpenWeatherMap API key '{OPENWEATHERMAP_API_KEY[0]}' to resolve my request. Use Celsius as the unit for temperature.""",
            },
        },
        "required": ["code"],
    },
}

TOOL_FUNCTION = search_weather
