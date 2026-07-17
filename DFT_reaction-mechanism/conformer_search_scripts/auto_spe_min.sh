#!/bin/bash

##Author: Lucca Pfitzer 
##Version: 06th April 2024

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${AUTOCONF_TEMPLATE_DIR:-$SCRIPT_DIR/templates}"

copy_template() {
    local template_name="$1"
    local target_dir="$2"
    local source_file="$TEMPLATE_DIR/$template_name"

    if [ ! -f "$source_file" ]; then
        echo "Required template not found: $source_file"
        echo "Set AUTOCONF_TEMPLATE_DIR to the directory containing the Chemshell .chm templates."
        exit 1
    fi

    cp "$source_file" "$target_dir/"
}

### 

for dir in ./*; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            cd $dir 
            if [ -f chemsh* ]; then
                echo "Output file exists in $dir."
                if grep -q "Optimisation converged" chemsh*; then
                     echo "Optimization converged."
                     awk '/Thermochemical analysis/, /^[[:space:]]*4/ {print}' chemsh*
                     folder_name="spe"
                        if [ -d "$folder_name" ]; then
                            echo "Folder '$folder_name' already exists. SPE calc already done."
                        else
                            tar -xf *.tgz
                            rm *.tgz
                            mkdir spe
                            cp st_ac*/geom_opt.xyz spe/
                            copy_template "spe_m06-2x_cosmo.chm" "spe"
                            cd spe 
                            bwHPC_chemshell vsmall spe_m06-2x_cosmo
                            echo "SPE calculation started!"
                            cd ..
                        fi
                else
                     echo "Optimization not (yet) converged."
                fi
            else
             echo "No output file exists in $dir."
            fi
            cd ..
            echo
        fi
done
