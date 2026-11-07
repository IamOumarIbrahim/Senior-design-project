#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import json
import ssl
import time
import urllib.error
import urllib.request

import config


class Uploader:

    def __init__(self, log):
        self.log = log
        self.endpoint = config.UPLOAD_URL

    # only tls 1.3 and the certificate must be good
    def tls(self):
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        if config.CA_FILE != "":
            ctx.load_verify_locations(config.CA_FILE)
        return ctx

    # one post, returns the ids the server accepted or None if it failed
    def post(self, session, events):
        body = {"device_id": config.DEVICE_ID, "session": session, "events": events}
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json", "X-Device-Key": config.DEVICE_KEY}
        req = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")
        try:
            res = urllib.request.urlopen(req, timeout=15, context=self.tls())
            answer = json.loads(res.read().decode())
            return answer["accepted"]
        except urllib.error.URLError as e:
            print("upload failed " + str(e))
        except OSError as e:
            print("upload failed " + str(e))
        return None

    # sends everything that is left, returns how many or None if it failed
    def send_session(self, session):
        sent = 0
        going = True
        while going:
            events = self.log.unsent_events(session["session_id"], config.UPLOAD_BATCH)
            accepted = self.post(session, events)
            if accepted == None:
                return None
            # marked only after the server says ok
            self.log.mark_events(accepted)
            sent = sent + len(accepted)
            if len(events) < config.UPLOAD_BATCH:
                going = False
            elif len(accepted) == 0:
                going = False
        return sent

    # selects unsent sessions and posts them, tries again after 30 60 and 120 s
    # then gives up until the next session
    def sync(self):
        total = 0
        if self.endpoint.startswith("https://") == False:
            print("upload url must be https")
            return 0

        sessions = self.log.unsent_sessions()
        for s in sessions:
            result = self.send_session(s)
            n = 0
            while result == None and n < len(config.RETRY_S):
                print("tryng again in " + str(config.RETRY_S[n]) + " s")
                time.sleep(config.RETRY_S[n])
                result = self.send_session(s)
                n = n + 1
            if result == None:
                return total
            total = total + result
            self.log.mark_session(s["session_id"])
        return total
