import streamlit as st
import PyPDF2
import pandas as pd
import re
import base64
import io
from datetime import datetime

# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Load and extract text from multiple PDF resumes
def load_resumes(files):
    resumes = []
    for file in files:
        candidate_name = re.sub(r'[-_]', ' ', file.name.split(".")[0])  # Replace '-' and '_' with space
        candidate_name = re.sub(r'\bCV\b', '', candidate_name, flags=re.IGNORECASE)  # Remove 'CV' or 'cv' keyword
        resume_text = extract_text_from_pdf(file)
        resumes.append((candidate_name.strip(), resume_text))  # Store candidate name along with the resume content
    return resumes

# Function to calculate scores based on keyword matches
def calculate_scores(resumes, keywords):
    scores = []
    for resume in resumes:
        score = sum([1 for keyword in keywords if keyword.lower() in resume[1].lower()])
        scores.append(score)
    return scores

# Function to display scores and generate graph
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
    st.title("Resume Analysis App")

    # Field of Activity and Keywords input
    field_of_activity = st.text_input("Enter the Field of Activity")
    keyword_input = st.text_area("Enter the Keywords (separated by comma)")

    if field_of_activity and keyword_input:
        keywords = [keyword.strip() for keyword in keyword_input.split(",")]

        # File uploader to load resumes
        uploaded_files = st.file_uploader("Upload PDF Resumes", accept_multiple_files=True, type="pdf")

        if uploaded_files:
            resumes = load_resumes(uploaded_files)
            scores = calculate_scores(resumes, keywords)
            display_scores(scores, [resume[0] for resume in resumes], [field_of_activity] * len(resumes))  # Pass candidate names and field_of_activity as lists
            
# Run the app
if __name__ == "__main__":
    main()
