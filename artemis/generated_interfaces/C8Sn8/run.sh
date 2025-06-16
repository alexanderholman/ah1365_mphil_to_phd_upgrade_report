#!/bin/bash

/home/alexander/.local/artemis/bin/artemis_executable-2.0.0 -f default.param.in > artemis.default.out 2>&1 &
/home/alexander/.local/artemis/bin/artemis_executable-2.0.0 -f no_shift.param.in > artemis.no_shift.out 2>&1 &