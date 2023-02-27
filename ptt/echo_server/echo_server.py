import pjsua2 as pj
import argparse
from envDefault import EnvDefault
import re
import traceback
import sys
from typing import Union
import threading
import queue
from enum import Enum
import sys
from signal import signal, SIGINT, SIGTERM

sys.path.append("../../")
from utils import sleep4PJSUA2, quitPJSUA

# pjsua2 endpoint instance
ep: Union[None, pj.Endpoint] = None

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
    there are Call class reference: https://www.pjsip.org/pjsip/docs/html/classpj_1_1Call.htm We may wants to implement our Call object to handle the "outgoing" call implement logic
    """

    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc

    # override the function at original parent class
    # parent class's function can be called by super().onCallState()
    def onCallState(self, prm):
        ci = self.getInfo()
        print("*** Call: {} [{}, {}]".format(ci.remoteUri,
              ci.lastStatusCode, ci.stateText))

        if ci.stateText == "CONNECTING":
            call_send_request_prm = pj.CallSendRequestParam()
            call_send_request_prm.method = "INFO"
            txo = pj.SipTxOption()
            txo.contentType = "text/plain"
            txo.msgBody = "test info"
            call_send_request_prm.txOption = txo
            self.sendRequest(call_send_request_prm)

        # python do not do the gc of underlaying C++ library, we need to do it by ourself
        elif ci.stateText == "DISCONNECTED":
            self.acc.removeCall(self)
            del self

    def onCallMediaState(self, prm):
        if not self.acc.curLeader:
            return

        try:
            # get the "local" media
            aud_med = self.getAudioMedia(-1)
            # generate echo
            self.acc.curLeader.getAudioMedia(-1).startTransmit(aud_med)
        except Exception as e:
            print("exception!!: {}".format(e.args))

    def onStreamDestroyed(self, prm):
        # print some summary
        print(self.dump(with_media=True, indent="  "))

class Account(pj.Account):
    def __init__(self):
        pj.Account.__init__(self)
        self.calls = []
        self.buddys = []
        self.curLeader = None

    def findCall(self, uri=""):
        for call in self.calls:
            ci = call.getInfo()
            if uri in ci.remoteUri:
                print(ci.remoteUri)
                return call
        return None

    def setLeader(self, uri=""):
        self.curLeader = self.findCall(uri)
        if not self.curLeader:
            print("can't set the ua as a leader")
            return

        srcMed = self.curLeader.getAudioMedia(-1)
        for call in self.calls:
            ci = call.getInfo()
            if uri not in ci.remoteUri:
                srcMed.startTransmit(call.getAudioMedia(-1))

    def delLeader(self):
        if not self.curLeader:
            print("can't delete the ua")
            return

        print(self.curLeader)
        curMed = self.curLeader.getAudioMedia(-1)
        for call in self.calls:
            try:
                if call.isActive():
                    med = call.getAudioMedia(-1)
                    curMed.stopTransmit(med)
            except Exception as e:
                print("exception!!: {}".format(e.args))
        self.curLeader = None

    def onRegState(self, prm):
        ai = self.getInfo()
        print("***{}: code={}".format(("*** Register" if ai.regIsActive else "*** Unregister"), prm.code))

    def onIncomingCall(self, iprm):
        call = Call(self, call_id=iprm.callId)
        call_prm = pj.CallOpParam()
        ci = call.getInfo()

        print("*** incoming call: {} [{}]".format(ci.remoteUri, ci.stateText))
        self.calls.append(call)
        call_prm.statusCode = 200
        call.answer(call_prm)

        print("*** create a buddy")
        curBuddy = None
        # find remote buddy
        for buddy in self.buddys:
            if(buddy.getInfo().uri == ci.remoteUri):
                curBuddy = self.findBuddy2(ci.remoteUri)
                print("found buddy")
        if not curBuddy:
            buddyCfg = pj.BuddyConfig()
            buddyCfg.uri = ci.remoteUri
            curBuddy = pj.Buddy()
            curBuddy.create(self, buddyCfg)
            self.buddys.append(curBuddy)
            print("not found buddy")

    def removeCall(self, call):
        for tmpCall in self.calls:
            if tmpCall.getInfo().callIdString == call.getInfo().callIdString:
                if self.curLeader and self.curLeader.getInfo().callIdString == call.getInfo().callIdString:
                    print("del")
                    self.curLeader = None

                self.calls.remove(tmpCall)
                break

    def onInstantMessage(self, prm):
        if prm.contentType == 'text/plain':
            if prm.msgBody == Instruction.TB_REQUEST.value:
                instantMessagePrm = pj.SendInstantMessageParam()
                instantMessagePrm.contentType = "text/plain"
                if self.curLeader:
                    print("send instant message")
                    instantMessagePrm.content = Instruction.TB_DENY.value
                else:
                    instantMessagePrm.content = Instruction.TB_GRANT.value
                    self.setLeader(prm.fromUri)
                self.findBuddy2(prm.fromUri).sendInstantMessage(instantMessagePrm)

            elif prm.msgBody == Instruction.TB_RELEASE.value:
                    if self.curLeader:
                        if prm.fromUri in self.curLeader.getInfo().remoteUri:
                            self.delLeader()

            print("end send instant message")


def enumLocalMedia():
    # important: the Endpoint::mediaEnumPorts2() and Call::getAudioMedia() only create a copy of device object
    # all memory should manage by developer
    print("enum the local media, and length is ".format(
        len(pj.Endpoint.instance().mediaEnumPorts2())))
    for med in pj.Endpoint.instance().mediaEnumPorts2():
        # media info ref: https://www.pjsip.org/pjsip/docs/html/structpj_1_1MediaFormatAudio.htm
        med_info = med.getPortInfo()
        print("id: {}, name: {}, format(channelCount): {}".format(
            med_info.portId, med_info.name, med_info.format.channelCount))

def handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGTERM, SIGINT or CTRL-C detected. Exiting gracefully')
    # quitPJSUA()

    exit(0)

def main():
    signal(SIGTERM, handler)
    signal(SIGINT, handler)
    # parse the cmd element
    global args
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
        "-s", "--threshold", action=EnvDefault, envvar='THRESHOLD', type=float, default=0.9, required=False,
        help="Specify the abnormal percent it would assert, default 0.9 (can also be specified using THRESHOLD environment variable)")
    parser.add_argument(
        "-D", "--debug", action=EnvDefault, envvar='DBG', type=bool, default=False, required=False,
        help="Specify whether the debug mode is open, default False (can also be specified using DBG environment variable)")

    args = parser.parse_args()

    global ep, f

    try:
        f = open('server.log', "a", buffering=1)
    except Exception as e:
        print("can't open the log file")

    try:
        # init the lib
        ep = pj.Endpoint()
        ep.libCreate()
        ep_cfg = pj.EpConfig()

        # using thread in python may cause some problem
        ep_cfg.uaConfig.threadCnt = 0
        ep_cfg.uaConfig.mainThreadOnly = True
        if args.debug:
            ep_cfg.logConfig.level = 10
            ep_cfg.logConfig.consoleLevel = 10
        else:
            ep_cfg.logConfig.level = 1
            ep_cfg.logConfig.consoleLevel = 1

        ep.libInit(ep_cfg)

        # add some config
        tcfg = pj.TransportConfig()
        tcfg.port = 5060
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

        acc = Account()
        acc.create(acc_cfg)

        ep.libStart()
        print("*** PJSUA2 STARTED ***")

        # use null device as conference bridge, instead of local sound card
        pj.Endpoint.instance().audDevManager().setNullDev()

        # enumerate current supported codec
        print("*** supported codec(priority 0 means disable) ***")
        for codec in ep.codecEnum2():
            print("codec_id: {} codec_priority: {}".format(
                codec.codecId, codec.priority))

        inputQueue = queue.Queue()
        def scanKeyboardPress():
            while True:
                s = input()
                inputQueue.put(s)
        # monitor the input
        inputThread = threading.Thread(target=scanKeyboardPress)
        # set it as daemon
        inputThread.setDaemon(True)
        inputThread.start()

        def control_loop():
            while not inputQueue.empty():
                # r stand for ptt request
                instSet = set(["s", "p", "d"])
                inst = inputQueue.get()
                inst = inst.split(' ')
                opcode, operand = inst[0], inst[1:]

                if opcode in instSet:
                    if opcode == "p":
                        enumLocalMedia()
                        print(acc.curLeader)
                    elif opcode == "s":
                        acc.setLeader(operand[0])
                    elif opcode == "d":
                        acc.delLeader()

        sleep4PJSUA2(-1, control_loop, 0.5)

        # hangup all call after the time we specified at args(sec)
        ep.hangupAllCalls()

        print("*** PJSUA2 SHUTTING DOWN ***")
        del acc

    except Exception as e:
        print("catch exception!!, exception error is: {}".format(e.args))
        traceback.print_exception(*sys.exc_info())
    finally:
        # close the library
        ep.libDestroy()
        


if __name__ == '__main__':
    main()
