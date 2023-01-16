import pjsua2 as pj
import time
import gc
# Subclass to extend the Account and get notifications etc.


class Account(pj.Account):
    def onRegState(self, prm):
        print("***OnRegState: " + prm.reason)

# pjsua2 test function


def pjsua2_test():
  # Create and initialize the library
  ep_cfg = pj.EpConfig()
  ep = pj.Endpoint()
  ep.libCreate()
  ep.libInit(ep_cfg)

  # Create SIP transport. Error handling sample is shown
  sipTpConfig = pj.TransportConfig();
  sipTpConfig.port = 5060;
  ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig);
  # Start the library
  ep.libStart();

  acfg = pj.AccountConfig();
  acfg.idUri = "sip:test@pjsip.org";
  acfg.idUri()
  acfg.regConfig.registrarUri = "sip:pjsip.org";
  cred = pj.AuthCredInfo("digest", "*", "test", 0, "pwtest");
  acfg.sipConfig.authCreds.append( cred );
  # Create the account
  acc = Account();
  acc.create(acfg);
  # Here we don't have anything else to do..
  time.sleep(10);

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
    pjsua2_test()
