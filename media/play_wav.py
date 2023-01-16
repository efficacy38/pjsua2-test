import pjsua2 as pj
import sys
import time
import gc

ep = None

# Subclass to extend the Account and get notifications etc.


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


class Account(pj.Account):
    def onRegState(self, prm):
        print("***OnRegState: " + prm.reason)


class myCall(pj.Call):
    def onCallMediaState(self, prm):
        print("enter onCallMediaState")
        ci = self.getInfo()

        print("1")
        aud_med = self.getAudioMedia(-1)
        print("2")
        cap_dev_med = ep.audDevManager().getCaptureDevMedia()
        print("3")
        cap_dev_med.startTransmit(aud_med)
        print("4")
        aud_med.startTransmit(play_dev_med)

# pjsua2 test function


def pjsua2_test():
    global ep
    print("START")
    # Create and initialize the library
    ep_cfg = pj.EpConfig()
    ep = pj.Endpoint()
    ep.libCreate()
    ep.libInit(ep_cfg)

    # Create SIP transport. Error handling sample is shown
    sipTpConfig = pj.TransportConfig()
    sipTpConfig.port = 5060
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)
    # Start the library
    ep.libStart()

    # create a account
    acfg = pj.AccountConfig()
    acfg.idUri = "sip:2@kamailio"
    acfg.regConfig.registrarUri = "sip:kamailio"
    cred = pj.AuthCredInfo("digest", "*", "2", 0, "test")
    acfg.sipConfig.authCreds.append(cred)
    # Create the account
    acc = Account()
    acc.create(acfg)

    # playing the wav file
    # create the AudioMediaPlayer
    # player = pj.AudioMediaPlayer()
    # play_dev_med = ep.audDevManager().getPlaybackDevMedia()
    # player.createPlayer("test.wav", pj.PJMEDIA_FILE_NO_LOOP)
    # player.startTransmit(play_dev_med)

    # call to the outside user
    # because the pjsua2's Call object is not compatiable with python's gc,
    # just disable it when we generate the outbound call
    gc.disable()
    # make call dev nullable
    # call for 1020
    # call = pj.Call(acc)
    call = myCall(acc)
    call_prm = pj.CallOpParam(True)
    # ep.audDevManager().setNullDev()
    try:
        call.makeCall("sip:1@kamailio", call_prm)
        while not call.done:
            ep.libHandleEvents(10)
            # check your saved call_state here
            if not call.call_state:
                continue
            if call.call_state == pj.PJSIP_INV_STATE_CONFIRMED:
                call.done = True
    except Exception:
        print("can't establish call")

    ep.libHandleEvents(10000)
    time.sleep(10)
    print("cleanup")
    del call

    # remove the Call object
    gc.enable()
    # Destroy the library
    ep.libDestroy()

# def pjsua2_test():
#     # freeze the gc
#     gc.disable()
#     # Create and initialize the library
#     ep_cfg = pj.EpConfig()
#     ep = pj.Endpoint()
#     ep.libCreate()
#     ep.libInit(ep_cfg)
#
#     # Create SIP transport. Error handling sample is shown
#     sipTpConfig = pj.TransportConfig()
#     sipTpConfig.port = 5060
#     ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)
#     # Start the library
#     ep.libStart()
#
#     acfg = pj.AccountConfig()
#     acfg.idUri = "sip:1020@163.22.22.67"
#     acfg.regConfig.registrarUri = "sip:163.22.22.67"
#     cred = pj.AuthCredInfo("digest", "*", "1020", 0, "aloha802.3")
#     acfg.sipConfig.authCreds.append(cred)
#     # Create the account
#     acc = Account()
#     acc.create(acfg)
#     # Here we don't have anything else to do..
#     time.sleep(10)
#
#     # make call dev nullable
#     # call for 1020
#     call = pj.Call(acc)
#     call_prm = pj.CallOpParam()
#     ep.audDevManager().setNullDev()
#     try:
#         call.makeCall("sip:1020@163.22.22.67", call_prm)
#     except Exception:
#         print("can't establish call")
#
#     print("cleanup")
#     del call
#
#     # Destroy the library
#     ep.libDestroy()
#     gc.enable()
#
# def pjsua2_test():
#     # Create and initialize the library
#     ep_cfg = pj.EpConfig()
#     ep = pj.Endpoint()
#     ep.libCreate()
#     ep.libInit(ep_cfg)
#
#     # Create SIP transport. Error handling sample is shown
#     sipTpConfig = pj.TransportConfig()
#     sipTpConfig.port = 5060
#     ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)
#     # Start the library
#     ep.libStart()
#
#     acfg = pj.AccountConfig()
#     acfg.idUri = "sip:1007@163.22.22.67"
#     acfg.regConfig.registrarUri = "sip:163.22.22.67"
#     cred = pj.AuthCredInfo("digest", "*", "1007", 0, "aloha802.3")
#     acfg.sipConfig.authCreds.append(cred)
#     # Create the account
#     acc = Account()
#     acc.create(acfg)
#
#     # make call dev nullable
#     # ep.audDevManager().setNullDev()
#
#     time.sleep(10)
#     # call for 1020
#     call = pj.Call(acc)
#     call_prm = pj.CallOpParam()
#     try:
#         call.makeCall("1020@163.22.22.67", call_prm)
#     except Exception:
#         print("can't establish call")
#     time.sleep(10)
#
#     # Destroy the library
#     ep.libDestroy()
#


#
# main()
#
if __name__ == "__main__":
    sys.stdout = Unbuffered(sys.stdout)
    pjsua2_test()
