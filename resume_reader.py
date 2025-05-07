import re
from PyPDF2 import PdfReader
from docx import Document


class ResumeReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.name = None
        self.email = None
        self.skills = []

    def extract_text(self):
        try:
            file_extension = self.file_path.lower().split('.')[-1]
            
            if file_extension == 'txt':
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            
            elif file_extension == 'pdf':
                reader = PdfReader(self.file_path)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() or ''
                return text
            
            elif file_extension == 'docx':
                doc = Document(self.file_path)
                text = ''
                for para in doc.paragraphs:
                    text += para.text + '\n'
                return text
            
            else:
                raise ValueError(f"unsupported file format: {file_extension}")

        except FileNotFoundError:
            raise FileNotFoundError(f"file {self.file_path} not found")
        except Exception as e:
            raise Exception(f"error reading file: {e}")

    def extract_info(self):
        try:
            content = self.extract_text()
            if not content:
                raise ValueError("no content extracted from file")

            content_normalized = re.sub(r'[ \t]+', ' ', content.strip())
            content_normalized = content_normalized.lower()

            content_for_name = re.sub(r'\s+', ' ', content.strip())

            name_pattern = r"(?:^|\n)\s*([A-Za-z]+(?:[-'][A-Za-z]+)?(?:\s+[A-Za-z]+(?:[-'][A-Za-z]+)?)*)\s*(?=\s*[a-zA-Z0-9._%+-]+@|\b(?:skills|contact|email)\b|$)"
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            skills_pattern = r'\b(python|java|c\+\+|sql|javascript|html|css|machine learning|data analysis|project management|teamwork|communication)\b'

            name_match = re.search(name_pattern, content_for_name, re.IGNORECASE)
            if name_match:
                raw_name = name_match.group(1).strip()
                name_parts = raw_name.split()
                unique_parts = []
                for part in name_parts:
                    if part.lower() not in [p.lower() for p in unique_parts]:
                        unique_parts.append(part)
                self.name = ' '.join(unique_parts).title()
            else:
                self.name = "unknown"

            email_match = re.search(email_pattern, content_normalized)
            self.email = email_match.group(0) if email_match else "unknown"

            self.skills = re.findall(skills_pattern, content_normalized)
            self.skills = list(set(self.skills))

            return True

        except Exception as e:
            print(f"error extracting info: {e}")
            return False