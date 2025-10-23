#! /usr/bin/env bash

function bluer_objects_gif() {
    local options=$1
    local do_open=$(bluer_ai_option_int "$options" open 0)
    if [[ "$do_open" == 1 ]]; then
        local options=$2
        local do_download=$(bluer_ai_option_int "$options" download 0)

        local object_name=$(bluer_ai_clarify_object $3 .)
        local filename=$(bluer_ai_option "$options" filename $object_name.gif)

        [[ "$do_download" == 1 ]] &&
            bluer_objects_download \
                filename=$filename \
                $object_name

        bluer_ai_browse $ABCLI_OBJECT_ROOT/$object_name/$filename

        return
    fi

    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_download=$(bluer_ai_option_int "$options" download $(bluer_ai_not $do_dryrun))
    local do_upload=$(bluer_ai_option_int "$options" upload $(bluer_ai_not $do_dryrun))

    local object_name=$(bluer_ai_clarify_object $2 .)

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download - $object_name

    bluer_ai_log "generating animated gif: $object_name ..."

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_objects.graphics \
        generate_animated_gif \
        --object_name $object_name \
        "${@:3}"
    local status="$?"

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $object_name

    return $status
}
