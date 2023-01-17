/*
 * Copyright (C) 2008-2013 Teluu Inc. (http://www.teluu.com)
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */
#include <iostream>
#include <pj/file_access.h>
#include <pjsua2.hpp>

#define THIS_FILE "pjsua2_demo.cpp"

using namespace pj;

class MyEndpoint : public Endpoint {
public:
  MyEndpoint() : Endpoint(){};
  virtual pj_status_t onCredAuth(OnCredAuthParam &prm) {
    std::cout << "*** Callback onCredAuth called ***" << std::endl;
    /* Return PJ_ENOTSUP to use
     * pjsip_auth_create_aka_response()/<b>libmilenage</b> (default),
     * if PJSIP_HAS_DIGEST_AKA_AUTH is defined.
     */
    return PJ_ENOTSUP;
  }
};

class MyAccount;

class MyCall : public Call {
private:
  MyAccount *myAcc;
  AudioMediaPlayer *wav_player;

public:
  MyCall(Account &acc, int call_id = PJSUA_INVALID_ID) : Call(acc, call_id) {
    wav_player = NULL;
    myAcc = (MyAccount *)&acc;
  }

  ~MyCall() {
    if (wav_player)
      delete wav_player;
  }

  virtual void onCallState(OnCallStateParam &prm);
  virtual void onCallMediaState(OnCallMediaStateParam &prm);
};

class MyAccount : public Account {
public:
  std::vector<Call *> calls;

public:
  MyAccount() {}

  ~MyAccount() {
    std::cout << "*** Account is being deleted: No of calls=" << calls.size()
              << std::endl;

    for (std::vector<Call *>::iterator it = calls.begin(); it != calls.end();) {
      delete (*it);
      it = calls.erase(it);
    }
  }

  void removeCall(Call *call) {
    for (std::vector<Call *>::iterator it = calls.begin(); it != calls.end();
         ++it) {
      if (*it == call) {
        calls.erase(it);
        break;
      }
    }
  }

  virtual void onRegState(OnRegStateParam &prm) {
    AccountInfo ai = getInfo();
    std::cout << (ai.regIsActive ? "*** Register: code="
                                 : "*** Unregister: code=")
              << prm.code << std::endl;
  }

  virtual void onIncomingCall(OnIncomingCallParam &iprm) {
    Call *call = new MyCall(*this, iprm.callId);
    CallInfo ci = call->getInfo();
    CallOpParam prm;

    std::cout << "*** Incoming Call: " << ci.remoteUri << " [" << ci.stateText
              << "]" << std::endl;

    calls.push_back(call);
    prm.statusCode = (pjsip_status_code)200;
    call->answer(prm);
  }
};

void MyCall::onCallState(OnCallStateParam &prm) {
  PJ_UNUSED_ARG(prm);

  CallInfo ci = getInfo();
  std::cout << "*** Call: " << ci.remoteUri << " [" << ci.stateText << "]"
            << std::endl;

  if (ci.state == PJSIP_INV_STATE_DISCONNECTED) {
    // myAcc->removeCall(this);
    /* Delete the call */
    // delete this;
  }
}

void MyCall::onCallMediaState(OnCallMediaStateParam &prm) {
  PJ_UNUSED_ARG(prm);

  CallInfo ci = getInfo();
  AudioMedia aud_med;
  // AudioMedia &play_dev_med =
  //     MyEndpoint::instance().audDevManager().getPlaybackDevMedia();
  Endpoint::instance().audDevManager().setNullDev();

  try {
    // Get the first audio media
    aud_med = getAudioMedia(-1);
  } catch (...) {
    std::cout << "Failed to get audio media" << std::endl;
    return;
  }

  if (!wav_player) {
    wav_player = new AudioMediaPlayer();
    try {
      wav_player->createPlayer("./input.16.wav", 0);
    } catch (...) {
      std::cout << "Failed opening wav file" << std::endl;
      delete wav_player;
      wav_player = NULL;
    }
  }

  // This will connect the wav file to the call audio media
  if (wav_player)
    wav_player->startTransmit(aud_med);

  // And this will connect the call audio media to the sound device/speaker
    //aud_med.startTransmit(play_dev_med);
}

extern "C" int main() {
  int ret = 0;
  MyEndpoint ep;

  try {
    ep.libCreate();

    // Init library
    EpConfig ep_cfg;
    ep.libInit(ep_cfg);

    // Create transport
    TransportConfig tcfg;
    tcfg.port = 5060;
    ep.transportCreate(PJSIP_TRANSPORT_UDP, tcfg);

    // Add account
    AccountConfig acc_cfg;
    acc_cfg.idUri = "sip:2@kamailio";
    std::cout << "*** start sending SIP REGISTER ***";
    acc_cfg.regConfig.registrarUri = "sip:kamailio";

    /* if there needed credential to login, just add following lines */
    AuthCredInfo cred("digest", "*", "2", 0, "test");
    acc_cfg.sipConfig.authCreds.push_back(cred);

    MyAccount *acc(new MyAccount);
    acc->create(acc_cfg);

    // Start library
    ep.libStart();
    std::cout << "*** PJSUA2 STARTED ***" << std::endl;

    // Make outgoing call
    // Call *call = new MyCall(*acc);
    // acc->calls.push_back(call);
    // CallOpParam prm(true);
    // prm.opt.audioCount = 1;
    // prm.opt.videoCount = 0;
    // call->makeCall("sip:1@kamailio", prm);

    // Hangup all calls after 10 sec
    pj_thread_sleep(10000);
    ep.hangupAllCalls();
    pj_thread_sleep(4000);

    // Destroy library
    std::cout << "*** PJSUA2 SHUTTING DOWN ***" << std::endl;
    delete acc; /* Will delete all calls too */

    ret = PJ_SUCCESS;
  } catch (Error &err) {
    std::cout << "Exception: " << err.info() << std::endl;
    ret = 1;
  }

  try {
    ep.libDestroy();
  } catch (Error &err) {
    std::cout << "Exception: " << err.info() << std::endl;
    ret = 1;
  }

  if (ret == PJ_SUCCESS) {
    std::cout << "Success" << std::endl;
  } else {
    std::cout << "Error Found" << std::endl;
  }

  return ret;
}
