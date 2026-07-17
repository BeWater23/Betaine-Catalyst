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
                     folder_name="ts_opt"
                        if [ -d "$folder_name" ]; then
                            echo "Folder '$folder_name' already exists. TS optimization already done."
                        else
                            tar -xf *.tgz
                            rm *.tgz
                            mkdir ts_opt
                            cp st_ac*/geom_opt.xyz ts_opt/ts_initial.xyz
                            cd st_ac*
                            if [ ! -f "vibmode_0001_mov.xyz" ]; then
                                echo "File 'vibmode_0001' does not exist."
                                exit 1
                            fi
                            ### defining the 2nd structure from vibmode as ts_second
                            line_number=0
                            while IFS= read -r line; do
                                ((line_number++))
                                if [ "$line_number" -eq 1 ]; then
                                atom_number=$(echo "$line" | awk '{print $NF}')
                                echo "atom_number: $atom_number"
                                start_of_ts2=$((line_number+atom_number+2))
                                end_of_ts2=$((start_of_ts2+atom_number+1))
                                fi
                            done < vibmode_0001_mov.xyz   
                            sed -n "${start_of_ts2},${end_of_ts2}p" "vibmode_0001_mov.xyz" > ts_second.xyz
                            mv ts_second.xyz ../ts_opt/
                            cd ..
                            ###
                            copy_template "ts_opt_m06-2x.chm" "ts_opt"
                            cd ts_opt
                            bwHPC_chemshell large ts_opt_m06-2x
                            echo "TS Dimer optimization submitted"
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
