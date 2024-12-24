import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO
import hashlib

# Database setup
conn = sqlite3.connect("employee_reports.db")
c = conn.cursor()

# Create table for storing reports if not exists
c.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT,
    employee_name TEXT,
    rag_status TEXT,
    comment TEXT,
    timestamp TEXT
)
''')
conn.commit()

# Simple users database (replace with a database for production)
# This dictionary holds usernames and their hashed passwords.
users_db = {
    "user1": hashlib.sha256("password1".encode()).hexdigest(),
    "user2": hashlib.sha256("password2".encode()).hexdigest(),
    "lingesh": hashlib.sha256("1234".encode()).hexdigest(),
    "siva": hashlib.sha256("1234".encode()).hexdigest(),
    "admin": hashlib.sha256("adminpass".encode()).hexdigest()
}

# Hash a password (this is used to compare the user input password to the stored hash)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Check if user credentials are valid
def check_credentials(username, password):
    hashed_password = hash_password(password)
    if username in users_db and users_db[username] == hashed_password:
        return True
    return False

# Login page UI
def login_page():
    st.title("Login to Employee Status Management System")
    username = st.text_input("Username", "")
    password = st.text_input("Password", "", type="password")

    if st.button("Login"):
        if username and password:
            if check_credentials(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome {username}!")
                return True
            else:
                st.error("Invalid username or password")
        else:
            st.error("Please enter both username and password")

    return False

# Streamlit UI for Employee Status Management
def employee_status_management():
    st.title("Employee Status Management")

    # Option for uploading employee data (Excel file)
    st.header("Upload Employee Data (Excel)")

    # File uploader for Excel files
    uploaded_file = st.file_uploader("Upload your employee data Excel file", type=["xlsx"])

    # Check if a file has been uploaded
    if uploaded_file is not None:
        # Read the uploaded Excel file into a DataFrame
        try:
            employee_data = pd.read_excel(uploaded_file)

            # Hide the uploaded data preview
            st.success("File uploaded successfully!")

            # Search section
            search_query = st.text_input("Search by employee name or ID")

            # Filter employees based on search query (by name or ID)
            filtered_df = employee_data[
                employee_data['Employee Name'].str.contains(search_query, case=False, na=False) |
                employee_data['Employee ID'].astype(str).str.contains(search_query)
            ]

            # Show warning if no employee is found
            if filtered_df.empty:
                st.warning("No employee found with that name or ID.")
            else:
                # RAG status selection
                rag_status = st.selectbox("Select RAG Status", ['Red', 'Amber', 'Green'])

                # Comment input
                comment = st.text_area("Enter Your Comment:")

                # Email trigger function (simulated)
                def send_email(recipients, subject, body):
                    st.write(f"Sending email to: {', '.join(recipients)}")
                    st.write(f"Subject: {subject}")
                    st.write(f"Body: {body}")
                    st.success("Emails have been simulated.")

                # Submit button for RAG status update and comments
                if st.button("Submit"):
                    if comment:
                        selected_employee = filtered_df.iloc[0]  # Get the first matching employee
                        
                        # Save the report to the database
                        c.execute('''
                        INSERT INTO reports (employee_id, employee_name, rag_status, comment, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (
                            selected_employee['Employee ID'],
                            selected_employee['Employee Name'],
                            rag_status,
                            comment,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                        conn.commit()

                        # Prepare the email subject and body
                        subject = f"Immediate Attention Required for {selected_employee['Employee Name']}"
                        body = f"Dear all,\n\nThe RAG status for {selected_employee['Employee Name']} has been marked as {rag_status}. Please review the comments and take necessary actions.\n\nComment: {comment}"

                        # If RAG status is 'Red', trigger emails
                        if rag_status == 'Red':
                            # List of recipients for RAG Red status
                            manager_mail = f"{selected_employee['Reporting Manager'].lower().replace(' ', '.')}@company.com"  # Simulating manager's email
                            hr_mail = "hr@company.com"  # Placeholder HR email
                            hr_manager_mail = "hrmanager@company.com"  # Placeholder HR manager email
                            hr_head_mail = "hrhead@company.com"  # Placeholder HR head email

                            # Send email to relevant parties based on RAG status
                            send_email(
                                recipients=[manager_mail, hr_mail, hr_manager_mail, hr_head_mail],  # For manager and HR team
                                subject=subject,
                                body=body
                            )
                            # Also notify the employee directly
                            send_email(
                                recipients=[selected_employee['Mail ID']],  # To the employee
                                subject=subject,
                                body=body
                            )
                        st.success("Report submitted successfully and stored in the database!")
                    else:
                        st.error("Please enter a comment before submitting.")

            # Generate report button
            if st.button("Generate Report"):
                st.info("Generating report...")

                # Option to choose which data to export: All or Filtered
                data_to_export = filtered_df if not filtered_df.empty else employee_data

                # Create CSV
                csv = data_to_export.to_csv(index=False)

                # Provide a download button to the user
                st.download_button(
                    label="Download Employee Data as CSV",
                    data=csv,
                    file_name="employee_report.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error reading the Excel file: {e}")

    # Option to download the database as an Excel file
    st.header("Download Database")
    if st.button("Export Database as Excel"):
        # Query data from the database
        query = "SELECT * FROM reports"
        reports_df = pd.read_sql_query(query, conn)

        # Save to an Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            reports_df.to_excel(writer, index=False, sheet_name='Reports')
        output.seek(0)

        # Provide download option
        st.download_button(
            label="Download Database as Excel",
            data=output,
            file_name="employee_reports.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""  # Clear username
        st.success("You have logged out successfully!")
        # Re-run the app to go back to the login page
        st.rerun()  # This replaces `st.experimental_rerun()`

# Main function
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Check if the user is logged in
    if st.session_state.logged_in:
        employee_status_management()  # Show the employee status management after login
    else:
        # If not logged in, show the login page
        if login_page():
            # After successful login, the employee status management page should be shown
            employee_status_management()

if __name__ == "__main__":
    main()
