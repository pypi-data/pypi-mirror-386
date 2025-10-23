from agentmake.utils.manage_package import installPipPackage
from agentmake import PACKAGE_PATH, getCurrentDateTime
import shutil, re, os

# install binary ffmpeg and python package yt-dlp to work with this plugin
if not shutil.which("yt-dlp"):
    installPipPackage("yt-dlp")
if not shutil.which("ffmpeg"):
    raise ValueError("Tool 'ffmpeg' is not found on your system! Read https://github.com/eliranwong/letmedoit/wiki/Install-ffmpeg for installation.")

# update once a date
currentDate = re.sub("_.*?$", "", getCurrentDateTime())
ytdlp_updated = os.path.join(PACKAGE_PATH, "temp", f"yt_dlp_updated_on_{currentDate}")
if not os.path.isfile(ytdlp_updated):
    installPipPackage("--upgrade yt-dlp")
    open(ytdlp_updated, "a", encoding="utf-8").close()

TOOL_SCHEMA = {
    "name": "extract_youtube_audio",
    "description": "Download Youtube audio into mp3 file and extract a section from it",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Youtube url given by user",
            },
            "start_time": {
                "type": "string",
                "description": "The start time of the extract audio, in the format like '00:00:00'",
            },
            "end_time": {
                "type": "string",
                "description": "The duration of the extract audio, in the format like '00:00:00'",
            },
            "location": {
                "type": "string",
                "description": "Output folder where downloaded file is to be saved",
            },
        },
        "required": ["url"],
    },
}

def extract_youtube_audio(url: str="", start_time: str="", end_time: str="", location: str="", **kwargs):

    from agentmake import getOpenCommand, showErrors, extractText, getCurrentDateTime
    from agentmake.utils.files import find_last_added_file
    from agentmake.utils.online import is_valid_url
    import re, os, shutil

    def is_youtube_url(url_string):
        pattern = r'(?:https?:\/\/)?(?:www\.)?youtu(?:\.be|be\.com)\/(?:watch\?v=|embed\/|v\/)?([a-zA-Z0-9_-]+)'
        match = re.match(pattern, url_string)
        return match is not None

    def terminalDownloadYoutubeFile(downloadCommand, url_string, outputFolder):
        original_file = f"{getCurrentDateTime()}_original_youtube_audio.mp3"
        downloadCommand += f" --output '{original_file}'"
        try:
            print("--------------------")
            # use os.system, as it displays download status ...
            os.system("cd {2}; {0} {1}".format(downloadCommand, url_string, outputFolder))
            if shutil.which("pkill"):
                os.system("pkill yt-dlp")
            command = f"""ffmpeg -i {os.path.join(outputFolder, original_file)} -ss {start_time} -to {end_time}  -c copy {os.path.join(outputFolder, f"{getCurrentDateTime()}_extracted_youtube_audio.mp3")}"""
            os.system("cd {0}; {1}".format(outputFolder, command))
            print(f"Downloaded in: '{outputFolder}'")
            if shutil.which(getOpenCommand()):
                try:
                    os.system(f'''{getOpenCommand()} {outputFolder}''')
                except:
                    pass
        except:
            showErrors()

    if is_youtube_url(url):
        print("Loading youtube downloader ...")
        format = "audio"
        if not (location and os.path.isdir(location)):
            androidMusicDir = "/data/data/com.termux/files/home/storage/shared/Music" # Android
            location = androidMusicDir if os.path.isdir(androidMusicDir) else os.getcwd()
        downloadCommand = "yt-dlp -x --audio-format mp3" if format == "audio" else "yt-dlp -f bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4"
        terminalDownloadYoutubeFile(downloadCommand, url, location)
        if shutil.which("termux-media-scan"): # Android
            os.system(f'termux-media-scan -r "{location}"')
        newFile = find_last_added_file(location, ext=".mp3")
        if newFile:
            message = f"File saved: {newFile}"
            print(message)
        return ""
    elif is_valid_url(url):
        try:
            print(extractText(url))
            return ""
        except Exception as e:
            showErrors(e)
            return None
    else:
        print("Invalid link given!")
        return None

TOOL_FUNCTION = extract_youtube_audio