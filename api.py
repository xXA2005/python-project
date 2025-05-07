from flask import Flask, request, jsonify, render_template
import os
from resume_reader import ResumeReader
from skill_matcher import SkillMatcher

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

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

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
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