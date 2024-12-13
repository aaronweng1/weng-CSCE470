from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from bm25 import BM25Ranker, Resume, load_resumes_from_csv
import re

app = Flask(__name__)
app.secret_key = "secret_key_for_flash_messages"
FILE_PATH = "Resume.csv"

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/rank", methods=["POST"])
def rank_resumes():
    categories = [cat.strip().upper() for cat in request.form["categories"].split(",")]

    # Log for debugging
    print(f"Categories selected: {categories}")

    # Check if a resume file was uploaded
    if 'resume_file' not in request.files or request.files['resume_file'].filename == '':
        flash("No resume file uploaded.")
        return redirect(url_for("home"))

    # Read and decode the uploaded resume file
    uploaded_file = request.files['resume_file']
    uploaded_resume_text = uploaded_file.read().decode("utf-8")

    # Clean the resume content
    uploaded_resume_text = re.sub(r"[\n,]+", " ", uploaded_resume_text).strip()

    # Load and filter resumes from the CSV file by categories
    resumes = load_resumes_from_csv(FILE_PATH, categories)

    if len(resumes) == 0:
        flash("No resumes found for the specified categories.")
        return redirect(url_for("home"))

    # Add the uploaded resume as a new Resume object
    uploaded_resume = Resume(id="uploaded", resume_str=uploaded_resume_text, resume_html="", category="Uploaded")
    resumes.append(uploaded_resume)  # Include the uploaded resume in the ranking

    # Initialize BM25 ranker
    bm25_ranker = BM25Ranker(resumes)

    # Get job description from the form
    job_description = request.form["job_description"]

    # Rank all resumes based on the job description
    ranked_resumes = bm25_ranker.rank_resumes(job_description)

    # Log the ranked resumes' IDs and scores for debugging
    print("Top-ranked resumes:")
    for resume in ranked_resumes[:10]:
        print(f"Resume ID: {resume.id}, Score: {resume.score}")

    # Identify the uploaded resume in the ranked list
    uploaded_resume_rank = next(
        (index + 1 for index, resume in enumerate(ranked_resumes) if resume.id == "uploaded"), None
    )

    return render_template(
        "results.html",
        resumes=ranked_resumes[:10],  # Top 10 resumes
        uploaded_resume_rank=uploaded_resume_rank,
        uploaded_resume_score=uploaded_resume.score,
    )

if __name__ == "__main__":
    app.run(debug=True)
