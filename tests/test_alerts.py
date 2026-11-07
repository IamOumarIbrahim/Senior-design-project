#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# FS-05 FS-14 FS-15 FS-16 and the flash limit from T-05
# fake led and fake audio here so this checks the timing and the logic only
import os
import time
import wave

from helper import check, done

import config
import messages
from alert_manager import AlertManager, LightBar
from decision_engine import DecisionEngine


def most_in_one_second(times):
    best = 0
    for i in range(len(times)):
        n = 0
        for j in range(i, len(times)):
            if times[j] - times[i] < 1.0:
                n = n + 1
        if n > best:
            best = n
    return best


# asking for 10 hz must still give at most 3
bar = LightBar()
bar.flash(10, 3)
time.sleep(3.2)
n = most_in_one_second(bar.toggles)
print("flashes in the worst second= " + str(n))
check("T-05 asking for 10 hz gives at most 3 each second", n <= 3)
check("light really flashed", len(bar.toggles) >= 7)

# changing pattern quickly must not beat the limit
bar = LightBar()
for i in range(20):
    bar.flash(3, 0.15)
    time.sleep(0.1)
n = most_in_one_second(bar.toggles)
check("fast pattern changes stay at most 3 each second", n <= 3)

# All sounds exist and have the right length
lengths = {config.CHIME: 1.5, config.BUZZ: 3.0, config.ALARM: 10.0}
for path in lengths:
    w = wave.open(path)
    secs = w.getnframes() / w.getframerate()
    w.close()
    check(os.path.basename(path) + " is " + str(lengths[path]) + " s", abs(secs - lengths[path]) < 0.05)

# All voice files exist in both languages
missing = 0
clips = messages.all_clips()
for key in clips:
    for lang in ["en", "ar"]:
        path = os.path.join(config.VOICE_DIR, lang, key + ".wav")
        if os.path.exists(path) == False:
            missing = missing + 1
check("voice file for all " + str(len(clips)) + " messages in en and ar", missing == 0)


def make(c, tier, voice):
    return {"class_name": c, "tier": tier, "voice": voice}


# Tier 0 is silent
a = AlertManager("en", True)
a.play(make("drinking", 0, ""))
a.wait()
check("muted cue plays nothing", len(a.played) == 0 and len(a.bar.toggles) == 0)

# Tier 1 is the class chime
a.play(make("drinking", 1, ""))
a.wait()
check("tier 1 is the class sound", a.played == [config.CHIME])

a.played = []
a.play(make("yawning", 1, ""))
a.wait()
check("yawning uses the buzz", a.played == [config.BUZZ])

# Tier 2 adds the voice
a.played = []
a.play(make("phone_use", 2, "phone_use_d5"))
a.wait()
check("tier 2 is chime and voice", len(a.played) == 2 and a.played[1].endswith("phone_use_d5.wav"))

# Arabic driver
b = AlertManager("ar", True)
b.play(make("yawning", 2, "yawning_n3"))
b.wait()
check("arabic driver hears the arabic file", os.path.join("ar", "yawning_n3.wav") in b.played[1])

# Tier 3 is the alarm
a.played = []
a.play(make("yawning", 3, ""))
a.wait()
check("tier 3 is the alarm", a.played == [config.ALARM])

# every voice key the engine can give must be a real file
eng = DecisionEngine(config.CUTOFF, config.COOLDOWN_S)
ok = True
for c in config.CLASSES:
    for n in range(0, 15):
        en, ar, voice = messages.make_message(c, 2, n, 5)
        if voice not in clips:
            ok = False
check("all tier 2 voice keys have a file", ok)

done()
