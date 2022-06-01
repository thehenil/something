import os
import subprocess
import requests
import time
import base64
import sys
import random
import mimetypes
from pymediainfo import MediaInfo
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


screenshot_count = 5

CATBOX_API_URL = "https://catbox.moe/user/api.php" 
key_imgbb = "417b4af9f57ea2d0d848b2babc4d00d7"
TEMP_FOLDER = "temp"
os.makedirs(TEMP_FOLDER,exist_ok=True)

def takeScreenShot(video_file, output_directory, ttl):
    out_put_file_name = output_directory + \
        "/" + str(time.time()) + ".png"
    file_genertor_command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(ttl),
        "-i",
        f'"{video_file}"',
        "-vframes",
        "1",
        f'"{out_put_file_name}"'
    ]
    cm_str = " ".join(file_genertor_command)
    print(f"Executing command: {cm_str}")
    os.system(cm_str)
    return out_put_file_name

def getVideoDuration(path):
    media_info = MediaInfo.parse(path)
    for track in media_info.tracks:
        if track.track_type == "Video":
            if isinstance(track.duration,int):
                return track.duration/1000
            return int(track.duration.split(".",1)[0])/1000

def getFilename(path):
    if os.name == 'nt':
        return path.rsplit("\\",1)[-1] 
    return path.rsplit("/",1)[-1]

def getMediainfo(path):
    outstr = ""
    p = subprocess.Popen(f"mediainfo {path}",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    while True:
        retcode = p.poll()
        outstr += p.stdout.readline().decode()
        if retcode is not None:
            break
    return outstr

def chunkDuration(duration, times):
    durations = []
    reduced_sec = duration - int(duration*2 / 100)
    for i in range(1, 1+times):
        durations.append(int(reduced_sec/times)*i)
    return durations

def imgbbUpload(path):
    with open(path, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": key_imgbb,
            "image": base64.b64encode(file.read()),
        }
    res = requests.post(url, payload)
    return res.json()['data']['url']

def catboxUpload(path):
    file = open(path,'rb')
    data = {
        'reqtype': 'fileupload',
        'userhash': '',
        'fileToUpload': (file.name, file,mimetypes.guess_type(path))
    }
    encoder = MultipartEncoder(fields=data)
    monitor = MultipartEncoderMonitor(encoder)
    res = requests.post(CATBOX_API_URL,
                            data=monitor,
                            headers={'Content-Type': monitor.content_type})
    return res.text

def main(fname):
    if not os.path.exists(fname):
        print(f"{fname} : no such file found")
        return
    outMsg = ""
    links = []
    dur  = getVideoDuration(fname)
    outMsg += f"[size=4]{getFilename(fname)}[/size]"
    outMsg += "[hr]"
    outMsg += f"[mediainfo]{getMediainfo(fname)}[/mediainfo]"
    outMsg += "[hr]"
    for chunk in chunkDuration(dur,screenshot_count):
        screenshot_path = takeScreenShot(fname,TEMP_FOLDER,chunk)
        link = imgbbUpload(screenshot_path)
        os.remove(screenshot_path)
        links.append(link)
        outMsg += f"[url={link}][img=300x300]{link}[/img][/url]"
    print("-"*50)
    print(outMsg)
    for link in links:
        print(link)

if len(sys.argv) < 2:
    print("specify filepath(s)")
else:
    for filepath in sys.argv[1:]:
        main(filepath)