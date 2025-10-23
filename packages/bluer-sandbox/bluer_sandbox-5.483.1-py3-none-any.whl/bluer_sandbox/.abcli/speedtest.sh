#! /usr/bin/env bash

function bluer_sandbox_speedtest() {
    local options=$1
    local do_install=$(bluer_ai_option_int "$options" install 1)
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_ping=$(bluer_ai_option_int "$options" ping 1)

    if [[ "$BLUER_AI_WIFI_SSID" == "Sion" ]]; then
        bluer_ai_browse \
            https://speedtest.mci.ir/

        if [[ "$do_ping" == 1 ]]; then
            ping google.com
        fi

        return
    fi

    local install_command=""
    if [[ "$do_install" == 1 ]]; then
        if [[ "$abcli_is_mac" == true ]]; then
            install_command="brew install speedtest-cli"
        elif [[ "$abcli_is_ubuntu" == true ]]; then
            install_command="sudo apt install -y speedtest-cli"
        else
            bluer_ai_log_error "do not know how to install speedtest."
            return 1
        fi

        bluer_ai_eval dryrun=$do_dryrun \
            $install_command
        [[ $? -ne 0 ]] && return 1
    fi

    bluer_ai_eval dryrun=$do_dryrun \
        speedtest
    [[ $? -ne 0 ]] && return 1

    if [[ "$do_ping" == 1 ]]; then
        ping google.com
    fi
}
