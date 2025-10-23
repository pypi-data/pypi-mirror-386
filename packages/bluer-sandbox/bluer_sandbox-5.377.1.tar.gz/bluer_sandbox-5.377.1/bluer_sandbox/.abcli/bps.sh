#! /usr/bin/env bash

# continues sandbox/bps/v1

function bluer_sandbox_bps() {
    local task=${1:-test}

    if [[ "$abcli_is_rpi" == false ]]; then
        bluer_ai_log_error "@sandbox: bps: only runs on rpi."
        return 1
    fi

    local options=$2
    local do_start_bluetooth=1
    [[ "|install|start|" == *"|$task|"* ]] &&
        do_start_bluetooth=0
    do_start_bluetooth=$(bluer_ai_option_int "$options" start_bluetooth $do_start_bluetooth)

    if [[ "$do_start_bluetooth" == 1 ]]; then
        bluer_sandbox_bps_start_bluetooth "$@"
        [[ $? -ne 0 ]] && return 1
    fi

    local function_name=bluer_sandbox_bps_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 bluer_sandbox.bps "$@"
}

bluer_ai_source_caller_suffix_path /bps
