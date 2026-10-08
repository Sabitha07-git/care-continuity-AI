import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def connect_database():
    connection = psycopg2.connect(DATABASE_URL)
    return connection


def insert_medical_record(data):

    connection = connect_database()
    cursor = connection.cursor()

    try:
        # Insert the main medical record
        cursor.execute(
            """
            INSERT INTO medical_records
            (
                patient_id,
                patient_name,
                record_date,
                hospital,
                record_type,
                content,
                symptoms,
                assessment
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (patient_id, record_date, hospital, record_type)
            DO NOTHING
            RETURNING id;
            """,
            (
                data.get("patient_id"),
                data.get("patient_name"),
                data.get("record_date"),
                data.get("hospital"),
                data.get("record_type"),
                data.get("content", ""),
                ", ".join(data.get("symptoms", [])),
                data.get("assessment", "")
            )
        )

        result = cursor.fetchone()

        # Duplicate record
        if result is None:
            connection.rollback()
            print("Duplicate record detected. Skipping insertion.")
            return False

        medical_record_id = result[0]

        # Insert laboratory results
        for lab in data.get("lab_results", []):
            cursor.execute(
                """
                INSERT INTO lab_results
                (
                    medical_record_id,
                    lab_name,
                    value,
                    unit
                )
                VALUES (%s, %s, %s, %s);
                """,
                (
                    medical_record_id,
                    lab.get("lab_name"),
                    lab.get("value"),
                    lab.get("unit")
                )
            )

        # Insert medications
        for medication in data.get("medications", []):
            cursor.execute(
                """
                INSERT INTO medications
                (
                    medical_record_id,
                    medication_name
                )
                VALUES (%s, %s);
                """,
                (
                    medical_record_id,
                    medication
                )
            )

        # Insert allergies
        for allergy in data.get("allergies", []):
            cursor.execute(
                """
                INSERT INTO allergies
                (
                    medical_record_id,
                    allergy_name
                )
                VALUES (%s, %s);
                """,
                (
                    medical_record_id,
                    allergy
                )
            )

        connection.commit()

        print("Medical record and structured information inserted successfully!")

        return True

    except Exception as e:
        connection.rollback()
        print("Database error:", e)
        return False

    finally:
        cursor.close()
        connection.close()

