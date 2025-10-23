#! /usr/bin/env bash

function bluer_objects_mlflow_lock_unlock() {
    local object_name=$(bluer_ai_clarify_object $1 .)

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_objects.mlflow.lock \
        unlock \
        --object_name $object_name \
        "${@:2}"

}
