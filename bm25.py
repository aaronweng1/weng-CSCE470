import math
import pandas as pd
from collections import Counter, defaultdict
import re

# Define stop words to filter out non-relevant terms
STOP_WORDS = {"and", "to", "the", "of", "in", "with", "for", "a", "is", "on", "at", "by", "an", "be", "as", "from"}

# Define the Resume class to store resume information and score
class Resume:
    def __init__(self, id, resume_str, resume_html, category):
        self.id = id
        self.resume_str = resume_str
        self.resume_html = resume_html
        self.category = category
        self.score = 0.0  # Default score to be calculated

    def __repr__(self):
        return f"Resume(ID: {self.id}, Score: {self.score:.4f})"

class BM25Ranker:
    def __init__(self, resumes, k1=1.5, b=0.75):
        self.resumes = resumes
        self.k1 = k1
        self.b = b
        self.avg_doc_length = self.calculate_avg_doc_length()

    def calculate_avg_doc_length(self):
        total_length = sum(len(resume.resume_str.split()) for resume in self.resumes)
        return total_length / len(self.resumes)

    def get_term_frequencies(self, text):
        terms = text.split()
        return Counter(term for term in terms if term not in STOP_WORDS)

    def calculate_document_frequency(self, term):
        return sum(1 for resume in self.resumes if term in resume.resume_str)

    def calculate_bm25_score(self, resume, job_description_terms):
        score = 0.0
        resume_terms = self.get_term_frequencies(resume.resume_str)
        doc_length = len(resume.resume_str.split())
        
        for term, qf in job_description_terms.items():
            term_freq_in_resume = resume_terms.get(term, 0)
            if term_freq_in_resume > 0:
                doc_freq = self.calculate_document_frequency(term)
                idf = math.log(1 + (len(self.resumes) - doc_freq + 0.5) / (doc_freq + 0.5))
                term_weight = ((self.k1 + 1) * term_freq_in_resume) / (self.k1 * ((1 - self.b) + self.b * doc_length / self.avg_doc_length) + term_freq_in_resume)
                score += idf * term_weight * qf
        return score

    def rank_resumes(self, job_description):
        job_description_terms = self.get_term_frequencies(job_description)
        
        for resume in self.resumes:
            resume.score = self.calculate_bm25_score(resume, job_description_terms)
        
        ranked_resumes = sorted(self.resumes, key=lambda x: x.score, reverse=True)
        return ranked_resumes

# Load resumes from CSV file and filter by category
def load_and_filter_resumes(file_path, categories):
    resumes = []
    data = pd.read_csv(file_path)
    pattern = "[^a-zA-Z0-9 ]"  # To clean special characters

    for _, row in data.iterrows():
        id = str(row["ID"]).strip()
        resume_str = str(row["Resume_str"]).replace('"', '').strip()
        resume_str = re.sub(pattern, "", resume_str).lower()  # Clean text
        resume_html = str(row["Resume_html"]).strip()
        category = str(row["Category"]).strip()

        if category in categories and id and resume_str:
            resumes.append(Resume(id, resume_str, resume_html, category))

    print(f"Loaded {len(resumes)} resumes for categories: {', '.join(categories)}")
    return resumes

# Get most relevant terms per category
def get_relevant_terms_per_category(resumes, top_n=10):
    category_term_freq = defaultdict(Counter)

    for resume in resumes:
        terms = resume.resume_str.split()
        category_term_freq[resume.category].update(term for term in terms if term not in STOP_WORDS)
    
    relevant_terms = {category: dict(term_counter.most_common(top_n)) for category, term_counter in category_term_freq.items()}
    return relevant_terms

# User input
file_path = "Resume.csv"
categories = input("Enter the categories you're interested in, separated by commas (Ex. SALES, HR): ").split(",")
categories = [category.strip() for category in categories]

# Load and rank resumes
resumes = load_and_filter_resumes(file_path, categories)
bm25_ranker = BM25Ranker(resumes)

# Display relevant terms for each category
relevant_terms = get_relevant_terms_per_category(resumes)
print("\nMost Relevant Terms by Category:")
for category, terms in relevant_terms.items():
    print(f"\nCategory: {category}")
    for term, count in terms.items():
        print(f"{term}: {count}")

# Define job description and rank resumes
job_description = input("\nEnter a job description to rank resumes (Ex. marketing and serving customers): ")
ranked_resumes = bm25_ranker.rank_resumes(job_description)

# Display top-ranked resumes with scores
print("\nTop Ranked Resumes with Scores:")
for i, resume in enumerate(ranked_resumes[:10]):  # Display top 10
    print(f"Rank {i + 1}: {resume}")
