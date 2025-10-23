#! /usr/bin/env bash

function bluer_ai_git_set_remote() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local remote=$(bluer_ai_option_choice "$options" https,ssh)

    local repo_name=$(bluer_ai_git_get_repo_name)

    bluer_ai_log "setting $repo_name.remote to $remote ..."

    local remote_url
    if [[ "$remote" == "https" ]]; then
        if [[ -z "$BLUER_AI_GITHUB_TOKEN" ]]; then
            bluer_ai_warning "generate a token: https://github.com/settings/tokens -> .env/BLUER_AI_GITHUB_TOKEN..."
            return 1
        fi

        echo $BLUER_AI_GITHUB_TOKEN | pbcopy
        bluer_ai_log "Ctrl+V to paste the github token when asked for password."

        git config --global credential.helper store

        remote_url="https://github.com/kamangir/$repo_name.git"
    else
        remote_url="git@github.com:kamangir/$repo_name.git"
    fi

    bluer_ai_eval dryrun=$do_dryrun \
        git remote set-url origin \
        $remote_url
    [[ $? -ne 0 ]] && return 1

    git remote -v
}
