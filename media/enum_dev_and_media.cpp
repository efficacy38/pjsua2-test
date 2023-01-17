#include <pjsua2.hpp>
#include <iostream>
#include <pj/file_access.h>

using namespace pj;

void enumDevs(Endpoint &ep){
    AudDevManager* aud_mgr = &ep.audDevManager();
    std::cout << "enum the devs, and length is " << aud_mgr->enumDev2().size() << std::endl;

    // important: the enumDev2() only create a copy of device object
    // all memory should manage by developer
    for (auto dev : aud_mgr->enumDev2()){
        std::cout << dev.name << "  " << dev.driver << std::endl;
    }
}

void enumMedia(Endpoint &ep){
    AudDevManager* aud_mgr = &ep.audDevManager();

    // important: the Endpoint::mediaEnumPorts2() and Call::getAudioMedia() only create a copy of device object
    // all memory should manage by developer
    std::cout << "enum the local media, and length is " << ep.mediaEnumPorts2().size() << std::endl;
    AudioMediaVector2 med_vec = ep.mediaEnumPorts2();
    for (AudioMedia med : med_vec){
        // media info ref: https://www.pjsip.org/pjsip/docs/html/structpj_1_1MediaFormatAudio.htm
        ConfPortInfo med_info = med.getPortInfo();
        std::cout << "id: " << med_info.portId << ",name: " << med_info.name << ", format(channelCount): "
            << med_info.format.channelCount << std::endl;
    }
}

void showPlaybackDev(Endpoint &ep){
    AudDevManager* aud_mgr = &ep.audDevManager();
    std::cout << "playback dev's id is " << aud_mgr->getPlaybackDev() << std::endl;
}

void enumPlayBack(Endpoint &ep){
    AudDevManager* aud_mgr = &ep.audDevManager();
    // std::cout << dev.name << "  " << dev.driver << std::endl;
}

int main(){
    Endpoint ep;
    ep.libCreate();
    EpConfig ep_cfg;
    ep.libInit( ep_cfg );
    // ep.audDevManager().setNullDev();

    enumDevs(ep);
    showPlaybackDev(ep);
    enumMedia(ep);
}
