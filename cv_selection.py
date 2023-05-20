import streamlit as st
import PyPDF2
import pandas as pd
import re
import glob
import base64
import io
import os
from datetime import datetime

# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Load and extract text from multiple PDF resumes in a folder
def load_resumes_from_folder(folder_path):
    resumes = []
    pdf_files = glob.glob(folder_path + "/*.pdf")
    for file in pdf_files:
        candidate_name = re.sub(r'[-_]', ' ', os.path.basename(file).split(".")[0])  # Replace '-' and '_' with space
        candidate_name = re.sub(r'\bCV\b', '', candidate_name, flags=re.IGNORECASE)  # Remove 'CV' or 'cv' keyword
        with open(file, "rb") as f:
            resume_text = extract_text_from_pdf(f)
        resumes.append((candidate_name.strip(), resume_text))  # Store candidate name along with the resume content
    return resumes

# Function to calculate scores based on keyword matches
def calculate_scores(resumes, keywords):
    scores = []
    for resume in resumes:
        score = sum([1 for keyword in keywords if keyword.lower() in resume[1].lower()])
        scores.append(score)
    return scores

# Function to display scores
def display_scores(scores, candidate_names, field_of_activity):
    df = pd.DataFrame({"Candidate Name": candidate_names, "Match Scores": scores, "Field of Activity": field_of_activity})
    df['Rank'] = df['Match Scores'].rank(ascending=False, method='min')  # Calculate ranks based on scores
    
    # Rearrange columns with "Rank" in the first position
    df = df[['Rank', 'Candidate Name', 'Match Scores', 'Field of Activity']]
    
    # Display dataframe sorted by rank
    sorted_df = df.sort_values(by='Rank').reset_index(drop=True)
    st.dataframe(sorted_df)
    
    # Generate download link for the dataframe as an XLSX file
    area = field_of_activity[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{area} Resume Match Scores_{timestamp}.xlsx"
    
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        sorted_df.to_excel(writer, sheet_name='Resume Match Scores', index=False)
    excel_file.seek(0)
    b64 = base64.b64encode(excel_file.read()).decode()  # Convert to base64 string
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Results</a>'
    st.markdown(href, unsafe_allow_html=True)

# Streamlit app
def main():

    # Centered title
    st.markdown(
        """
        <style>
        body {
            background-color: #BF8C88;
        }
        .title {
            text-align: left;
            text-decoration: underline;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<h2 class="title">Resume Analysis App</h2>', unsafe_allow_html=True)

    # st.sidebar.title("Resume Analysis App")

    # Sidebar options
    st.sidebar.markdown('<h2 class="title">Options</h2>', unsafe_allow_html=True)

    # Field of Activity input
    field_of_activity = st.sidebar.text_input("Enter the Field of Activity")

    # Keywords input
    keyword_input = st.sidebar.text_area("Enter the Keywords (separated by comma)")

    # Folder uploader to load CVs
    st.markdown('<h3 class="title">Folder uploader to load CVs</h3>', unsafe_allow_html=True)
    folder_path = st.text_input("Enter the Folder Path")

    if field_of_activity and keyword_input and folder_path:
        if not os.path.exists(folder_path):
            st.error("Folder path does not exist.")
            return
        
        keywords = [keyword.strip() for keyword in keyword_input.split(",")]
        resumes = load_resumes_from_folder(folder_path)
        scores = calculate_scores(resumes, keywords)
        
        st.markdown('<h3 class="title">Display Match Scores</h3>', unsafe_allow_html=True)
        display_scores(scores, [resume[0] for resume in resumes], [field_of_activity] * len(resumes))  # Pass candidate names and field_of_activity as lists

# Run the app
if __name__ == "__main__":
    main()
