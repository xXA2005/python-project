import re
import os
from typing import List, Dict, Optional
from flask import Flask, request, jsonify, render_template
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ResumeReader:
    """Class to read and extract information from resume files (TXT, PDF)."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.name: Optional[str] = None
        self.email: Optional[str] = None
        self.skills: List[str] = []

    def extract_text(self) -> Optional[str]:
        """Extract text from TXT or PDF files."""
        try:
            file_ext = os.path.splitext(self.file_path)[1].lower()
            
            if file_ext == '.txt':
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            
            elif file_ext == '.pdf':
                with open(self.file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                    return text
            
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
        except FileNotFoundError:
            raise FileNotFoundError(f"File {self.file_path} not found.")
        except Exception as e:
            raise Exception(f"Error reading file: {e}")

    def extract_info(self) -> bool:
        """Extract name, email, and skills from the resume content."""
        try:
            content = self.extract_text()
            if not content:
                raise ValueError("No content extracted from file.")
                
       
            
            # Normalize content: collapse multiple spaces/tabs, but preserve newlines
            content_normalized = re.sub(r'[ \t]+', ' ', content.strip())
            content_normalized = content_normalized.lower()

            # Regex patterns for extraction
            # Updated name pattern: match two words, followed by space/email/skills
            name_pattern = r'(?:^|\n)\s*([a-zA-Z]+\s+[a-zA-Z]+)\s*(?=\n|\s*(?:[a-zA-Z0-9._%+-]+@|skills))'
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            skills_pattern = r'\b(python|java|c\+\+|sql|javascript|html|css|machine learning|data analysis|project management|teamwork|communication)\b'

            # Extract name
            name_match = re.search(name_pattern, content_normalized, re.MULTILINE)
            self.name = name_match.group(1).strip().title() if name_match else "Unknown"

            # Extract email
            email_match = re.search(email_pattern, content_normalized)
            self.email = email_match.group(0) if email_match else "Unknown"

            # Extract skills
            self.skills = re.findall(skills_pattern, content_normalized)
            self.skills = list(set(self.skills))  # Remove duplicates

            return True

        except Exception as e:
            print(f"Error extracting info: {e}")
            return False

class SkillMatcher:
    """Class to match resume skills with job profiles."""
    
    def __init__(self):
        # Static job profiles with required skills
        self.job_profiles: Dict[str, List[str]] = {
            "Software Engineer": ["python", "java", "c++", "sql", "javascript"],
            "Data Scientist": ["python", "sql", "machine learning", "data analysis"],
            "Project Manager": ["project management", "teamwork", "communication"]
        }
        self.vectorizer = TfidfVectorizer()

    def match_skills(self, candidate_skills: List[str]) -> Dict[str, float]:
        """Match candidate skills with job profiles using cosine similarity."""
        try:
            candidate_skills_str = " ".join(candidate_skills)
            job_skill_strings = [" ".join(skills) for skills in self.job_profiles.values()]
            corpus = [candidate_skills_str] + job_skill_strings
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            results = {job: round(similarity * 100, 2) for job, similarity in zip(self.job_profiles.keys(), similarities)}
            return results
        except Exception as e:
            print(f"Error in skill matching: {e}")
            return {}

# Flask App
app = Flask(__name__)
UPLOAD_FOLDER = 'Uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    """Render the upload page."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_resume():
    """API endpoint to upload and process a resume."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        allowed_extensions = {'.txt', '.pdf'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({"error": f"Unsupported file format: {file_ext}"}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        reader = ResumeReader(file_path)
        if not reader.extract_info():
            return jsonify({"error": "Failed to process resume"}), 500

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
    """Main function for console-based testing."""
    resume_file = "resume.txt"  # Use one of the demo resumes
    reader = ResumeReader(resume_file)
    matcher = SkillMatcher()
    
    if reader.extract_info():
        print(f"Name: {reader.name}")
        print(f"Email: {reader.email}")
        print(f"Skills: {', '.join(reader.skills)}")
        if reader.skills:
            match_results = matcher.match_skills(reader.skills)
            print("\nJob Match Results:")
            for job, score in match_results.items():
                print(f"{job}: {score}% match")
        else:
            print("No skills found in resume.")
    else:
        print("Failed to process resume.")

if __name__ == "__main__":
    main()
    app.run()