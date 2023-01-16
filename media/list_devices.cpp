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

extern "C" int main()
{
    int ret = 0;
    Endpoint ep;

    try {
        ep.libCreate();

        // Init library
        EpConfig ep_cfg;
        ep.libInit(ep_cfg);

        // Start library
        ep.libStart();
        std::cout << "*** PJSUA2 STARTED ***" << std::endl;

        // list all the device
        {
            
        }
        ret = PJ_SUCCESS;
    } catch (Error& err) {
        std::cout << "Exception: " << err.info() << std::endl;
        ret = 1;
    }

    try {
        ep.libDestroy();
    } catch (Error& err) {
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
