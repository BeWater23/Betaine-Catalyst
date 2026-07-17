
##Author: Lucca Pfitzer 
##Version: 12th August 2024

import numpy as np

# Open the file "auto_energies.out" for ts_major
try:
    with open("ts_major/auto_energies.out", "r") as file:
        # Initialize an empty dictionary to store the extracted data
        data_dict = {}
        
        # Read all lines from the file
        lines = file.readlines()
        
        # Iterate through each line and check if it contains the desired string
        for line in lines:
            if "total free energy G =" in line:
                # Find the position of "=" sign
                equals_index = line.find("=")
                
                # Extract the first word
                first_word = line[:equals_index].strip().split()[0]
                
                # Extract the number after the "=" sign
                number_str = line[equals_index + 1:line.find("H")].strip()
                number = float(number_str)
                
                # Store the data in the dictionary
                data_dict[first_word] = number

        # Sort the dictionary based on values in descending order
        sorted_data = dict(sorted(data_dict.items(), key=lambda item: item[1], reverse=False))
        #print(sorted_data)
        first_value = list(sorted_data.values())[0]  # Get the first value (reference konformer)
        relative_energies = {key: np.round((value - first_value) * 627.5, 2) for key, value in sorted_data.items()}  # Convert to kcal/mol
        print(relative_energies)
 
except FileNotFoundError:
    print("File not found. Please make sure the file exists in the current directory.")
except Exception as e:
    print("An error occurred:", e)

# Open the file "auto_energies.out" for ts_minor
try:
    with open("ts_minor/auto_energies.out", "r") as file:
        # Initialize an empty dictionary to store the extracted data
        data_dict_minor = {}
        
        # Read all lines from the file
        lines = file.readlines()
        
        # Iterate through each line and check if it contains the desired string
        for line in lines:
            if "total free energy G =" in line:
                # Find the position of "=" sign
                equals_index = line.find("=")
                
                # Extract the first word
                first_word = line[:equals_index].strip().split()[0]
                
                # Extract the number after the "=" sign
                number_str = line[equals_index + 1:line.find("H")].strip()
                number = float(number_str)
                
                # Store the data in the dictionary
                data_dict_minor[first_word] = number

        # Sort the dictionary based on values in descending order
        sorted_data_minor = dict(sorted(data_dict_minor.items(), key=lambda item: item[1], reverse=False))
        #print(sorted_data_minor)
        first_value_minor = list(sorted_data_minor.values())[0]  # Get the first value (reference konformer)
        relative_energies_minor = {key: np.round((value - first_value) * 627.5, 2) for key, value in sorted_data_minor.items()}  # Convert to kcal/mol
        print(relative_energies_minor)

except FileNotFoundError:
    print("File not found. Please make sure the file exists in the current directory.")
except Exception as e:
    print("An error occurred:", e)


# 1) Based on single best TSs
print("ee prediction based on single best TSs")

deltaG = (first_value_minor - first_value) * 2625.5  # Convert to kJ/mol
print("ddG =", np.round(deltaG,2), "kJ/mol")
print("ddG =", np.round((first_value_minor - first_value)*627.5, 2), "kcal/mol")

if deltaG > 0:
    print("TS_major is actually TS_major")
else:
    print("TS_minor is actually TS_major")

def ee(dG):
    tof_ratio = np.exp(dG*1000 / (8.314 * 298))
    ee_value = (tof_ratio - 1) / (tof_ratio + 1) * 100
    return ee_value

ee_single = np.round(ee(deltaG), 1)
print("ee_s =", ee_single)
print()


# 2) Based on Boltzmann weighting
print("ee prediction based on Boltzmann weighting")

# Convert energy differences to kJ/mol
ens_major = np.array([(value - first_value) * 2625.5 for value in sorted_data.values()])
ens_minor = np.array([(value - first_value) * 2625.5 for value in sorted_data_minor.values()])
#print(ens_major)
#print(ens_minor)

def boltzmann_weighted_deltaG(ens):
    boltzmann_factors = np.exp(-ens*1000 / (8.314 * 298))
    probabilities = boltzmann_factors / np.sum(boltzmann_factors)
    #print(probabilities)
    return np.sum(probabilities * ens)

deltaG_boltzmann = boltzmann_weighted_deltaG(ens_minor) - boltzmann_weighted_deltaG(ens_major)
print("ddG =", np.round(deltaG_boltzmann, 2), "kJ/mol")
print("ddG =", np.round(deltaG_boltzmann*0.239,2), "kcal/mol")

if deltaG_boltzmann > 0:
    print("TS_major is actually TS_major")
else:
    print("TS_minor is actually TS_major")

ee_boltzmann = np.round(ee(deltaG_boltzmann),1)
print("ee_bz =", ee_boltzmann)
