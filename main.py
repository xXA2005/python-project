import re
from PyPDF2 import PdfReader
from docx import Document
import os
from flask import Flask, request, jsonify, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

            name_pattern = r'(?:^|\n)\s*([a-zA-Z]+\s+[a-zA-Z]+)\s*(?=\n|\s*(?:[a-zA-Z0-9._%+-]+@|skills))'
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            skills_pattern = r'\b(python|java|c\+\+|sql|javascript|html|css|machine learning|data analysis|project management|teamwork|communication)\b'

            name_match = re.search(name_pattern, content_normalized, re.MULTILINE)
            self.name = name_match.group(1).strip().title() if name_match else "unknown"

            email_match = re.search(email_pattern, content_normalized)
            self.email = email_match.group(0) if email_match else "unknown"

            self.skills = re.findall(skills_pattern, content_normalized)
            self.skills = list(set(self.skills))

            return True

        except Exception as e:
            print(f"error extracting info: {e}")
            return False

class SkillMatcher:
    def __init__(self):
        self.job_profiles = {
            "Software Engineer": ["python", "java", "c++", "sql", "javascript"],
            "Data Scientist": ["python", "sql", "machine learning", "data analysis"],
            "Project Manager": ["project management", "teamwork", "communication"]
        }
        self.vectorizer = TfidfVectorizer()

    def match_skills(self, candidate_skills):
        try:
            candidate_skills_str = " ".join(candidate_skills)
            job_skill_strings = [" ".join(skills) for skills in self.job_profiles.values()]
            corpus = [candidate_skills_str] + job_skill_strings
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            results = {job: round(similarity * 100, 2) for job, similarity in zip(self.job_profiles.keys(), similarities)}
            return results
        except Exception as e:
            print(f"error in skill matching: {e}")
            return {}

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_resume():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "no file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "no file selected"}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        reader = ResumeReader(file_path)
        if not reader.extract_info():
            return jsonify({"error": "failed to process resume"}), 500

        matcher = SkillMatcher()
        match_results = matcher.match_skills(reader.skills) if reader.skills else {}

        response = {
            "name": reader.name,
            "email": reader.email,
            "skills": reader.skills,
            "job_matches": match_results
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def main():
    while True:
        print("\noptions:")
        print("1. analyze resume (enter file path)")
        print("2. start API (type 'api')")
        print("3. exit (type 'exit')")
        choice = input("choice: ").strip()

        if choice.lower() == 'api':
            app.run()
            break
        elif choice.lower() == 'exit':
            print("exiting program")
            break
        else:
            resume_file = choice
            reader = ResumeReader(resume_file)
            matcher = SkillMatcher()
            
            if reader.extract_info():
                print(f"name: {reader.name}")
                print(f"email: {reader.email}")
                print(f"skills: {', '.join(reader.skills)}")
                if reader.skills:
                    match_results = matcher.match_skills(reader.skills)
                    print("\njob match results:")
                    for job, score in match_results.items():
                        print(f"{job}: {score}% match")
                else:
                    print("no skills found in resume")
            else:
                print("failed to process resume")

if __name__ == "__main__":
    main()