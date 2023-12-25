import streamlit as st
import pandas as pd
import json

# Function to load the global fee structure dictionary from a JSON file
def load_global_fee_structure():
    try:
        with open('fee_structure.json', 'r') as file:
            fee_structure = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        fee_structure = {}
    return fee_structure

# Function to save the global fee structure dictionary to a JSON file
def save_global_fee_structure(fee_structure):
    with open('fee_structure.json', 'w') as file:
        json.dump(fee_structure, file)

# Function to display and update the fee structure
def display_fee_structure(sheet_name, fee_structure, password):
    st.sidebar.subheader(f'Fee Structure for {sheet_name}')
    if st.text_input('Enter Password:', type='password') == password:
        for scholarship_type in ['scholar', 'non scholar', 'spot', 'ss']:
            fee_key = f'{sheet_name}_{scholarship_type}'
            fee_structure[fee_key] = st.sidebar.number_input(f'Fee for {scholarship_type.capitalize()}:', key=fee_key, value=fee_structure.get(fee_key, 0))
        st.sidebar.button('Save', on_click=save_global_fee_structure, args=(fee_structure,))

# Function to calculate remaining balance
def calculate_remaining_balance(row, fee_structure):
    sheet_name = row['Sheet Name']
    scholarship_type = row['Scholarship Type']
    fee_key = f'{sheet_name}_{scholarship_type.lower()}'

    total_fee = fee_structure.get(fee_key, 0)

    # Split the 'Amount' and 'Dates' columns by ';' and handle the case where they are integers
    amounts_str = str(row['Amount'])
    dates_str = str(row['Dates'])

    amounts = [int(x) for x in amounts_str.split(';')]
    dates = [x.strip() for x in dates_str.split(';')]

    fee_paid = sum(amounts)
    remaining_balance = total_fee - fee_paid

    # Rename the columns to avoid duplicates
    return pd.Series({
        'Calculated Total Fee': total_fee,
        'Calculated Fee Paid': fee_paid,
        'Calculated Remaining Balance': remaining_balance,
        'Calculated Amounts': amounts,
        'Calculated Dates': dates,
        'Calculated Scholarship Type': scholarship_type
    })

# Streamlit app
st.title('Student Management Portal 🔥')

# File uploader for drag-and-drop functionality
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file is not None:
    # Automatically update JSON file with new fee structure
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names
    selected_sheet = st.sidebar.selectbox('Select Sheet', sheet_names)

    fee_structure = load_global_fee_structure()
    display_fee_structure(selected_sheet, fee_structure, "9441142451")

    # Load data with headers starting from row 5
    df = pd.read_excel(excel_file, sheet_name=selected_sheet, header=4)

    if df is not None:
        # Data cleaning - remove leading and trailing whitespaces from all string columns
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        # Convert 'Admn. No.' column to strings (handling both integers and floats)
        df['Admn. No'] = df['Admn. No'].astype(str)

        # Add a new column 'Sheet Name' to the dataframe
        df['Sheet Name'] = selected_sheet

        # Apply the calculate_remaining_balance function to each row
        df = pd.concat([df, df.apply(calculate_remaining_balance, fee_structure=fee_structure, axis=1)], axis=1)

        # Sidebar for searching
        st.sidebar.subheader('Search by Admission Number')
        admission_number = st.sidebar.text_input('Enter Admission Number:').strip()

        # Button to trigger the search
        search_button = st.sidebar.button('Search')

        # Display student details if admission number is provided and the button is pressed
        if admission_number and search_button:
            st.subheader('Student Details')
            student_details = df[df['Admn. No'].str.contains(admission_number, case=False)].reset_index(drop=True)

            if not student_details.empty:
                for _, row in student_details.iterrows():
                    st.write(f"## {row['Student Name as Per SSC']}")
                    st.write(f"**Scholarship Type:** {row['Scholarship Type']}")
                    st.write(f"**Student Mobile:** {row['Student Mobile Number']}")
                    st.write(f"**Total Fee:** Rs {row['Calculated Total Fee']}/-")
                    st.write(f"**Fee Paid:** Rs {row['Calculated Fee Paid']}/-")
                    st.write(f"**Remaining Balance:** Rs {row['Calculated Remaining Balance']}/-")

                    # Display amount paid along with corresponding date
                    amounts_dates_str = ", ".join([f"Rs {amount}/- on {date}" for amount, date in zip(row['Calculated Amounts'], row['Calculated Dates']) if amount > 0])
                    st.write(f"**Amounts and Dates:** {amounts_dates_str}")

                    st.write("---")
            else:
                st.warning(f"No student found with Admission Number: {admission_number}")

        # Display raw data
        st.subheader('Raw Data')
        st.write(df)
hide_streamlit_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
