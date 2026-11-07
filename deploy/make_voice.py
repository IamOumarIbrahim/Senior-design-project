#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# makes all the voice messages once on a laptop, the pi only plays the wav files
# needs internet, edge-tts and ffmpeg. only the fixed sentences are sent, nothing about a driver
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "edge"))

import messages

VOICE_EN = "en-GB-SoniaNeural"
VOICE_AR = "ar-AE-FatimaNeural"


def make_clip(text, voice, out_wav):
    mp3 = out_wav + ".mp3"
    subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--text", text,
                    "--write-media", mp3], check=True, stdout=subprocess.DEVNULL)
    # 24 khz mono is enough for voice and keeps the files small
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", "24000", "-ac", "1", out_wav], check=True)
    os.remove(mp3)


folder_en = os.path.join(REPO, "voice", "en")
folder_ar = os.path.join(REPO, "voice", "ar")
for f in [folder_en, folder_ar]:
    if os.path.exists(f) == False:
        os.makedirs(f)

clips = messages.all_clips()
count = 0
for key in clips:
    path_en = os.path.join(folder_en, key + ".wav")
    path_ar = os.path.join(folder_ar, key + ".wav")
    if os.path.exists(path_en) == False:
        make_clip(clips[key][0], VOICE_EN, path_en)
    if os.path.exists(path_ar) == False:
        make_clip(clips[key][1], VOICE_AR, path_ar)
    count = count + 1
    print(str(count) + " of " + str(len(clips)))
