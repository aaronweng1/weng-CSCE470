import math
import pandas as pd
from collections import Counter, defaultdict
import re

# Define stop words to filter out non-relevant terms
STOP_WORDS = {"i", "or", "new", "name", "state", "city", "all", "and", "to", "the", "of", "in", "with", "for", "a", "is", "on", "at", "by", "an", "be", "as", "from"}

# Define the Resume class to store resume information and score
class Resume:
    def __init__(self, id, resume_str, resume_html, category, source="database"):
        self.id = id
        self.resume_str = resume_str
        self.resume_html = resume_html
        self.category = category.upper()  # Ensure category is uppercase
        self.score = 0.0  # Default score to be calculated
        self.source = source  # To track if resume is from database or user file

    def __repr__(self):
        return f"Resume(ID: {self.id}, Score: {self.score:.4f}, Source: {self.source})"

class BM25Ranker:
    def __init__(self, resumes, k1=1.5, b=0.75):
        self.resumes = resumes
        self.k1 = k1
        self.b = b
        # Check if resumes are available to avoid division by zero
        if len(self.resumes) > 0:
            self.avg_doc_length = self.calculate_avg_doc_length()
        else:
            self.avg_doc_length = 0  # Set to 0 if there are no resumes

    def calculate_avg_doc_length(self):
        total_length = sum(len(resume.resume_str.split()) for resume in self.resumes)
        return total_length / len(self.resumes) if len(self.resumes) > 0 else 1  # Avoid division by zero

    def get_term_frequencies(self, text):
        terms = text.upper().split()  # Convert to uppercase for uniformity
        return Counter(term for term in terms if term not in STOP_WORDS)

    def calculate_document_frequency(self, term):
        return sum(1 for resume in self.resumes if term in resume.resume_str.upper())  # Convert to uppercase for consistency

    def calculate_bm25_score(self, resume, job_description_terms):
        score = 0.0
        resume_terms = self.get_term_frequencies(resume.resume_str)
        doc_length = len(resume.resume_str.split())

        for term, qf in job_description_terms.items():
            term_freq_in_resume = resume_terms.get(term, 0)
            if term_freq_in_resume > 0:
                doc_freq = self.calculate_document_frequency(term)
                if doc_freq > 0:
                    idf = math.log(1 + (len(self.resumes) - doc_freq + 0.5) / (doc_freq + 0.5))
                else:
                    idf = 0
                term_weight = ((self.k1 + 1) * term_freq_in_resume) / (self.k1 * ((1 - self.b) + self.b * doc_length / self.avg_doc_length) + term_freq_in_resume)
                score += idf * term_weight * qf
        return score

    def rank_resumes(self, job_description):
        if len(self.resumes) == 0:
            print("No resumes available to rank.")
            return []

        job_description_terms = self.get_term_frequencies(job_description)
        
        for resume in self.resumes:
            resume.score = self.calculate_bm25_score(resume, job_description_terms)
        
        ranked_resumes = sorted(self.resumes, key=lambda x: x.score, reverse=True)
        return ranked_resumes

def load_resumes_from_csv(file_path, categories=None, source="database"):
    resumes = []
    data = pd.read_csv(file_path)
    pattern = "[^a-zA-Z0-9 ]"  # To clean special characters

    for _, row in data.iterrows():
        id = str(row["ID"]).strip()
        resume_str = str(row["Resume_str"]).replace('"', '').strip()
        resume_str = re.sub(pattern, "", resume_str).lower()
        resume_html = str(row["Resume_html"]).strip()
        category = str(row["Category"]).strip().upper()

        # Add resume only if it belongs to the selected categories or if no categories are provided
        if categories is None or category in categories:
            resumes.append(Resume(id, resume_str, resume_html, category, source))
    
    return resumes

def rank_combined_resumes(database_file, user_file, job_description, categories=None):
    # Load resumes from both files and filter by categories
    database_resumes = load_resumes_from_csv(database_file, categories, source="database")
    user_resumes = load_resumes_from_csv(user_file, categories, source="user")

    # Combine both lists of resumes
    all_resumes = database_resumes + user_resumes

    # Initialize the BM25 ranker with all resumes
    bm25_ranker = BM25Ranker(all_resumes)
    
    # Rank resumes based on the provided job description
    ranked_resumes = bm25_ranker.rank_resumes(job_description)
    
    # Separate out the user resumes from the ranked list
    user_ranked_resumes = [resume for resume in ranked_resumes if resume.source == "user"]

    return ranked_resumes, user_ranked_resumes

# Test example
if __name__ == "__main__":
    database_file = "ResumeDatabase.csv"  # Example database file
    user_file = "UserResumes.csv"         # Example user-uploaded file
    job_description = "marketing and serving customers"  # Example job description

    # User can input categories, e.g., ["SALES", "HR"], or leave it as None to include all categories
    categories = ["SALES", "HR"]  # Example categories filter

    ranked_resumes, user_ranked_resumes = rank_combined_resumes(database_file, user_file, job_description, categories)
    
    # Display all ranked resumes with scores
    print("Top Ranked Resumes with Scores (All):")
    for i, resume in enumerate(ranked_resumes[:10]):  # Display top 10
        print(f"Rank {i + 1}: {resume}")
    
    # Display only user-provided resumes with scores
    print("\nTop Ranked User-Provided Resumes with Scores:")
    for i, resume in enumerate(user_ranked_resumes[:10]):  # Display top 10 user resumes
        print(f"Rank {i + 1}: {resume}")

# User input
'''
file_path = "Resume.csv"
categories = input("Enter the categories you're interested in, separated by commas (Ex. SALES, HR): ").upper().split(",")
categories = [category.strip() for category in categories]

# Load and rank resumes
resumes = load_and_filter_resumes(file_path, categories)
bm25_ranker = BM25Ranker(resumes)

# Display relevant terms for each category
if resumes:  # Only display relevant terms if resumes are loaded
    relevant_terms = get_relevant_terms_per_category(resumes)
    print("\nMost Relevant Terms by Category:")
    for category, terms in relevant_terms.items():
        print(f"\nCategory: {category}")
        for term, count in terms.items():
            print(f"{term}: {count}")

# Define job description and rank resumes
job_description = input("\nEnter a job description to rank resumes (Ex. marketing and serving customers): ").upper()
ranked_resumes = bm25_ranker.rank_resumes(job_description)

# Display top-ranked resumes with scores
if ranked_resumes:  # Only display if there are ranked resumes
    print("\nTop Ranked Resumes with Scores:")
    for i, resume in enumerate(ranked_resumes[:10]):  # Display top 10
        print(f"Rank {i + 1}: {resume}")
'''
        
if __name__ == "__main__":
    print("This module is not meant to be run directly.")