How to run:
>python ap.py
then, go to the local address:
http://127.0.0.1:5000/
Then input a job description (ex. marketing experience)
Then input a category (ex. sales, aviation, finance, business-development)
Then upload a file (There's a file called 'testresume.csv', to upload another resume it must be in the same format as 'testresume.csv'!!!)
Click 'Rank Resumes'
- You will see the top 10 resumes in that category ranked according to the job description (skills)
- Also you will see the rating of your own resume

Imports:
import math
from collections import Counter, defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from bm25 import BM25Ranker, Resume, load_resumes_from_csv
import re