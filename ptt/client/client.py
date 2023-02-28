import argparse
import pjsua2 as pj
import re
import sys
from enum import Enum
from signal import signal, SIGINT, SIGTERM
import threading
import queue

sys.path.append("../../")
from utils.controlLoop import sleep4PJSUA2, quitPJSUA
from utils.envDefault import EnvDefault

DBG = 1


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


sys.stdout = Unbuffered(sys.stdout)

class Instruction(Enum):
    TB_REQUEST='request'
    TB_GRANT='grant'
    TB_DENY='deny'
    TB_RELEASE='release'
    TB_TAKEN='taken'
    TB_IDLE='idle'

class Call(pj.Call):
    """
    Call class, High level Python Call object, derived from pjsua2's Call object.
    there are Call class reference: https://www.pjsip.org/pjsip/docs/html/classpj_1_1Call.htm
    We may wants to implement our Call object to handle the "outgoing" call implement logic
    """

    def __init__(self, acc, peer_uri='', chat=None, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.wav_player = None
        self.wav_recorder = None
        self.curStatus = None

    # override the function at original parent class
    # parent class's function can be called by super().onCallState()
    def onCallState(self, prm):
        ci = self.getInfo()
        print("*** Call: {} [{}]".format(ci.remoteUri, ci.lastStatusCode))
        if ci.lastStatusCode == 404:
            print("call can't established with code 404!")
            # quitPJSUA()

    def onCallMediaState(self, prm):
        aud_med = None
        try:
            # get the "local" media
            aud_med = self.getAudioMedia(-1)
        except pj.Error as e:
            print("exception!!: {}".format(e.args))
            handleErr(e)

        if not self.wav_player:
            self.wav_player = pj.AudioMediaPlayer()
            try:
                self.wav_player.createPlayer("./input.16.wav")
            except pj.Error as e:
                print("Exception!!: failed opening wav file")
                del self.wav_player
                self.wav_player = None
                handleErr(e)
            else:
                self.wav_player.startTransmit(aud_med)

        if args.record:
            if not self.wav_recorder:
                self.wav_recorder = pj.AudioMediaRecorder()
                try:
                    self.wav_recorder.createRecorder("./recordered.wav")
                except pj.Error as e:
                    print("Exception!!: failed opening recordered wav file")
                    del self.wav_recorder
                    self.wav_recorder = None
                    handleErr(e)
                else:
                    aud_med.startTransmit(self.wav_recorder)

def handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGTERM, SIGINT or CTRL-C detected. Exiting gracefully')
    # quitPJSUA()

    exit(0)

def main():
    global args

    signal(SIGTERM, handler)
    signal(SIGINT, handler)

    # parse the cmd element
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--username", action=EnvDefault, envvar='USERNAME',
        help="Specify the username, example: `-u 1000` (can also be specified using USERNAME environment variable)")
    parser.add_argument(
        "-p", "--password", action=EnvDefault, envvar='PASSWORD',
        help="Specify the password (can also be specified using PASSWORD environment variable)")
    parser.add_argument(
        "-R", "--registrarURI", action=EnvDefault, envvar='REGISTER_URI',
        help="Specify the registrarURI, example: `-R sip:kamailio` (can also be specified using REGISTER_URI environment variable)")
    parser.add_argument(
        "-c", "--callURI", action=EnvDefault, envvar='CALL_URI',
        help="Specify the URI you wants to call, example: `-c sip:1@kamailio` (can also be specified using CALL_URI environment variable)")
    parser.add_argument(
        "-x", "--record", action=EnvDefault, envvar='RECORD', type=bool, default=False, required=False,
        help="Specify the whether it would record the audio to /recordered.wav, default False (can also be specified using RECORD environment variable)")

    args = parser.parse_args()

    ep = None
    try:
        # init the lib
        ep = pj.Endpoint()
        ep.libCreate()
        ep_cfg = pj.EpConfig()
        if not DBG:
            ep_cfg.logConfig.level = 1
            ep_cfg.logConfig.consoleLevel = 1
        # using thread in python may cause some problem
        ep_cfg.uaConfig.threadCnt = 0
        ep_cfg.uaConfig.mainThreadOnly = True
        ep.libInit(ep_cfg)

        # add some config
        tcfg = pj.TransportConfig()
        # tcfg.port = 5060
        ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, tcfg)

        # add account config
        acc_cfg = pj.AccountConfig()
        acc_cfg.idUri = "sip:{}@{}".format(args.username,
                                           re.findall("sip:(.*)", args.registrarURI)[0])
        print("*** start sending SIP REGISTER ***")
        acc_cfg.regConfig.registrarUri = args.registrarURI

        # if there needed credential to login, just add following lines
        cred = pj.AuthCredInfo("digest", "*", args.username, 0, args.password)
        acc_cfg.sipConfig.authCreds.append(cred)

        acc = pj.Account()
        acc.create(acc_cfg)

        ep.libStart()
        print("*** PJSUA2 STARTED ***")

        # use null device as conference bridge, instead of local sound card
        pj.Endpoint.instance().audDevManager().setNullDev()

        # add an buddy using dst uri
        buddy = pj.Buddy()
        buddyCfg = pj.BuddyConfig()
        buddyCfg.uri = args.callURI
        buddy.create(acc, buddyCfg)

        # call to the dst uri
        call = Call(acc)
        prm = pj.CallOpParam(True)
        prm.opt.audioCount = 1
        prm.opt.videoCount = 0
        call.makeCall(args.callURI, prm)

        inputQueue = queue.Queue()
        def scanKeyboardPress():
            while True:
                s = input()
                inputQueue.put(s)
                print("****** push s")

        inputThread = threading.Thread(target=scanKeyboardPress)
        # set it as daemon
        inputThread.setDaemon(True)
        inputThread.start()

        
        def control_loop():
            # isQuit = not call.isActive()
            isQuit = False;
            while not inputQueue.empty() and not isQuit:
                # r stand for ptt request
                instSet = set(["request", "release", "print"])
                inst = inputQueue.get()
                print("****** pop {}".format(inst))
                if inst in instSet:
                    if inst == "print":
                        print()
                    elif inst == "request":
                        instantMessagePrm = pj.SendInstantMessageParam()
                        instantMessagePrm.content = Instruction.TB_REQUEST.value
                        instantMessagePrm.contentType = "text/plain"
                        buddy.sendInstantMessage(instantMessagePrm)
                    elif inst == "release":
                        instantMessagePrm = pj.SendInstantMessageParam()
                        instantMessagePrm.content = Instruction.TB_RELEASE.value
                        instantMessagePrm.contentType = "text/plain"
                        buddy.sendInstantMessage(instantMessagePrm)
            return isQuit


        # hangup all call after the time we specified at args(sec)
        sleep4PJSUA2(-1, control_loop, 0.5)


    except KeyboardInterrupt as e:
        print("catch KeyboardInterrupt!!, exception error is: {}".format(e.args))
    finally:
        ep.hangupAllCalls()

        del call

        print("*** PJSUA2 SHUTTING DOWN ***")
        del acc
        # close the library
        ep.libDestroy()


if __name__ == '__main__':
    main()
