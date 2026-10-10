
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

load_dotenv()


# --------------------------------------------------
# 1. CONNECT TO POSTGRESQL
# --------------------------------------------------

def connect_database():
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing from your .env file."
        )

    return psycopg2.connect(database_url)


# --------------------------------------------------
# 2. CHECK TABLE COLUMNS
# --------------------------------------------------

def get_table_columns(cursor, table_name):
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))

    return [row[0] for row in cursor.fetchall()]


# --------------------------------------------------
# 3. AUTOMATICALLY FIX THE SOURCE COLUMN
# --------------------------------------------------

def ensure_database_schema():
    connection = None
    cursor = None

    try:
        connection = connect_database()
        cursor = connection.cursor()

        cursor.execute("""
            ALTER TABLE medical_records
            ADD COLUMN IF NOT EXISTS source
            TEXT DEFAULT 'Medical Record';
        """)

        connection.commit()
        print("Database schema checked successfully.")

    except Exception as e:
        if connection:
            connection.rollback()

        print(
            f"Database schema error: "
            f"{type(e).__name__}: {e}"
        )
        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# Run the schema check when this module is imported.
ensure_database_schema()


# --------------------------------------------------
# 4. HELPERS FOR DIFFERENT DATABASE COLUMN NAMES
# --------------------------------------------------

def find_column(existing_columns, possible_names):
    for name in possible_names:
        if name in existing_columns:
            return name
    return None


def get_value(data, possible_names, default=None):
    for name in possible_names:
        if name in data and data[name] is not None:
            return data[name]
    return default


def normalize_text(value):
    if value is None:
        return None

    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value)

    return str(value)


# --------------------------------------------------
# 5. INSERT RELATED RECORDS USING ACTUAL COLUMNS
# --------------------------------------------------

def insert_related_records(
    cursor,
    table_name,
    medical_record_id,
    items,
    field_aliases
):
    if not items:
        return

    columns = get_table_columns(cursor, table_name)

    if not columns:
        raise ValueError(
            f"Table '{table_name}' was not found "
            "in the current PostgreSQL schema."
        )

    foreign_key = find_column(
        columns,
        [
            "medical_record_id",
            "record_id",
            "medical_id"
        ]
    )

    if not foreign_key:
        raise ValueError(
            f"No recognized medical-record foreign key "
            f"was found in '{table_name}'. "
            f"Actual columns: {columns}"
        )

    for item in items:
        if not isinstance(item, dict):
            raise ValueError(
                f"Expected each item in '{table_name}' "
                "to be a dictionary."
            )

        insert_data = {
            foreign_key: medical_record_id
        }

        for target_names, source_names in field_aliases:
            target = find_column(columns, target_names)

            if target:
                value = get_value(item, source_names)

                if value is not None:
                    insert_data[target] = value

        if len(insert_data) == 1:
            raise ValueError(
                f"Could not match the data fields to "
                f"the columns in '{table_name}'. "
                f"Actual columns: {columns}"
            )

        query = sql.SQL(
            "INSERT INTO {} ({}) VALUES ({})"
        ).format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(
                sql.Identifier(column)
                for column in insert_data
            ),
            sql.SQL(", ").join(
                sql.Placeholder()
                for _ in insert_data
            )
        )

        cursor.execute(
            query,
            list(insert_data.values())
        )


# --------------------------------------------------
# 6. INSERT A MEDICAL RECORD
# --------------------------------------------------

def insert_medical_record(data):
    connection = None
    cursor = None

    try:
        connection = connect_database()
        cursor = connection.cursor()

        patient_id = data.get("patient_id")
        patient_name = data.get("patient_name")
        record_date = data.get("record_date")
        hospital = data.get("hospital")
        record_type = data.get("record_type")

        # Check for an existing record.
        cursor.execute("""
            SELECT id
            FROM medical_records
            WHERE patient_id IS NOT DISTINCT FROM %s
              AND record_date IS NOT DISTINCT FROM %s
              AND hospital IS NOT DISTINCT FROM %s
              AND record_type IS NOT DISTINCT FROM %s
            LIMIT 1;
        """, (
            patient_id,
            record_date,
            hospital,
            record_type
        ))

        if cursor.fetchone():
            connection.rollback()
            return "duplicate"

        # Save the main record.
        cursor.execute("""
            INSERT INTO medical_records (
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
            RETURNING id;
        """, (
            patient_id,
            patient_name,
            record_date,
            hospital,
            record_type,
            data.get("content"),
            normalize_text(data.get("symptoms")),
            data.get("assessment"),
            data.get("source", "Medical Record")
        ))

        medical_record_id = cursor.fetchone()[0]

        # Save laboratory results.
        insert_related_records(
            cursor,
            "lab_results",
            medical_record_id,
            data.get("lab_results") or [],
            [
                (
                    ["test_name", "name", "test", "parameter",
                     "lab_test", "test_type"],
                    ["test_name", "name", "test", "parameter",
                     "lab_test", "test_type"]
                ),
                (
                    ["test_value", "value", "result",
                     "result_value", "reading"],
                    ["test_value", "value", "result",
                     "result_value", "reading"]
                ),
                (
                    ["unit", "test_unit", "measurement_unit"],
                    ["unit", "test_unit", "measurement_unit"]
                ),
                (
                    ["reference_range", "normal_range",
                     "reference_value", "range"],
                    ["reference_range", "normal_range",
                     "reference_value", "range"]
                )
            ]
        )

        # Save medications.
        insert_related_records(
            cursor,
            "medications",
            medical_record_id,
            data.get("medications") or [],
            [
                (
                    ["medication_name", "name", "medicine_name",
                     "drug_name", "medication"],
                    ["medication_name", "name", "medicine_name",
                     "drug_name", "medication"]
                ),
                (
                    ["dosage", "dose", "strength"],
                    ["dosage", "dose", "strength"]
                ),
                (
                    ["frequency", "intake_frequency"],
                    ["frequency", "intake_frequency"]
                ),
                (
                    ["duration", "treatment_duration"],
                    ["duration", "treatment_duration"]
                )
            ]
        )

        # Save allergies.
        insert_related_records(
            cursor,
            "allergies",
            medical_record_id,
            data.get("allergies") or [],
            [
                (
                    ["allergen", "allergy_name", "name",
                     "allergy"],
                    ["allergen", "allergy_name", "name",
                     "allergy"]
                ),
                (
                    ["reaction", "allergic_reaction"],
                    ["reaction", "allergic_reaction"]
                ),
                (
                    ["severity", "allergy_severity"],
                    ["severity", "allergy_severity"]
                )
            ]
        )

        # Save all related records together.
        connection.commit()

        print(
            f"Medical record {medical_record_id} "
            "saved successfully."
        )

        return True

    except Exception as e:
        if connection:
            connection.rollback()

        print(
            f"Error inserting medical record: "
            f"{type(e).__name__}: {e}"
        )

        return False

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# --------------------------------------------------
# 7. GET ALL MEDICAL RECORDS
# --------------------------------------------------

def get_all_medical_records():
    connection = None
    cursor = None

    try:
        connection = connect_database()
        cursor = connection.cursor(
            cursor_factory=RealDictCursor
        )

        cursor.execute("""
            SELECT
                id,
                patient_id,
                patient_name,
                record_date,
                hospital,
                record_type,
                content,
                symptoms,
                assessment,
                source
            FROM medical_records
            ORDER BY record_date DESC NULLS LAST, id DESC;
        """)

        records = cursor.fetchall()

        for record in records:
            record_id = record["id"]

            for table_name, result_key in [
                ("lab_results", "lab_results"),
                ("medications", "medications"),
                ("allergies", "allergies")
            ]:
                columns = get_table_columns(
                    cursor,
                    table_name
                )

                foreign_key = find_column(
                    columns,
                    [
                        "medical_record_id",
                        "record_id",
                        "medical_id"
                    ]
                )

                if not foreign_key:
                    raise ValueError(
                        f"Cannot find the record ID column "
                        f"in '{table_name}'. "
                        f"Actual columns: {columns}"
                    )

                query = sql.SQL(
                    "SELECT * FROM {} WHERE {} = %s"
                ).format(
                    sql.Identifier(table_name),
                    sql.Identifier(foreign_key)
                )

                cursor.execute(query, (record_id,))
                record[result_key] = cursor.fetchall()

        return records

    except Exception as e:
        print(
            f"Error loading medical records: "
            f"{type(e).__name__}: {e}"
        )
        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# --------------------------------------------------
# 8. DELETE A MEDICAL RECORD
# --------------------------------------------------

def delete_medical_record(record_id):
    connection = None
    cursor = None

    try:
        connection = connect_database()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM medical_records
            WHERE id = %s;
        """, (record_id,))

        deleted = cursor.rowcount > 0

        connection.commit()
        return deleted

    except Exception as e:
        if connection:
            connection.rollback()

        print(
            f"Error deleting medical record: "
            f"{type(e).__name__}: {e}"
        )

        return False

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
