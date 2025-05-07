from resume_reader import ResumeReader
from skill_matcher import SkillMatcher
from api import app

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