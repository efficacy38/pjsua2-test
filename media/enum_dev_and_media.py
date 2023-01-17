import pjsua2 as pj
import time
import os
import gc


def enumDevs(ep):
    aud_mgr = ep.instance().audDevManager()
    # important: the enumDev2() only create a copy of device object
    # all memory should manage by developer
    print("enum the devs, and the length is {}".format(len(aud_mgr.enumDev2())))
    for dev in aud_mgr.enumDev2():
        print("name: {}, driver: {}".format())


def enumMedia(ep):
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
        ep_cfg = pj.EpConfig()
        ep.libCreate()
        ep.libInit(ep_cfg)
        ep.libStart()

        # Use Null Audio Device as main media clock. This is useful for improving
        # media clock (see also https://trac.pjsip.org/repos/wiki/FAQ#tx-timing)
        # especially when sound device clock is jittery.
        ep.audDevManager().setNullDev()

        enumDevs(ep)
        enumMedia(ep)

    except Exception as e:
        print("catch exception!!, exception error is: {}".format(e.args))

    # close the library
    try:
        ep.libDestroy()
    except Exception as e:
        print("catch exception!!, exception error is: {}".format(e.args))


if __name__ == '__main__':
    main()
