#! /usr/bin/env bash

function bluer_sandbox_bps_beacon() {
    bluer_ai_eval ,$1 \
        sudo -E \
        $(which python3) -m \
        bluer_sandbox.bps.beacon \
        "$@"
}
