import pjsua2 as pj
import time
import os
import gc

def main():
    ep = None
    try: 
        paths = [ "../../../../tests/pjsua/wavs/input.16.wav",\
                  "../../tests/pjsua/wavs/input.16.wav",\
                  "./input.16.wav"]

        # init the lib
        ep = pj.Endpoint()
        ep_cfg = pj.EpConfig()
        ep.libCreate()
        ep.libInit(ep_cfg)
        filename = None

        for path in paths:
            if os.path.exists(path):
                filename = path

        if(filename == None):
            raise Exception('path not found')

        ep.libStart()

        # Use Null Audio Device as main media clock. This is useful for improving
        # media clock (see also https://trac.pjsip.org/repos/wiki/FAQ#tx-timing)
        # especially when sound device clock is jittery.
        ep.audDevManager().setNullDev()
        
        # create player and recorder
        amp = pj.AudioMediaPlayer()
        amp.createPlayer(filename)
        amr = pj.AudioMediaRecorder()
        amr.createRecorder("recorder_test_output.wav")
        
        # start transmit(this uni-directional, amp(src) -> amr(sink))
        amp.startTransmit(amr);
        
        # then wait 5 sec to transmit
        ep.libHandleEvents(5000)

        # python gc would not destroy the object with correct order
        del amp, amr
    except Exception as e:
        print("catch exception!!, exception error is: {}".format(e.args))

    # close the library
    try:
        ep.libDestroy()
    except Exception as e:
        print("catch exception!!, exception error is: {}".format(e.args))

if __name__ == '__main__':
    main()
