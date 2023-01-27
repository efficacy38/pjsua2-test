import pjsua2 as pj
import time
import gc
from inspect import currentframe, getframeinfo
import threading
# Subclass to extend the Account and get notifications etc.

isQuitting = False


class Account(pj.Account):
    def quit(self):
        pass

    def onRegState(self, prm):
        global isQuitting
        print("***OnRegState: " + prm.reason)
        tmp = get_linenumber_and_filename()
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        isQuitting = True
        raise pj.Error(2, 'Error', 'WHAT', *tmp)
        # self.quit()

# pjsua2 test function


def get_linenumber_and_filename():
    cf = currentframe()
    return (getframeinfo(cf).filename, cf.f_back.f_lineno)


isQuit = False


def pjsua2_register():
    global ep
    gc.disable()
    # Create and initialize the library
    ep_cfg = pj.EpConfig()
    ep = pj.Endpoint()
    ep.libCreate()
    ep_cfg.uaConfig.threadCnt = 1
    ep_cfg.uaConfig.mainThreadOnly = True
    ep_cfg.logConfig.level = 10
    ep_cfg.logConfig.consoleLevel = 10
    # ep_cfg.logConfig.writer = pj.LogWriter
    ep_cfg.logConfig.filename = "test.log"
    ep.libInit(ep_cfg)

    # Create SIP transport. Error handling sample is shown
    sipTpConfig = pj.TransportConfig()
    sipTpConfig.port = 5060
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)
    # Start the library
    ep.libStart()

    # create a account config
    # AccountRegConfig, to specify registration settings, such as registrar server and retry interval.
    # AccountSipConfig, to specify SIP settings, such as credential information and proxy server.
    # AccountCallConfig, to specify call settings, such as whether reliable provisional response (SIP 100rel) is required.
    # AccountPresConfig, to specify presence settings, such as whether presence publication (PUBLISH) is enabled.
    # AccountMwiConfig, to specify MWI (Message Waiting Indication) settings.
    # AccountNatConfig, to specify NAT settings, such as whether STUN or ICE is used.
    # AccountMediaConfig, to specify media settings, such as Secure RTP (SRTP) related settings.
    # AccountVideoConfig, to specify video settings, such as default capture and render device.

    acfg = pj.AccountConfig()
    # idURI is AoR record, specify where you are
    acfg.idUri = "sip:2@kamailio"

    # registrarURI is the UAS URI
    acfg.regConfig.registrarUri = "sip:kamailio"

    # pj.AuthCredInfo take following five argument
    # 1. string &scheme: like "digest"
    # 2. string &realm: the realm of gigest auth, tipically set "*"
    # 3. string &user_name
    # 4. int data_type: "0" mean the following data contain plain text pasword
    # 5. string data: the password
    cred = pj.AuthCredInfo("digest", "*", "2", 0, "test")

    # authCreds is an array contain multiple credential
    # this can be challenge by the SIP proxies
    acfg.sipConfig.authCreds.append(cred)

    # instane the account
    acc = Account()
    # create the account
    acc.create(acfg)

    # please check this issue to handle the sleep usage
    # https://github.com/pjsip/pjproject/issues/2685
    # libHandleEvents, this function will also scan and run any pending jobs in the list.
    while True:
        ep.libHandleEvents(20)
        if isQuitting:
            break


    # Destroy the library
    ep.libDestroy()
    gc.enable()


if __name__ == "__main__":
    pjsua2_register()
