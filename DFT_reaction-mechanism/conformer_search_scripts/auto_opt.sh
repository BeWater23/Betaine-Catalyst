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


##### Input reading ######

# Check if at least one argument was provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"

# Check if the input file exists
if [ -f "$input_file" ]; then
    echo "Input file found: $input_file"
    # Now you can use "$input_file" in your script
else
    echo "Input file not found: $input_file"
    exit 1
fi

constrain=false
numbers=()

# Check if there is an optional --constrain argument
if [[ $# -gt 1 && "$2" == "--constrain="* ]]; then
    constrain=true
    numbers_string="${2#*=}"
    IFS=',' read -r -a numbers <<< "$numbers_string"
    numbers=$(echo "${numbers[*]}" | tr ',' ' ')
fi


###### 1)ensemble_splitting #########
line_number=0
conf_number=0

while IFS= read -r line; do
    # Increment line number
    ((line_number++))
        # Check if the line starts with two blanks and a number (indicating the number of atoms)
        if [[ $line =~ ^[[:blank:]]*[[:digit:]] ]]; then
            ((conf_number++))
            atom_number=$(echo "$line" | awk '{print $NF}')
            starting_line_of_conformer=$line_number
            end_line_of_conformer=$((line_number+atom_number+1)) #plus 1 sicnce there is always the line containing the energy and the conformer name
            conformer_name="censo_$conf_number"
            #echo "atom_number=$atom_number"
            #echo "starting_line_of_conformer:$starting_line_of_conformer"
            #echo "end_line_of_conformer:$end_line_of_conformer"
            mkdir "$conformer_name"
            sed -n "${starting_line_of_conformer},${end_line_of_conformer}p" "$input_file" > geom_ini.xyz
            mv geom_ini.xyz "$conformer_name"/
        fi
done < $input_file


###### 2)optimization ########

 # Code to execute if a constrain keyword was provided (TS search)
if $constrain; then
    echo "Constraining atoms $numbers"
    for dir in ./*; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            copy_template "opt_constrained_m06-2x.chm" "$dir"
            cd $dir
            sed -i "s/frozen= {[^}]*}/frozen= {$numbers}/g" opt_constrained_m06-2x.chm
            #bwHPC_chemshell large opt_constrained_m06-2x
            echo "Submitted constrained optimization of $dir" 
            cd ..
        fi
    done
  # Code to execute if there is no constrain (minimum search)
else
    for dir in ./*; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            copy_template "opt_m06-2x_numfreq.chm" "$dir"
            cd $dir
            bwHPC_chemshell large opt_m06-2x_numfreq
            echo "Submitted constrained optimization of $dir" 
            cd ..
        fi
    done
fi


