#! /usr/bin/env bash

function bluer_sandbox_notebooks_build() {
    local notebook_name=$(bluer_ai_clarify_input $1 notebook)

    [[ "$notebook_name" == *.ipynb ]] && notebook_name="${notebook_name%.ipynb}"

    export bluer_sandbox_notebooks_input="${@:2}"

    jupyter-nbconvert \
        $notebook_name.ipynb \
        -y --ExecutePreprocessor.timeout=-1 --execute --allow-errors \
        --to html \
        --output-dir $abcli_object_path

    mv -v \
        $abcli_object_path/$notebook_name.html \
        $abcli_object_path/$abcli_object_name.html
}
