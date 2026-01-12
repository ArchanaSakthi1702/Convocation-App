import json

# Define the class IDs
CLASS_ID_1 = "09931c0c-4734-40a4-9f3e-336bd8b698f0"
CLASS_ID_2 = "31f6bf61-5ca7-4552-b791-25226724d1cb"

def update_student_ids(file_path):
    try:
        # Load the existing data
        with open(file_path, 'r') as f:
            data = json.load(f)

        for student in data['students']:
            # Extract digits from roll number (e.g., '21UL01' -> 1)
            roll_str = student['roll_number']
            roll_num = int(''.join(filter(str.isdigit, roll_str[2:])))

            # Logic for first range: 01-21 and 22-47
            if 1 <= roll_num <= 47:
                student['class_id'] = CLASS_ID_1
            
            # Logic for second range: 51-70 and 72-95
            elif 51 <= roll_num <= 70 or 72 <= roll_num <= 95:
                student['class_id'] = CLASS_ID_2

        # Save the updated data back to the file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Successfully updated {file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the update
update_student_ids('new.json')