# MediLink_UI.py
from datetime import datetime
import os, sys

# Set up paths using core utilities
from MediCafe.core_utils import setup_module_paths
setup_module_paths(__file__)

from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config
MediLink_ConfigLoader = get_shared_config_loader()
import MediLink_DataMgmt
import MediLink_PatientProcessor
import MediLink_Display_Utils

def display_welcome():
    print("\n" + "-" * 60)
    print("          *~^~*:    Welcome to MediLink!    :*~^~*")
    print("-" * 60)

def display_menu(options):
    print("Menu Options:")
    for i, option in enumerate(options):
        print("{0}. {1}".format(i+1, option))

def get_user_choice():
    return input("Enter your choice: ").strip()

def display_exit_message():
    print("\nExiting MediLink.")

def display_invalid_choice():
    print("Invalid choice. Please select a valid option.")

def display_patient_options(detailed_patient_data):
    """
    Displays a list of patients with their current suggested endpoints, prompting for selections to adjust.
    """
    print("\nPlease select the patients to adjust by entering their numbers separated by commas\n(e.g., 1,3,5):")
    # Can disable this extra print for now because the px list would already be on-screen.
    #for i, data in enumerate(detailed_patient_data, start=1):
    #    patient_info = "{0} ({1}) - {2}".format(data['patient_name'], data['patient_id'], data['surgery_date'])
    #    endpoint = data.get('suggested_endpoint', 'N/A')
    #    print("{:<3}. {:<30} Current Endpoint: {}".format(i, patient_info, endpoint))

def get_selected_indices(patient_count):
    """
    Collects user input for selected indices to adjust endpoints.
    """
    selected_indices_input = input("> ")
    selected_indices = [int(index.strip()) - 1 for index in selected_indices_input.split(',') if index.strip().isdigit() and 0 <= int(index.strip()) - 1 < patient_count]
    return selected_indices

def display_patient_for_adjustment(patient_name, suggested_endpoint):
    """
    Displays the current endpoint for a selected patient and prompts for a change.
    """
    print("\n- {0} | Current Endpoint: {1}".format(patient_name, suggested_endpoint))

def get_endpoint_decision():
    """
    Asks the user if they want to change the endpoint.
    Ensures a valid entry of 'Y' or 'N'.
    """
    while True:
        decision = input("Change endpoint? (Y/N): ").strip().lower()
        if decision in ['y', 'n']:
            return decision
        else:
            print("Invalid input. Please enter 'Y' for Yes or 'N' for No.")

def display_endpoint_options(endpoints_config):
    """
    Displays the endpoint options to the user based on the provided mapping.

    Args:
        endpoints_config (dict): A dictionary mapping endpoint keys to their properties, 
                                 where each property includes a 'name' key for the user-friendly name.
                                 Example: {'Availity': {'name': 'Availity'}, 'OptumEDI': {'name': 'OptumEDI'}, ...}

    Returns:
        None
    """
    print("Select the new endpoint for the patient:")
    for index, (key, details) in enumerate(endpoints_config.items(), 1):
        print("{0}. {1}".format(index, details['name']))

def get_new_endpoint_choice():
    """
    Gets the user's choice for a new endpoint.
    Single selection only.
    """
    while True:
        choice = input("Select desired endpoint (e.g. 1): ").strip()
        corrected_choice = choice.replace(' ', '')
        if corrected_choice.isdigit():
            return int(corrected_choice)
        else:
            print("Invalid input. Please enter a single number corresponding to the endpoint.")

# Display functions moved to MediLink_Display_Utils.py to eliminate circular dependencies

def user_select_files(file_list):
    # Sort files by creation time in descending order
    file_list = sorted(file_list, key=os.path.getctime, reverse=True)[:10]  # Limit to max 10 files
    
    print("\nSelect the Z-form files to submit from the following list:\n")

    formatted_files = []
    for i, file in enumerate(file_list):
        basename = os.path.basename(file)
        parts = basename.split('_')
        
        # Try to parse the timestamp from the filename
        if len(parts) > 2:
            try:
                timestamp_str = parts[1] + parts[2].split('.')[0]
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                formatted_date = timestamp.strftime('%m/%d %I:%M %p')  # Changed to 12HR format with AM/PM
            except ValueError:
                formatted_date = basename  # Fallback to original filename if parsing fails
        else:
            formatted_date = basename  # Fallback to original filename if no timestamp
        
        formatted_files.append((formatted_date, file))
        print("{}: {}".format(i + 1, formatted_date))
    
    selected_indices = input("\nEnter the numbers of the files to process, separated by commas\n(or press Enter to select all): ")
    if not selected_indices:
        return [file for _, file in formatted_files]
    
    selected_indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
    selected_files = [formatted_files[i][1] for i in selected_indices]
    
    return selected_files


def user_decision_on_suggestions(detailed_patient_data, config, insurance_edited, crosswalk):
    """
    Presents the user with all patient summaries and suggested endpoints,
    then asks for confirmation to proceed with all or specify adjustments manually.
    
    FIXED: Display now properly shows effective endpoints (user preferences over original suggestions)
    """
    if insurance_edited:
        # Display summaries only if insurance types were edited
        MediLink_Display_Utils.display_patient_summaries(detailed_patient_data)

    while True:
        proceed_input = input("Do you want to proceed with all suggested endpoints? (Y/N): ").strip().lower()
        if proceed_input in ['y', 'yes']:
            proceed = True
            break
        elif proceed_input in ['n', 'no']:
            proceed = False
            break
        else:
            print("Invalid input. Please enter 'Y' for yes or 'N' for no.")

    # If the user agrees to proceed with all suggested endpoints, confirm them.
    if proceed:
        return MediLink_DataMgmt.confirm_all_suggested_endpoints(detailed_patient_data), crosswalk
    # Otherwise, allow the user to adjust the endpoints manually.
    else:
        return select_and_adjust_files(detailed_patient_data, config, crosswalk)
   

def select_and_adjust_files(detailed_patient_data, config, crosswalk):
    """
    Allows users to select patients and adjust their endpoints by interfacing with UI functions.
    
    FIXED: Now properly updates suggested_endpoint and persists user preferences to crosswalk.
    """
    # Display options for patients
    display_patient_options(detailed_patient_data)

    # Get user-selected indices for adjustment
    selected_indices = get_selected_indices(len(detailed_patient_data))
    
    # Get an ordered list of endpoint keys
    medi = extract_medilink_config(config)
    endpoint_keys = list(medi.get('endpoints', {}).keys())
    
    # Iterate over each selected index and process endpoint changes
    for i in selected_indices:
        data = detailed_patient_data[i]
        current_effective_endpoint = MediLink_PatientProcessor.get_effective_endpoint(data)
        display_patient_for_adjustment(data['patient_name'], current_effective_endpoint)
        
        endpoint_change = get_endpoint_decision()
        if endpoint_change == 'y':
            display_endpoint_options(medi.get('endpoints', {}))
            endpoint_index = get_new_endpoint_choice() - 1  # Adjusting for zero-based index
            
            if 0 <= endpoint_index < len(endpoint_keys):
                selected_endpoint_key = endpoint_keys[endpoint_index]
                print("Endpoint changed to {0} for patient {1}.".format(medi.get('endpoints', {}).get(selected_endpoint_key, {}).get('name', selected_endpoint_key), data['patient_name']))
                
                # Use the new endpoint management system
                updated_crosswalk = MediLink_DataMgmt.update_suggested_endpoint_with_user_preference(
                    detailed_patient_data, i, selected_endpoint_key, config, crosswalk
                )
                if updated_crosswalk:
                    crosswalk = updated_crosswalk
                # STRATEGIC NOTE (Medicare Crossover UI): High-risk implementation requiring strategic decisions
                # 
                # CRITICAL QUESTIONS FOR IMPLEMENTATION:
                # 1. **Crossover Detection**: How to detect Medicare crossover failures?
                #    - Automatic from claim status API responses?
                #    - Manual user indication?
                #    - Time-based detection (no crossover after X days)?
                # 
                # 2. **Secondary Claim Workflow**: How should secondary claim creation be integrated?
                #    - Automatic prompt when crossover failure detected?
                #    - Manual option in patient management interface?
                #    - Batch processing for multiple failed crossovers?
                # 
                # 3. **Data Requirements**: What data is needed for secondary claims?
                #    - Medicare payment amount (required vs optional)?
                #    - Denial/adjustment reasons from Medicare?
                #    - Secondary payer eligibility verification?
                #
                # To implement: Add crossover failure detection and secondary claim creation UI
                # with proper validation and error handling for Medicare -> Secondary workflow
            else:
                print("Invalid selection. Keeping the current endpoint.")
                data['confirmed_endpoint'] = current_effective_endpoint
        else:
            data['confirmed_endpoint'] = current_effective_endpoint

    return detailed_patient_data, crosswalk