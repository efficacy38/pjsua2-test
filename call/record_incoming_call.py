import pjsua2 as pj
from utils import sleep4PJSUA2


class Call(pj.Call):
    """
    Call class, High level Python Call object, derived from pjsua2's Call object.
    there are Call class reference: https://www.pjsip.org/pjsip/docs/html/classpj_1_1Call.htm
    We may wants to implement our Call object to handle the "outgoing" call implement logic
    """

    def __init__(self, acc, peer_uri='', chat=None, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.wav_recorder = None

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
        except Exception as e:
            print("exception!!: {}".format(e.args))

        if not self.wav_recorder:
            self.wav_recorder = pj.AudioMediaRecorder()
            try:
                self.wav_recorder.createRecorder("./recording.wav")
            except Exception as e:
                print("Exception!!: failed opening wav file")
                del self.wav_recorder
                self.wav_recorder = None

        if self.wav_recorder:
            aud_med.startTransmit(self.wav_recorder)


class Account(pj.Account):
    def __init__(self):
        pj.Account.__init__(self)
        self.calls = []

    def onRegState(self, prm):
        ai = self.getInfo()
        print("***{}: code={}".format(("*** Register: code=" if ai.regIsActive else "*** Unregister"), prm.code))

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
    ep = None
    try:
        # init the lib
        ep = pj.Endpoint()
        ep.libCreate()
        ep_cfg = pj.EpConfig()
        ep.libInit(ep_cfg)

        # add some config
        tcfg = pj.TransportConfig()
        tcfg.port = 5060
        ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, tcfg)

        # add account config
        acc_cfg = pj.AccountConfig()
        acc_cfg.idUri = "sip:2@kamailio"
        print("*** start sending SIP REGISTER ***")
        acc_cfg.regConfig.registrarUri = "sip:kamailio"

        # if there needed credential to login, just add following lines
        cred = pj.AuthCredInfo("digest", "*", "2", 0, "test")
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
