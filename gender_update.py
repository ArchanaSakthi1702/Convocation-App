import json
import os

# Path to your file
file_path = r'F:\\Convocation\\consolidated_student_records.json'

def update_genders():
    # 1. Load the data
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    students = data.get('students', [])
    
    print("--- Gender Update Tool ---")
    print("Instructions: Enter 0 for Male, 1 for Female. Press Enter to skip.")
    print("-" * 30)

    try:
        for student in students:
            # Skip if gender is already set (optional - remove if you want to re-check all)
            if student['gender'] not in ['Unknown', '']:
                continue

            print(f"\nStudent: {student['name']} (Roll: {student['roll_number']})")
            choice = input("Gender (0:Male / 1:Female / skip:Enter): ").strip()

            if choice == '0':
                student['gender'] = 'Male'
                print("Updated to Male")
            elif choice == '1':
                student['gender'] = 'Female'
                print("Updated to Female")
            else:
                print("Skipped")

    except KeyboardInterrupt:
        print("\n\nProcess interrupted. Saving progress...")

    # 2. Save the updated data
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print("\nFile saved successfully.")

if __name__ == "__main__":
    update_genders()