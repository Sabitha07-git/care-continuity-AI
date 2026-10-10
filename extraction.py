from pathlib import Path
from docx import Document
import fitz


def read_document(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def read_pdf(file_path):
    document = fitz.open(file_path)
    text = ""

    for page in document:
        text += page.get_text()

    document.close()
    return text


def read_docx(file_path):
    document = Document(file_path)
    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text

def extract_documents():
    documents_folder = Path("documents")
    output_folder = Path("data/extracted_documents")

    output_folder.mkdir(parents=True, exist_ok=True)

    for file_path in documents_folder.iterdir():

        if file_path.suffix.lower() == ".txt":
            content = read_document(file_path)

        elif file_path.suffix.lower() == ".pdf":
            content = read_pdf(file_path)

        elif file_path.suffix.lower() == ".docx":
            content = read_docx(file_path)

        else:
            continue

        output_file = output_folder / f"{file_path.stem}.txt"

        with open(output_file, "w", encoding="utf-8") as file:
            file.write(content)

        print(f"Extracted: {file_path.name}")
        print(f"Saved to: {output_file}")


if __name__ == "__main__":
    extract_documents()
