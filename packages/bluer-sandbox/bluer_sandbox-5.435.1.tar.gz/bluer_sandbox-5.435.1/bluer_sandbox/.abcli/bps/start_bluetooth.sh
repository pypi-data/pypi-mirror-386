#! /usr/bin/env bash

function bluer_sandbox_bps_start_bluetooth() {
    bluer_ai_log "starting bluetooth..."

    sudo systemctl start bluetooth
    sudo systemctl status --no-pager bluetooth

    sudo bluetoothctl power on
    sudo bluetoothctl discoverable on
    bluer_ai_eval - \
        sudo bluetoothctl show
}
