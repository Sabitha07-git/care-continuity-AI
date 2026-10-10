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
                assessment,
                source
                 
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
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
                data.get("assessment", ""),
                data.get("source", "") 
            )
        )

        result = cursor.fetchone()

        # Duplicate record
        if result is None:
            connection.rollback()
            print("Duplicate record detected. Skipping insertion.")
            return "duplicate" 

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


def get_all_medical_records():

    connection = connect_database()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                patient_id,
                patient_name,
                record_date,
                hospital,
                record_type,
                symptoms,
                assessment,
                source
            FROM medical_records
            ORDER BY record_date ASC;
        """)

        medical_records = cursor.fetchall()
        records = []

        for row in medical_records:

            medical_record_id = row[0]

            cursor.execute(
                """
                SELECT lab_name, value, unit
                FROM lab_results
                WHERE medical_record_id = %s;
                """,
                (medical_record_id,)
            )

            labs = [
                {
                    "lab_name": lab[0],
                    "value": lab[1],
                    "unit": lab[2]
                }
                for lab in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT medication_name
                FROM medications
                WHERE medical_record_id = %s;
                """,
                (medical_record_id,)
            )

            medications = [
                medication[0]
                for medication in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT allergy_name
                FROM allergies
                WHERE medical_record_id = %s;
                """,
                (medical_record_id,)
            )

            allergies = [
                allergy[0]
                for allergy in cursor.fetchall()
            ]

            records.append({
                "id": row[0],
                "patient_id": row[1],
                "patient_name": row[2], 
                "source": row[8] or "Medical Record",
                "record_date": str(row[3]) if row[3] else "",
                "hospital": row[4],
                "record_type": row[5],
                "symptoms": row[6].split(", ") if row[6] else [],
                "assessment": row[7],
                "labs": labs,
                "medications": medications,
                "allergies": allergies
            })

        return records

    finally:
        cursor.close()
        connection.close()



def delete_medical_record(record_id):
    connection = connect_database()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM medical_records WHERE id = %s RETURNING id;",
            (record_id,)
        )

        deleted = cursor.fetchone()

        if deleted is None:
            connection.rollback()
            return False

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Delete error:", e)
        return False

    finally:
        cursor.close()
        connection.close()
