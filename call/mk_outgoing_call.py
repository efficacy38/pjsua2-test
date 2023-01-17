import pjsua2 as pj
import time
import os
import gc



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

    # override the function at original parent class
    # parent class's function can be called by super().onCallState()
    def onCallState(self, prm):
        ci = self.getInfo()
        print("*** Call: {} [{}]".format(ci.remoteUri, ci.statusCode))

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

        if not self.wav_player:
            self.wav_player = pj.AudioMediaPlayer()
            try:
                self.wav_player.createPlayer("./input.16.wav")
            except Exception as e:
                print("Exception!!: failed opening wav file")
                del self.wav_player
                self.wav_player = None

        if self.wav_player:
           self.wav_player.startTransmit(aud_med)


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

        acc = pj.Account()
        acc.create(acc_cfg)

        ep.libStart()
        print("*** PJSUA2 STARTED ***")

        # hangup all call after 10 sec
        while True:
            ep.libHandleEvents(10000)

        # time.sleep(10)
        ep.hangupAllCalls()
        ep.libHandleEvents(4000)

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
