#!/bin/bash

##Author: Lucca Pfitzer 
##Version: 08th April 2024

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

##### Input reading ######
ts=false
if [[ "$1" == "--ts" ]]; then
    ts=true
fi

#### Energy evaluation for both cases ####
if $ts; then
    echo "Energy evaluation TS mode starting..."
    echo
    for dir in ./*; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            cd $dir
            cd ts_opt
            folder_name="spe"
            # extracting the spe
            if [ -d "$folder_name" ]; then
                cd spe
                if [ -f chemsh* ]; then
                    if grep -q "Energy (  turbomole):" chemsh*; then
                        echo "SPE calculation finished for $(basename "$dir")"
                        line=$(grep -E "Energy \(  turbomole\):" chemsh*)
                        spe_value=$(echo "$line" | awk '{ print $4 }')
                        echo "SPE = $spe_value H"
                    else
                        echo "SPE calculation not (yet) finished"
                    fi
                else
                    echo "No SPE output file found."
                fi
                cd ..
            else
                echo "No folder '$folder_name' exists."
            fi
            # extracting the free energy contributions
            if [ -f chemsh* ]; then
                if grep -q "Fatal error : dscf failed - see dscf.log" chemsh*; then
                            echo "Analytical frequency calculation crashed. Extracting the results from the numerical frequency calc."
                            folder_name_="numfreq"
                            if [ -d "$folder_name_" ]; then
                                cd $folder_name_
                                # extracting the free energy contributions
                                if [ -f chemsh* ]; then
                                    awk '/Thermochemical analysis/, /^[[:space:]]*4/ {print}' chemsh*
                                    G_con=$(grep -A 6 'Energy contributions for solutions' chemsh* | awk '/G\(T\)/{getline; print $3}')
                                    echo "G(T) = $G_con H"
                                    free_energy=$(echo "$spe_value + $G_con" | bc)
                                    free_energy_rounded=$(printf "%.6f" "$free_energy")
                                    echo "$(basename "$dir") total free energy G = $free_energy_rounded H"
                                else
                                    echo "Numerical frequency calculation (not) yet finished."
                                fi
                                cd ..
                            else
                                echo "No folder including numerical frequency calculations found."
                            fi
                else
                    if [ -f chemsh* ]; then
                        echo "Analytical frequency calculation worked: Extracting results from it."
                        awk '/Thermochemical analysis/, /^[[:space:]]*4/ {print}' chemsh*
                        G_con=$(grep -A 6 'Energy contributions for solutions' chemsh* | awk '/G\(T\)/{getline; print $3}')
                        echo "G(T) = $G_con H"
                        if [ -n "$spe_value" ] && [ -n "$G_con" ]; then
                            free_energy=$(echo "$spe_value + $G_con" | bc)
                            free_energy_rounded=$(printf "%.6f" "$free_energy")
                            echo "$(basename "$dir") total free energy G = $free_energy_rounded H"
                        else
                         echo "Not able to calculate total free energy due to missing values for spe or G."
                        fi
                    else
                        echo "Error: Numerical frequency calculation results not found. Check the Chemshell output."
                    fi
                fi
            else
                echo "No geometry optimization output file found."
            fi
            cd ../..
            echo
        fi
    done

else
    echo "Energy evaluation minima mode starting..."
    echo
    for dir in ./*; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            cd $dir
            folder_name="spe"
            # extracting the spe
            if [ -d "$folder_name" ]; then
                cd spe
                if grep -q "Energy (  turbomole):" chemsh*; then
                    echo "SPE calculation finished for $(basename "$dir")"
                    line=$(grep -E "Energy \(  turbomole\):" chemsh*)
                    spe_value=$(echo "$line" | awk '{ print $4 }')
                    echo "SPE = $spe_value H"
                else
                    echo "SPE calculation not (yet) finished"
                fi
                cd ..
            else
                echo "No folder '$folder_name' exists."
            fi
            # extracting the free energy contributions
            if [ -f chemsh* ]; then
                awk '/Thermochemical analysis/, /^[[:space:]]*4/ {print}' chemsh*
                G_con=$(grep -A 6 'Energy contributions for solutions' chemsh* | awk '/G\(T\)/{getline; print $3}')
                echo "G(T) = $G_con H"
                if [ -n "$spe_value" ] && [ -n "$G_con" ]; then
                    free_energy=$(echo "$spe_value + $G_con" | bc)
                    free_energy_rounded=$(printf "%.6f" "$free_energy")
                    echo "$(basename "$dir") total free energy G = $free_energy_rounded H"
                else
                    echo "Not able to calculate total free energy due to missing values for spe or G."
                fi
            else
                echo "No output from geometry optimization exists. Not possible to extract frequencies."
            fi
            cd ..
            echo
        fi
    done
fi

echo "Relative energies of all conformers written to conformer_energies.txt"
python3 "$SCRIPT_DIR/energy_sorting.py" > conformer_energies.txt

# Input file containing the order of censo_x folders and energies
input_file="conformer_energies.txt"   # Replace with your input file if different
output_file="ts_conformers.xyz"

# Clear the output file before appending
> "$output_file"

# Loop through each line of the input file
tail -n +2 "$input_file" | while IFS= read -r line
do
    # Extract folder name (censo_x)
    folder=$(echo "$line" | cut -d ':' -f 1)
    
    # Check if the folder exists and the ts_opt.xyz file is present
    if [[ -d "$folder/ts_opt/spe" && -f "$folder/ts_opt/spe/ts_opt.xyz" ]]; then
        # Read the first two lines and append the comment at the end of the 2nd line
        first_line=$(sed -n '1p' "$folder/ts_opt/spe/ts_opt.xyz")
        second_line=$(sed -n '2p' "$folder/ts_opt/spe/ts_opt.xyz")
        
        # Append the modified first and second line with the comment
        echo "$first_line" >> "$output_file"
        echo "$second_line # From:$folder" >> "$output_file"
        
        # Append the rest of the file (starting from the third line)
        sed -n '3,$p' "$folder/ts_opt/spe/ts_opt.xyz" >> "$output_file"

    else
        echo "Warning: $folder/ts_opt/spe/ts_opt.xyz not found or directory missing!"
    fi

done < "$input_file"

echo "All ts_opt.xyz files have been combined into $output_file."

#create a folder with the results, which can be easily copied to your local machine
mkdir -p results
cp ts_conformers.xyz conformer_energies.txt auto_energies.out results/
