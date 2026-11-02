
import heapq
from datetime import datetime
from connection import conn, cursor


# Emergency Priority Queue
emergency_queue = []


# ---------------- COMMON FUNCTIONS ----------------

def get_int(message, minimum=None, maximum=None):
    while True:
        try:
            value = int(input(message))

            if minimum is not None and value < minimum:
                print(f"Value must be at least {minimum}.")
                continue

            if maximum is not None and value > maximum:
                print(f"Value must not be greater than {maximum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def record_exists(table, column, value):
    # Used only with fixed table and column names in this program.
    cursor.execute(
        f"SELECT 1 FROM {table} WHERE {column} = %s",
        (value,)
    )
    return cursor.fetchone() is not None


def show_records(records):
    if not records:
        print("\nNo records found.")
        return

    for record in records:
        print("-" * 60)
        for value in record:
            print(value)


# ---------------- PATIENT MANAGEMENT ----------------

def add_patient():
    print("\n--- Add Patient ---")

    name = input("Enter patient name: ").strip()

    if not name:
        print("Patient name cannot be empty.")
        return

    age = get_int("Enter age: ", 1, 120)
    gender = input("Enter gender: ").strip()
    contact = input("Enter contact number: ").strip()
    medical_info = input("Enter medical information: ").strip()

    cursor.execute("""
        INSERT INTO Patient
        (name, age, gender, contact, medical_info)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, age, gender, contact, medical_info))

    conn.commit()
    print("Patient added successfully!")
    print("Patient ID:", cursor.lastrowid)


def view_patients():
    cursor.execute("""
        SELECT patient_id, name, age, gender, contact, medical_info
        FROM Patient
    """)
    show_records(cursor.fetchall())


def search_patient():
    patient_id = get_int("Enter Patient ID: ", 1)

    cursor.execute("""
        SELECT * FROM Patient
        WHERE patient_id = %s
    """, (patient_id,))

    show_records(cursor.fetchall())


def update_patient_contact():
    patient_id = get_int("Enter Patient ID: ", 1)
    contact = input("Enter new contact number: ").strip()

    cursor.execute("""
        UPDATE Patient
        SET contact = %s
        WHERE patient_id = %s
    """, (contact, patient_id))

    conn.commit()

    if cursor.rowcount > 0:
        print("Patient contact updated successfully!")
    else:
        print("Patient not found.")


def delete_patient():
    patient_id = get_int("Enter Patient ID: ", 1)

    try:
        cursor.execute("""
            DELETE FROM Patient
            WHERE patient_id = %s
        """, (patient_id,))

        conn.commit()

        if cursor.rowcount > 0:
            print("Patient deleted successfully!")
        else:
            print("Patient not found.")

    except Exception as e:
        conn.rollback()
        print("Patient cannot be deleted because related records may exist.")
        print("Details:", e)


# ---------------- DOCTOR MANAGEMENT ----------------

def add_doctor():
    print("\n--- Add Doctor ---")

    name = input("Enter doctor name: ").strip()

    if not name:
        print("Doctor name cannot be empty.")
        return

    specialization = input("Enter specialization: ").strip()
    availability = input("Enter availability: ").strip()

    cursor.execute("""
        INSERT INTO Doctor
        (name, specialization, availability)
        VALUES (%s, %s, %s)
    """, (name, specialization, availability))

    conn.commit()

    print("Doctor added successfully!")
    print("Doctor ID:", cursor.lastrowid)


def view_doctors():
    cursor.execute("""
        SELECT * FROM Doctor
    """)
    show_records(cursor.fetchall())


def search_doctor():
    specialization = input("Enter specialization: ").strip()

    cursor.execute("""
        SELECT * FROM Doctor
        WHERE specialization LIKE %s
    """, ("%" + specialization + "%",))

    show_records(cursor.fetchall())


def update_doctor_availability():
    doctor_id = get_int("Enter Doctor ID: ", 1)
    availability = input("Enter new availability: ").strip()

    cursor.execute("""
        UPDATE Doctor
        SET availability = %s
        WHERE doctor_id = %s
    """, (availability, doctor_id))

    conn.commit()

    if cursor.rowcount > 0:
        print("Doctor availability updated successfully!")
    else:
        print("Doctor not found.")


# ---------------- APPOINTMENT MANAGEMENT ----------------

def doctor_is_available(doctor_id, appointment_date, appointment_time):
    cursor.execute("""
        SELECT COUNT(*)
        FROM Appointment
        WHERE doctor_id = %s
        AND `date` = %s
        AND `time` = %s
        AND status = 'Booked'
    """, (doctor_id, appointment_date, appointment_time))

    return cursor.fetchone()[0] == 0


def book_appointment():
    print("\n--- Book Appointment ---")

    patient_id = get_int("Enter Patient ID: ", 1)
    doctor_id = get_int("Enter Doctor ID: ", 1)

    if not record_exists("Patient", "patient_id", patient_id):
        print("Patient does not exist!")
        return

    if not record_exists("Doctor", "doctor_id", doctor_id):
        print("Doctor does not exist!")
        return

    try:
        appointment_date = datetime.strptime(
            input("Enter date (YYYY-MM-DD): ").strip(),
            "%Y-%m-%d"
        ).date()

        appointment_time = datetime.strptime(
            input("Enter time (HH:MM): ").strip(),
            "%H:%M"
        ).time()

    except ValueError:
        print("Invalid date or time format.")
        return

    if not doctor_is_available(
        doctor_id, appointment_date, appointment_time
    ):
        print("Doctor already has an appointment at this time!")
        return

    cursor.execute("""
        INSERT INTO Appointment
        (patient_id, doctor_id, `date`, `time`, status)
        VALUES (%s, %s, %s, %s, 'Booked')
    """, (
        patient_id,
        doctor_id,
        appointment_date,
        appointment_time
    ))

    conn.commit()

    print("Appointment booked successfully!")
    print("Appointment ID:", cursor.lastrowid)


def view_appointments():
    cursor.execute("""
        SELECT
            appointment_id,
            patient_id,
            doctor_id,
            `date`,
            `time`,
            status
        FROM Appointment
        ORDER BY appointment_id
    """)

    show_records(cursor.fetchall())


def cancel_appointment():
    appointment_id = get_int("Enter Appointment ID: ", 1)

    cursor.execute("""
        UPDATE Appointment
        SET status = 'Cancelled'
        WHERE appointment_id = %s
        AND status = 'Booked'
    """, (appointment_id,))

    conn.commit()

    if cursor.rowcount > 0:
        print("Appointment cancelled successfully!")
    else:
        print("Appointment not found or already cancelled.")


# ---------------- EMERGENCY MANAGEMENT ----------------

def load_emergency_queue():
    """Load waiting emergency cases from MySQL into heapq."""

    emergency_queue.clear()

    cursor.execute("""
        SELECT emergency_id, patient_id, `condition`, priority
        FROM Emergency
        WHERE status = 'Waiting'
        ORDER BY priority, emergency_id
    """)

    records = cursor.fetchall()

    for record in records:
        emergency_id, patient_id, condition, priority = record

        heapq.heappush(
            emergency_queue,
            (priority, emergency_id, patient_id, condition)
        )


def add_emergency():
    print("\n--- Add Emergency Case ---")

    patient_id = get_int("Enter Patient ID: ", 1)

    if not record_exists("Patient", "patient_id", patient_id):
        print("Patient does not exist!")
        return

    condition = input("Enter emergency condition: ").strip()

    if not condition:
        print("Emergency condition cannot be empty.")
        return

    priority = get_int("Enter priority (1-4): ", 1, 4)

    cursor.execute("""
        INSERT INTO Emergency
        (patient_id, `condition`, priority, status)
        VALUES (%s, %s, %s, 'Waiting')
    """, (patient_id, condition, priority))

    conn.commit()

    print("Emergency case added successfully!")
    print("Emergency ID:", cursor.lastrowid)

    load_emergency_queue()


def view_emergencies():
    cursor.execute("""
        SELECT
            e.emergency_id,
            p.name,
            e.`condition`,
            e.priority,
            e.status
        FROM Emergency e
        JOIN Patient p
        ON e.patient_id = p.patient_id
        ORDER BY e.priority ASC, e.emergency_id ASC
    """)

    show_records(cursor.fetchall())


def process_next_emergency():
    load_emergency_queue()

    if not emergency_queue:
        print("No emergency cases waiting.")
        return

    priority, emergency_id, patient_id, condition = heapq.heappop(
        emergency_queue
    )

    cursor.execute("""
        UPDATE Emergency
        SET status = 'Processed'
        WHERE emergency_id = %s
        AND status = 'Waiting'
    """, (emergency_id,))

    conn.commit()

    if cursor.rowcount > 0:
        print("\n--- Processing Emergency Case ---")
        print("Emergency ID:", emergency_id)
        print("Patient ID:", patient_id)
        print("Condition:", condition)
        print("Priority:", priority)
        print("Status: Processed")
    else:
        print("Emergency case could not be processed.")

    load_emergency_queue()


# ---------------- SUMMARY REPORT ----------------

def summary_report():
    print("\n--- Hospital Summary Report ---")

    tables = ["Patient", "Doctor", "Appointment", "Emergency"]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Total {table} Records: {count}")


# ---------------- SUBMENUS ----------------

def patient_menu():
    while True:
        print("""
====== PATIENT MANAGEMENT ======
1. Add Patient
2. View Patients
3. Search Patient
4. Update Patient Contact
5. Delete Patient
6. Back to Main Menu
""")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_patient()
        elif choice == "2":
            view_patients()
        elif choice == "3":
            search_patient()
        elif choice == "4":
            update_patient_contact()
        elif choice == "5":
            delete_patient()
        elif choice == "6":
            break
        else:
            print("Invalid choice!")


def doctor_menu():
    while True:
        print("""
====== DOCTOR MANAGEMENT ======
1. Add Doctor
2. View Doctors
3. Search Doctor
4. Update Doctor Availability
5. Back to Main Menu
""")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_doctor()
        elif choice == "2":
            view_doctors()
        elif choice == "3":
            search_doctor()
        elif choice == "4":
            update_doctor_availability()
        elif choice == "5":
            break
        else:
            print("Invalid choice!")


def appointment_menu():
    while True:
        print("""
====== APPOINTMENT MANAGEMENT ======
1. Book Appointment
2. View Appointments
3. Cancel Appointment
4. Back to Main Menu
""")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            book_appointment()
        elif choice == "2":
            view_appointments()
        elif choice == "3":
            cancel_appointment()
        elif choice == "4":
            break
        else:
            print("Invalid choice!")


def emergency_menu():
    while True:
        print("""
====== EMERGENCY MANAGEMENT ======
1. Add Emergency Case
2. View Emergency Cases
3. Process Next Emergency
4. Back to Main Menu
""")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_emergency()
        elif choice == "2":
            view_emergencies()
        elif choice == "3":
            process_next_emergency()
        elif choice == "4":
            break
        else:
            print("Invalid choice!")


# ---------------- MAIN MENU ----------------

def main():
    print("\n================================")
    print("     HOSPITAL MANAGEMENT SYSTEM")
    print("================================")
    print("Database connected successfully!")

    # Load previously saved waiting emergency cases.
    load_emergency_queue()

    while True:
        print("""
========== MAIN MENU ==========
1. Patient Management
2. Doctor Management
3. Appointment Management
4. Emergency Management
5. Summary Report
6. Exit
""")

        choice = input("Enter your choice: ").strip()

        try:
            if choice == "1":
                patient_menu()

            elif choice == "2":
                doctor_menu()

            elif choice == "3":
                appointment_menu()

            elif choice == "4":
                emergency_menu()

            elif choice == "5":
                summary_report()

            elif choice == "6":
                print("Thank you for using Hospital Management System!")
                break

            else:
                print("Invalid choice! Please try again.")

        except Exception as e:
            conn.rollback()
            print("\nOperation could not be completed.")
            print("Error:", e)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")

    except Exception as e:
        print("\nApplication error:", e)

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()
