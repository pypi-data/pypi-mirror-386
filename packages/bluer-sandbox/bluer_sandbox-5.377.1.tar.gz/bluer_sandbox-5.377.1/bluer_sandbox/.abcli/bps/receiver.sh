#! /usr/bin/env bash

function bluer_sandbox_bps_receiver() {
    bluer_ai_eval ,$1 \
        sudo \
        hcitool \lescan \
        "${@:2}"
}
