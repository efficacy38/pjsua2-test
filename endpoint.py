import pjsua2 as pj
import time
# Subclass to extend the Account and get notifications etc.


class Account(pj.Account):
    def onRegState(self, prm):
        print("***OnRegState: " + prm.reason)

# pjsua2 test function


def pjsua2_endpoint():

    # Create and initialize the library(Endpoint class)
    # 1. UAConfig, to specify core SIP user agent settings.
    # 2. MediaConfig, to specify various media global settings
    # 3. LogConfig, to customize logging settings.
    ep_cfg = pj.EpConfig()

    # https://www.pjsip.org/docs/book-latest/html/reference.html?highlight=level#_CPPv4N2pj9LogConfigE
    # lower is less output
    ep_cfg.logConfig.level = 5;
    ep_cfg.logConfig.consoleLevel = 4;
    # https://www.pjsip.org/docs/book-latest/html/reference.html?highlight=maxcalls#_CPPv4N2pj8UaConfigE
    ep_cfg.uaConfig.maxCalls = 4;
    # ep_cfg.medConfig.sndClockRate = 16000;

    # create the endpoint object
    ep = pj.Endpoint()
    ep.libCreate()
    ep.libInit(ep_cfg)

    # Create SIP transport. Error handling sample is shown
    sipTpConfig = pj.TransportConfig()
    sipTpConfig.port = 5060
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)
    # Start the library
    ep.libStart()

    # Here we don't have anything else to do..
    time.sleep(1)

    # Destroy the library
    ep.libDestroy()


if __name__ == "__main__":
    pjsua2_endpoint()
