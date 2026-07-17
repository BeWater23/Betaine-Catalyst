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
            if [ -d "ts_opt" ]; then
                cd ts_opt
                if [ -f chemsh* ]; then
                    echo "Output file exists in $dir/ts_opt."
                    if grep -q "Optimisation converged" chemsh*; then
                        echo "Optimization converged."
                        folder_name="spe"
                            if [ -d "$folder_name" ]; then
                                echo "Folder '$folder_name' already exists. SPE calc already done."
                            else
                                tar -xf *.tgz
                                rm *.tgz
                                mkdir spe
                                cp st_ac*/ts_opt.xyz spe/
                                copy_template "spe_ts_m06-2x.chm" "spe"
                                cd spe 
                                #bwHPC_chemshell vsmall spe_ts_m06-2x
                                echo "SPE calculation submitted"
                                cd ..
                            fi
                    else
                        echo "Optimization not (yet) converged."
                    fi

                    # Now it will check if frequency calc crashed or not
                    if grep -q "Fatal error : dscf failed - see dscf.log" chemsh*; then
                        echo "Analytical frequency calculation crashed. Starting finite differences frequency calculation..."
                        folder_name_="numfreq"
                        if [ -d "$folder_name_" ]; then
                            echo "Folder '$folder_name_' already exists. numfreq calc already done."
                        else
                            mkdir numfreq
                            cp st_ac*/ts_opt.xyz numfreq/
                            copy_template "numfreq_ts_m06-2x.chm" "numfreq"
                            cd numfreq/
                            #bwHPC_chemshell large numfreq_ts_m06-2x
                            echo "Numerical frequency calculation submitted"
                            cd ..
                        fi
                    else 
                        awk '/Thermochemical analysis/, /^[[:space:]]*4/ {print}' chemsh*
                    fi  

                else
                    echo "No output file exists in $dir/ts_opt."
                fi
                cd ..
            else
                echo "ts_opt not found in $dir"
            fi
            cd ..
            echo
        fi
done
