#! /usr/bin/env bash

function bluer_sandbox_bps_beacon_and_receiver() {
    sudo btmgmt --index 0 le on
    sudo btmgmt --index 0 connectable on
    sudo btmgmt --index 0 advertising on
    sudo btmgmt --index 0 scanning on

    bluer_ai_eval ,$1 \
        sudo -E \
        $(which python3) -m \
        bluer_sandbox.bps.utils.beacon_and_receiver \
        "${@:2}"
}
