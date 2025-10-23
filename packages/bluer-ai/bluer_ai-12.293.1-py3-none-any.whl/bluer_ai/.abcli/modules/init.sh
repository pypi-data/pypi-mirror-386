#! /usr/bin/env bash

function bluer_ai_init() {
    local plugin_name=$(bluer_ai_clarify_input "$1" all)

    local options=$2

    local current_path=$(pwd)

    if [ "$plugin_name" == "all" ]; then
        [[ "$abcli_is_mac" == true ]] &&
            local options=~terraform,$options

        source $abcli_path_abcli/bluer_ai/.abcli/bluer_ai.sh "$options" "${@:3}"
    elif [ "$plugin_name" == "clear" ]; then
        bluer_ai_init - clear
    else
        local plugin_name=$1
        local module_name=$(bluer_ai_get_module_name_from_plugin $plugin_name)

        for filename in $(python3 -m $module_name locate)/.abcli/*.sh; do
            source $filename
        done
    fi

    [[ "$current_path" == "$abcli_path_git"* ]] &&
        cd $current_path

    local do_clear=$(bluer_ai_option_int "$options" clear 0)
    [[ "$do_clear" == 1 ]] &&
        clear

    return 0
}
