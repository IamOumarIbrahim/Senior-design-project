#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# every alert text in english and arabic
# the voice key is the name of the wav file inside voice/en and voice/ar

NAME_EN = {
    "yawning": "Yawning",
    "hand_over_mouth": "Hand over mouth",
    "drinking": "Drinking",
    "phone_use": "Phone use",
}
NAME_AR = {
    "yawning": "التثاؤب",
    "hand_over_mouth": "تغطية الفم باليد",
    "drinking": "الشرب",
    "phone_use": "استخدام الهاتف",
}
ADVICE_EN = {
    "yawning": "Consider a short break.",
    "hand_over_mouth": "You seem tired. Consider a short break.",
    "drinking": "Keep your eyes on the road.",
    "phone_use": "Please put the phone down.",
}
ADVICE_AR = {
    "yawning": "يرجى أخذ استراحة قصيرة.",
    "hand_over_mouth": "تبدو متعبا. يرجى أخذ استراحة قصيرة.",
    "drinking": "انتبه إلى الطريق.",
    "phone_use": "يرجى ترك الهاتف.",
}

# number of times in arabic, 3 to 10
TIMES_AR = {
    3: "ثلاث مرات",
    4: "أربع مرات",
    5: "خمس مرات",
    6: "ست مرات",
    7: "سبع مرات",
    8: "ثماني مرات",
    9: "تسع مرات",
    10: "عشر مرات",
}

MAX_COUNT = 10   # we only made voice files up to 10


# tier 2 voice when the cue was seen many times
def count_text(c, n):
    en = NAME_EN[c] + " detected " + str(n) + " times in 5 minutes. " + ADVICE_EN[c]
    ar = "تم رصد " + NAME_AR[c] + " " + TIMES_AR[n] + " خلال خمس دقائق. " + ADVICE_AR[c]
    return en, ar


# tier 2 voice when the cue lasted 5 seconds
def hold_text(c):
    en = NAME_EN[c] + " detected for 5 seconds. " + ADVICE_EN[c]
    ar = "تم رصد " + NAME_AR[c] + " لمدة خمس ثوان. " + ADVICE_AR[c]
    return en, ar


def make_message(c, tier, count, d):
    voice = ""
    if tier == 2:
        if count >= 3:
            if count > MAX_COUNT:
                count = MAX_COUNT
            en, ar = count_text(c, count)
            voice = c + "_n" + str(count)
        else:
            en, ar = hold_text(c)
            voice = c + "_d5"
    else:
        # tier 0 1 and 3 are not spoken, its only for the log and display
        secs = str(round(d, 1))
        en = NAME_EN[c] + " detected for " + secs + " seconds."
        ar = "تم رصد " + NAME_AR[c] + " لمدة " + secs + " ثانية."
        if tier == 3:
            en = en + " " + ADVICE_EN[c]
            ar = ar + " " + ADVICE_AR[c]
    return en, ar, voice


EYES_EN = "Eyes closed for 1.5 seconds. Pull over safely."
EYES_AR = "عيناك مغلقتان منذ ثانية ونصف. توقف في مكان آمن."
PERCLOS_EN = "You look tired, consider a break."
PERCLOS_AR = "تبدو متعبا، فكر في أخذ استراحة."
BLOCKED_EN = "Camera blocked."
BLOCKED_AR = "الكاميرا محجوبة."
FAULT_EN = "Device fault."
FAULT_AR = "يوجد عطل في الجهاز."


# all fixed clips, used by deploy/make_voice.py
def all_clips():
    clips = {
        "eyes_closed": [EYES_EN, EYES_AR],
        "perclos": [PERCLOS_EN, PERCLOS_AR],
        "camera_blocked": [BLOCKED_EN, BLOCKED_AR],
        "device_fault": [FAULT_EN, FAULT_AR],
    }
    for c in NAME_EN:
        en, ar = hold_text(c)
        clips[c + "_d5"] = [en, ar]
        for n in range(3, MAX_COUNT + 1):
            en, ar = count_text(c, n)
            clips[c + "_n" + str(n)] = [en, ar]
    return clips
