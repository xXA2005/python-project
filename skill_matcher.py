from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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