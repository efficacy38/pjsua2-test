import pjsua2 as pj
from utils import sleep4PJSUA2
from parseLog import PjsuaLogParser
import argparse
from envDefault import EnvDefault
import humanfriendly
import re
from datetime import datetime


class Call(pj.Call):
    """
    Call class, High level Python Call object, derived from pjsua2's Call object.
    there are Call class reference: https://www.pjsip.org/pjsip/docs/html/classpj_1_1Call.htm
    We may wants to implement our Call object to handle the "outgoing" call implement logic
    """

    def __init__(self, acc, peer_uri='', chat=None, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc

    # override the function at original parent class
    # parent class's function can be called by super().onCallState()
    def onCallState(self, prm):
        ci = self.getInfo()
        print("*** Call: {} [{}, {}]".format(ci.remoteUri,
              ci.lastStatusCode, ci.stateText))

        # python do not do the gc of underlaying C++ library, we need to do it by ourself
        if ci.stateText == "DISCONNCTD":
            self.acc.removeCall(self)
            del self

    def onCallMediaState(self, prm):
        # Deprecated: for PJSIP version 2.8 or earlier
        # ci = self.getInfo()
        # for mi in ci.media:
        #     if mi.type == pj.PJMEDIA_TYPE_AUDIO and \
        #         (mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE or
        #          mi.status == pj.PJSUA_CALL_MEDIA_REMOTE_HOLD):
        #         m = self.getMedia(mi.index)
        #         am = pj.AudioMedia.typecastFromMedia(m)
        #         # connect ports
        #         ep.Endpoint.instance.audDevManager().getCaptureDevMedia().startTransmit(am)
        #         am.startTransmit(
        #             ep.Endpoint.instance.audDevManager().getPlaybackDevMedia())
        aud_med = None
        try:
            # get the "local" media
            aud_med = self.getAudioMedia(-1)
            # generate echo
            aud_med.startTransmit(aud_med)
        except Exception as e:
            print("exception!!: {}".format(e.args))

    def onStreamDestroyed(self, prm):
        call_id = self.getInfo().callIdString
        parser = PjsuaLogParser(call_id)
        parser.parseIndent(self.dump(True, "    "))
        stats = parser.toJSON()

        # flag the abnormal data
        is_abnormal = False
        min_pktsz = ""
        max_pktsz = ""
        log_str = ""

        if len(list(enumerate(stats["media"]))) != 0:
            try:
                min_pktsz = min(humanfriendly.parse_size(stats["media"]["0"]["rx"]["total_packet_cnt"]), humanfriendly.parse_size(
                    stats["media"]["0"]["tx"]["total_packet_cnt"]))
                max_pktsz = max(humanfriendly.parse_size(stats["media"]["0"]["rx"]["total_packet_cnt"]), humanfriendly.parse_size(
                    stats["media"]["0"]["tx"]["total_packet_cnt"]))
            except Exception as e:
                print("err: {}, stats: {}".format(e.args, stats))

            if min_pktsz == 0:
                is_abnormal = True
            elif int(min_pktsz) / int(max_pktsz) < args.threshold:
                is_abnormal = True
        else:
            log_str = "{} Error(no media) callid:{}\n".format(
                datetime.now(), stats["call_id"])

        with open('server.log', "a") as f:
            if len(log_str) == 0:
                if is_abnormal:
                    log_str = "{} Error callid:{} tx_pktsz:{} rx_pktsz:{} dbg_msg={}\n".format(
                        datetime.now(), stats["call_id"], stats["media"]["0"]["tx"]["total_packet_size"], stats["media"]["0"]["rx"]["total_packet_size"], stats)
                else:
                    log_str = "{} Normal callid:{} tx_pktsz:{} rx_pktsz:{}\n".format(
                        datetime.now(), stats["call_id"], stats["media"]["0"]["tx"]["total_packet_size"], stats["media"]["0"]["rx"]["total_packet_size"])
            print(log_str)
            f.write(log_str)


class Account(pj.Account):
    def __init__(self):
        pj.Account.__init__(self)
        self.calls = []

    def onRegState(self, prm):
        ai = self.getInfo()
        print("***{}: code={}".format(("*** Register" if ai.regIsActive else "*** Unregister"), prm.code))

    def onIncomingCall(self, iprm):
        call = Call(self, call_id=iprm.callId)
        call_prm = pj.CallOpParam()
        ci = call.getInfo()

        print("*** Incoming Call: {} [{}]".format(ci.remoteUri, ci.stateText))
        self.calls.append(call)
        call_prm.statusCode = 200
        call.answer(call_prm)

    def removeCall(self, call):
        for tmpCall in self.calls:
            if tmpCall.getInfo().callIdString == call.getInfo().callIdString:
                self.calls.remove(tmpCall)
                break


def enumLocalMedia(ep):
    # important: the Endpoint::mediaEnumPorts2() and Call::getAudioMedia() only create a copy of device object
    # all memory should manage by developer
    print("enum the local media, and length is ".format(len(ep.mediaEnumPorts2())))
    for med in ep.mediaEnumPorts2():
        # media info ref: https://www.pjsip.org/pjsip/docs/html/structpj_1_1MediaFormatAudio.htm
        med_info = med.getPortInfo()
        print("id: {}, name: {}, format(channelCount): {}".format(
            med_info.portId, med_info.name, med_info.format.channelCount))


def main():
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
        "-D", "--debug", action=EnvDefault, envvar='DBG', type=float, default=False, required=False,
        help="Specify whether the debug mode is open, default False (can also be specified using DBG environment variable)")

    args = parser.parse_args()

    ep = None
    try:
        # init the lib
        ep = pj.Endpoint()
        ep.libCreate()
        ep_cfg = pj.EpConfig()
        if args.debug:
            ep_cfg.logConfig.level = 10
            ep_cfg.logConfig.consoleLevel = 10
        else:
            ep_cfg.logConfig.level = 1
            ep_cfg.logConfig.consoleLevel = 1
        # do some logging
        ep_cfg.logConfig.filename = "pjsua2.log"
        # disable the VAD
        ep_cfg.medConfig.noVad = True

        # set the maximum call
        ep_cfg.uaConfig.maxCalls = 32

        # disable the echo cancelation
        # ep_cfg.medConfig.setEcOptions(pj.PJMEDIA_ECHO_USE_SW_ECHO)

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

        # hangup all call after 10 sec
        sleep4PJSUA2(-1)

        print("*** PJSUA2 SHUTTING DOWN ***")
        del acc

    except Exception as e:
        print("catch exception!!, exception error is: {}".format(e.args))

    # close the library
    try:
        ep.libDestroy()
    except Exception as e:
        print("catch exception!!, exception error is: {}".format(e.args))


if __name__ == '__main__':
    main()
