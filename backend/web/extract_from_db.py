import mysql.connector
import os

# Function to fetch student details from the 'users' table
def fetch_student_details(db_config):
    try:
        print("Connecting to the database...")  # Debugging output
        # Connect to the database
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )

        cursor = connection.cursor(dictionary=True)
        
        # Execute query to fetch student details (assuming you have a table named 'users')
        print("Executing query to fetch student data...")  # Debugging output
        cursor.execute("SELECT * FROM users WHERE role = 'student';")
        
        # Fetch all rows from the result
        students = cursor.fetchall()
        
        print(f"Found {len(students)} student records.")  # Debugging output
        return students

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Function to write the student details to a .sql file
def write_to_sql_file(students, file_path):
    try:
        if not students:
            print("No student data to write to file.")  # Debugging output
            return
        
        print(f"Writing {len(students)} student records to {file_path}...")  # Debugging output
        with open(file_path, 'w') as file:
            # Write the header for the SQL file (to create a table or for INSERTs)
            file.write("USE your_database_name;\n\n")  # Specify your DB name here
            file.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")  # Disable foreign key checks if necessary

            # Iterate over students and generate INSERT statements
            for student in students:
                # Modify the query to match the table structure and column names of your 'users' table
                columns = ', '.join(student.keys())
                values = ', '.join(f"'{v}'" for v in student.values())
                
                # Write the SQL INSERT statement
                insert_query = f"INSERT INTO users ({columns}) VALUES ({values});\n"
                file.write(insert_query)

            # Optionally, re-enable foreign key checks if you disabled them
            file.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
            
            print(f"Student details successfully written to {file_path}")  # Debugging output

    except Exception as e:
        print(f"Error writing to file: {e}")

# Main function to execute the entire process
def main():
    db_config = {
        # 'host': 'localhost:3306l',        # E.g., 'localhost' or IP address of the server
        'host': '192.168.1.32',        # E.g., 'localhost' or IP address of the server
        'user': 'root',        # Your database username
        'password': '',  # Your database password
        'database': 'dunis_attendance_system_db'     # The name of your database
    }

    # Fetch student details from the database
    students = fetch_student_details(db_config)

    if students:
        # Specify the path where you want to save the .sql file
        output_file = 'student_details.sql'
        write_to_sql_file(students, output_file)
    else:
        print("No student details found or there was an error fetching data.")

if __name__ == "__main__":
    main()
