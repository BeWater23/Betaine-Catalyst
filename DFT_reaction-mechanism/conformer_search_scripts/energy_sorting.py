##Author: Lucca Pfitzer 
##Version: 07th April 2024

# Open the file "auto_energies.out"
try:
    with open("auto_energies.out", "r") as file:
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
        
        #print(data_dict)

        # Sort the dictionary based on values in descending order
        sorted_data = dict(sorted(data_dict.items(), key=lambda item: item[1], reverse=False))
        
        # Print the sorted dictionary
        #print("Sorted energies (from lowest to highest):", sorted_data)

        # Subtract the first value from all values and multiply by 627.5
        first_value = list(sorted_data.values())[0]  # Get the first value (reference konformer)
        modified_data = {key: ((value - first_value) * 627.5, "kcal/mol") for key, value in sorted_data.items()}

        print("Relative energies:")
        for key, value in modified_data.items():
            print(f"{key}: {value[0]:.2f} {value[1]}")
 
except FileNotFoundError:
    print("File not found. Please make sure the file exists in the current directory.")
except Exception as e:
    print("An error occurred:", e)
