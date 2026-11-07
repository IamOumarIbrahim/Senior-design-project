#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import uuid

import config
import messages

# states of the alert machine, figure 4.14
IDLE = 0
CANDIDATE = 1
TIER1 = 2
TIER2 = 3
TIER3 = 4
COOLDOWN = 5
SUPPRESSED = 6


class DecisionEngine:

    def __init__(self, cutoffs, cooldown_s):
        self.cutoffs = cutoffs
        self.cooldown_s = cooldown_s
        self.state = {}
        self.t_above = {}       # when the score went above the cutoff
        self.cool_end = {}
        self.recent = {}        # times of the last events for each class
        self.first_id = {}      # event id of the first row of this cue
        self.muted = {}         # already logged this cue inside cooldown
        self.same_cue = {}      # cue started in cooldown and is still going
        for c in config.CLASSES:
            self.state[c] = IDLE
            self.t_above[c] = None
            self.cool_end[c] = 0
            self.recent[c] = []
            self.first_id[c] = None
            self.muted[c] = False
            self.same_cue[c] = False
        self.blocked = False
        self.eyes_on = False
        self.perclos_on = False
        self.perclos_last = -1000000

    # returns a list of events for this frame, it can be empty
    def step(self, ema, t, raw, eye=None):
        out = []
        if self.blocked == False:
            for c in config.CLASSES:
                self.step_class(c, ema[c], raw[c], t, out)
            if eye != None:
                self.step_eyes(eye, t, out)
        return out

    def step_class(self, c, s, x, t, out):
        st = self.state[c]
        above = s >= self.cutoffs[c]

        if st == COOLDOWN:
            if t >= self.cool_end[c]:
                # if a muted cue is still going its the same cue not a new one
                if self.muted[c] and above:
                    self.same_cue[c] = True
                self.state[c] = IDLE
                self.t_above[c] = None
                self.muted[c] = False
                st = IDLE
            else:
                # second cue inside cooldwon, logged but no alert
                if above:
                    if self.t_above[c] == None:
                        self.t_above[c] = t
                    d = t - self.t_above[c]
                    if d >= config.CONFIRM[c] and self.muted[c] == False:
                        self.muted[c] = True
                        self.recent[c].append(t)
                        out.append(self.make_event(c, x, d, 0, 0, t))
                else:
                    self.t_above[c] = None
                    self.muted[c] = False

        if st == IDLE:
            if above:
                self.state[c] = CANDIDATE
                self.t_above[c] = t

        elif st == CANDIDATE:
            if above == False:
                self.state[c] = IDLE
                self.t_above[c] = None
                self.same_cue[c] = False
            else:
                d = t - self.t_above[c]
                if d >= config.CONFIRM[c]:
                    self.confirm(c, x, d, t, out)

        elif st == TIER1 or st == TIER2 or st == TIER3:
            if above == False:
                self.end_cue(c, t, out)
            else:
                d = t - self.t_above[c]
                # cue still there so it gets stronger
                if st == TIER1 and d >= config.TIER2_S:
                    self.state[c] = TIER2
                    out.append(self.make_event(c, x, d, 2, 1, t))
                if st == TIER2 and d >= config.TIER3_S:
                    self.state[c] = TIER3
                    out.append(self.make_event(c, x, d, 3, 1, t))

    def confirm(self, c, x, d, t, out):
        escalated = 0
        if self.same_cue[c]:
            escalated = 1
        else:
            self.recent[c].append(t)
        self.same_cue[c] = False

        n = self.count_recent(c, t)
        tier = 1
        if n >= config.REPEAT_COUNT:
            tier = 2
        event = self.make_event(c, x, d, tier, escalated, t)
        self.first_id[c] = event["event_id"]
        if tier == 2:
            self.state[c] = TIER2
        else:
            self.state[c] = TIER1
        out.append(event)

    # cooldown starts when the cue ends and not at the first alert
    # if it started at the alert the tiers could never happen
    def end_cue(self, c, t, out):
        end = {}
        end["kind"] = "end"
        end["event_id"] = self.first_id[c]
        end["duration_s"] = t - self.t_above[c]
        out.append(end)
        self.state[c] = COOLDOWN
        self.cool_end[c] = t + self.cooldown_s
        self.t_above[c] = None
        self.first_id[c] = None

    def count_recent(self, c, t):
        keep = []
        for old in self.recent[c]:
            if t - old <= config.REPEAT_WINDOW_S:
                keep.append(old)
        self.recent[c] = keep
        return len(keep)

    def step_eyes(self, eye, t, out):
        closed = eye["closed_s"]
        # nodding off is also head down so this only waits longer, it never mutes
        need = config.EYES_CLOSED_S
        if eye.get("head_down", False):
            need = config.EYES_DOWN_S
        if closed >= need:
            # no cooldown here, this one is the dangerous one
            if self.eyes_on == False:
                self.eyes_on = True
                event = self.make_fixed(config.EYES, 1.0, 3, t)
                event["duration_s"] = closed
                event["message"] = messages.EYES_EN
                event["message_ar"] = messages.EYES_AR
                event["voice"] = config.EYES
                out.append(event)
        elif closed == 0:
            self.eyes_on = False

        p = eye["perclos"]
        if p != None:
            if p > config.PERCLOS_LIMIT:
                if self.perclos_on == False and t - self.perclos_last >= self.cooldown_s:
                    self.perclos_on = True
                    self.perclos_last = t
                    event = self.make_fixed(config.PERCLOS, p, 2, t)
                    event["message"] = messages.PERCLOS_EN
                    event["message_ar"] = messages.PERCLOS_AR
                    event["voice"] = config.PERCLOS
                    out.append(event)
            else:
                self.perclos_on = False

    def make_event(self, c, x, d, tier, escalated, t):
        n = self.count_recent(c, t)
        en, ar, voice = messages.make_message(c, tier, n, d)
        event = self.make_fixed(c, x, tier, t)
        event["duration_s"] = d
        event["escalated"] = escalated
        event["message"] = en
        event["message_ar"] = ar
        event["voice"] = voice
        return event

    def make_fixed(self, c, x, tier, t):
        event = {}
        event["kind"] = "alert"
        event["event_id"] = str(uuid.uuid4())
        event["class_name"] = c
        event["confidence"] = x
        event["duration_s"] = 0
        event["tier"] = tier
        event["escalated"] = 0
        event["t"] = t
        return event

    # camera blocked pauses everything
    def set_blocked(self, on, t):
        self.blocked = on
        self.eyes_on = False
        for c in config.CLASSES:
            if on:
                st = self.state[c]
                if st == TIER1 or st == TIER2 or st == TIER3:
                    self.cool_end[c] = t + self.cooldown_s
                self.state[c] = SUPPRESSED
                self.t_above[c] = None
                self.muted[c] = False
                self.same_cue[c] = False
            else:
                if t < self.cool_end[c]:
                    self.state[c] = COOLDOWN
                else:
                    self.state[c] = IDLE

    # what the display should show right now
    def status(self):
        tier = 0
        word = "Attentive"
        if self.eyes_on:
            tier = 3
            word = "Drowsy"
        for c in config.CLASSES:
            st = self.state[c]
            now = 0
            if st == TIER1:
                now = 1
            if st == TIER2:
                now = 2
            if st == TIER3:
                now = 3
            if now > tier:
                tier = now
                if c == "yawning" or c == "hand_over_mouth":
                    word = "Drowsy"
                else:
                    word = "Distracted"
        return word, tier
