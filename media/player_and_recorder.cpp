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

extern "C" int main() {
  int ret = 0;
  Endpoint ep;

  try {
    ep.libCreate();
    const char *paths[] = {"../../../../tests/pjsua/wavs/input.16.wav",
                           "../../tests/pjsua/wavs/input.16.wav",
                           "input.16.wav"};
    unsigned i;
    const char *filename = NULL;

    // Init library
    EpConfig ep_cfg;
    ep.libInit(ep_cfg);

    for (i = 0; i < PJ_ARRAY_SIZE(paths); ++i) {
      if (pj_file_exists(paths[i])) {
        filename = paths[i];
        break;
      }
    }

    if (!filename) {
      PJSUA2_RAISE_ERROR3(PJ_ENOTFOUND, "main()",
                          "Could not locate input.16.wav");
    }

    // Start library
    ep.libStart();
    std::cout << "*** PJSUA2 STARTED ***" << std::endl;

    /* Use Null Audio Device as main media clock. This is useful for improving
     * media clock (see also https://trac.pjsip.org/repos/wiki/FAQ#tx-timing)
     * especially when sound device clock is jittery.
     */
    ep.audDevManager().setNullDev();

    /* And install sound device using Extra Audio Device */
    /* ExtraAudioDevice auddev2(-1, -1); */
    /* try { */
    /*     auddev2.open(); */
    /* } catch (...) { */
    /*     std::cout << "Extra sound device failed" << std::endl; */
    /* } */

    // Create player and recorder
    {
      AudioMediaPlayer amp;
      amp.createPlayer(filename);

      AudioMediaRecorder amr;
      amr.createRecorder("recorder_test_output.wav");

      // it would transmit a media source to a media sink
      // the recorder_test_output would have the same media between
      // `recorder_test_output.wav` and `input.16.wav`
      amp.startTransmit(amr);
      /* if (auddev2.isOpened()) */
      /*     amp.startTransmit(auddev2); */

      pj_thread_sleep(5000);
    }
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
