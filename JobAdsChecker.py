#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 30 22:45:14 2024

@author: Shin Kira
"""
import requests
import argparse
import platform
from bs4 import BeautifulSoup
import os
import json
import pandas as pd
from collections import OrderedDict
from urllib.parse import urljoin
import datetime

# List of URLs to search through
urls = {
    "SfN": "https://neurojobs.sfn.org/jobs/",
    "Science": "https://jobs.sciencecareers.org/jobs/",
    "Nature": "https://www.nature.com/naturecareers/jobs/"
}

# Base URLs for each site
base_urls = {
    "SfN": "https://neurojobs.sfn.org",
    "Science": "https://jobs.sciencecareers.org",
    "Nature": "https://www.nature.com"
}

# Keywords for filtering
position_keywords = ["tenure-track", "tenure track", "assistant professor", "assistant/associate", "assistant / associate", "assistant or associate", "open rank", "faculty"]
neuro_keywords = ["neuro", "neural", "brain", "neuroscience", "psych", "physiol", "cognit"]

# Function to fetch the job listings from a given page URL
def fetch_jobs(page_url, base_url, source):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    jobs = soup.find_all('li', class_='lister__item')
    job_list = []

    def add_job_to_list(job_id, title, recruiter, location, link, description, source):
        job_list.append({
            'Job ID': job_id,
            'Title': title,
            'University': recruiter,
            'Location': location,
            'Link': link,
            'Description': description,
            'Source': source,
        })

    for job in jobs:
        header = job.find('h3', class_='lister__header')
        if header:
            title_tag = header.find('a')
            if title_tag:
                title = title_tag.string.strip()
                link = base_url + title_tag['href'].strip()
                location_tag = job.find('li', class_='lister__meta-item--location')
                location = location_tag.string.strip() if location_tag else "N/A"
                recruiter_tag = job.find('li', class_='lister__meta-item--recruiter')
                recruiter = recruiter_tag.string.strip() if recruiter_tag else "N/A"
                description_tag = job.find('p', class_='lister__description')
                description = description_tag.string.strip() if description_tag else "N/A"
                job_id = job.get('id').split("-")[1].strip() if job else None
                
                # Define title and description conditions
                title_condition = (any(keyword in title.lower() for keyword in position_keywords) or
                                   any(keyword in description.lower() for keyword in position_keywords))
                
                description_condition = (any(keyword in title.lower() for keyword in neuro_keywords) or
                                         any(keyword in description.lower() for keyword in neuro_keywords))
                
                # Filter jobs based on the defined conditions
                if source == "SfN":
                    if title_condition:
                        add_job_to_list(job_id, title, recruiter, location, link, description, source)
                else:
                    if title_condition and description_condition:
                        add_job_to_list(job_id, title, recruiter, location, link, description, source)

    return job_list

# Function to find the next page URL
def get_next_page_url(soup, base_url):
    next_page = soup.find('link', rel='next')
    if next_page:
        next_url = next_page['href']
        # Check if the URL is relative or absolute
        if not next_url.startswith('http'):
            next_url = urljoin(base_url, next_url)
        return next_url
    return None

# Function to fetch job listings from all pages for a given URL
def fetch_all_jobs(start_url, base_url, source):
    global debug
    all_jobs = []
    current_url = start_url
    counter = 0
    if debug:
        max_iterations = 3
    else:
        max_iterations = float('inf')

    while current_url and counter < max_iterations:
        print(current_url)
        response = requests.get(current_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        all_jobs.extend(fetch_jobs(current_url, base_url, source))
        current_url = get_next_page_url(soup, base_url)
        counter += 1
    return all_jobs

# Function to fetch job listings from multiple URLs
def fetch_jobs_from_multiple_urls(urls, base_urls):
    all_jobs = []
    for source, url in urls.items():
        base_url = base_urls[source]
        all_jobs.extend(fetch_all_jobs(url, base_url, source))
    return all_jobs

# Function to fetch detailed job info
def fetch_job_details(job_link):
    response = requests.get(job_link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        job_details = {}

        # Extract job title
        try:
            job_title = soup.find('h1', class_='mds-font-trafalgar').get_text(strip=True)
        except:
            job_title = soup.find('h1', class_='mds-font-s6').get_text(strip=True)
        job_details['Title'] = job_title

        # Extract employer
        employer = soup.find('dd', class_='mds-list__value').get_text(strip=True)
        job_details['Employer'] = employer

        # Extract location
        location = soup.find_all('dd', class_='mds-list__value')[1].get_text(strip=True)
        job_details['Location'] = location

        # Extract salary
        salary = soup.find_all('dd', class_='mds-list__value')[2].get_text(strip=True)
        job_details['Salary'] = salary

        # Extract job description
        try:
            description = soup.find('div', class_='mds-edited-text').get_text(strip=True)
        except:
            description = soup.find('div', class_='mds-prose').get_text(strip=True)
        job_details['Description'] = description

        # Extract application URL
        apply_button = soup.find('a', {'data-hook': 'apply-button'})
        if apply_button:
            application_url = apply_button['href']
        else:
            # Handle the case where the element is not found
            application_url = None  # or some default value, or log an error
        # application_url = soup.find('a', {'data-hook': 'apply-button'})['href']
        job_details['ApplicationURL'] = application_url
        
        # Find the script tag that contains the JSON data
        script_tag = soup.find('script', string=lambda string: string and 'ClientGoogleTagManagerDataLayer' in string)
        
        if script_tag:
            # Extract the JSON part from the script content
            json_str = script_tag.string.split('=', 1)[1].strip().rstrip(';')
            json_content = json.loads(json_str)
        
            # Extract the JobDatePosted
            job_date_posted = json_content[0].get('JobDatePosted', None)
            job_details['Date Posted'] = job_date_posted
            
        return job_details
    else:
        return {}


# Main function to detect new job ads
def detect_new_jobs():
    new_jobs = fetch_jobs_from_multiple_urls(urls, base_urls)
    detailed_jobs = []
    
    field_order = [
        "Source",
        "Date Posted",
        "University",
        "Title",
        "Department",
        "Field",
        "Location",
        "Deadline",
        "# Rec Letters",
        "Contact Only?",
        "Research Stat",
        "Res Page Limit",
        "Cover Letter",
        "CV",
        "Diversity Stat",
        "Teaching Stat",
        "Other docs",
        "Recruiter",
        "Link",
        "Job ID",
        "Description"
    ]
    
    for job in new_jobs:
        
        
        details = fetch_job_details(job['Link'])
            
        job.update(details)
        
            
        ordered_job = OrderedDict((k, job[k]) for k in field_order if k in job)
        
        # Replace the old job dictionary with the new ordered one
        detailed_jobs.append(ordered_job)  # Instead of job, use ordered_job
        
    return detailed_jobs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check job ads (@ SfN, Science, Nature, AJO etc) and save in Excel.")
    parser.add_argument("--debug", action="store_true", help="Checks ads only on 3 pages on each site.")
    args = parser.parse_args()
    debug = args.debug
    # debug= True
    if debug:
        print('Running in debug mode')
    # Fetch and print the job listings
    job_listings = detect_new_jobs()
    df = pd.DataFrame(job_listings)
    
    # Remove any extra text, such as "(listed until 2024/09/30)"
    df['Date Posted'] = df['Date Posted'].str.replace(r"\(.*", "", regex=True).str.strip()
    df['Date Posted'] = df['Date Posted'].str.replace(r"\s\d{2}:\d{2}[APM]{2}", "", regex=True)
    df['Date Posted'] = df['Date Posted'].str.replace('Sept', 'Sep')

    # Remove "The" at the beginning of university names.
    df['University'] = df['University'].str.replace(r'^\s*The\s+', '', regex=True)
    

    def parse_dates(date_str):
        for fmt in ("%d %b %Y", "%Y/%m/%d", "%b %d, %Y"):
            try:
                return pd.to_datetime(date_str, format=fmt)
            except ValueError:
                continue
        return pd.NaT  # If neither format works, return NaT

    # Apply the custom function to parse the 'Date Posted' column
    df['Date Posted'] = df['Date Posted'].apply(parse_dates)

    # Sort the DataFrame by 'Date Posted'
    df = df.sort_values(by=['Date Posted', 'University', 'Source'], ascending=[False, True, False])
        
    print(df)
    
    # Define the output file path
    current_date = current_date = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    output_file = f'job_ads_{current_date}.xlsx'
    if debug:
        output_file = output_file.split('.')[0] + '_debug' + '.xlsx'
        
    # Detect the operating system
    current_os = platform.system()
    
    # Get the computer name
    computer_name = platform.node()
    
    # Dictionary to map computer names to directories
    computer_dirs = {
        'My-PC': r'C:/Users',
        'My-MAC': r'/Users'
        # Add more computer names and directories as needed
    }
    
    # Function to get the save directory based on the computer name
    def get_save_dir(computer_name):
        # Check if any key is a substring of the computer name
        for key in computer_dirs:
            if key in computer_name:
                return computer_dirs[key]
        raise Exception(f"Unsupported computer name: {computer_name}")
    
    # Get the save directory
    save_dir = get_save_dir(computer_name)
    
    
    output_file_path = os.path.join(save_dir, output_file)
    
    # Replace "University of" or "University" with "U" in the 'University' column
    df['University'] = df['University'].str.replace(r'\bUniversity of\b', 'U.', regex=True)
    df['University'] = df['University'].str.replace(r'\bUniversity\b', 'Univ', regex=True)
    
    # Save to an Excel file with hyperlinks
    with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Jobs')
        workbook = writer.book
        worksheet = writer.sheets['Jobs']
        
        # Create a date format
        date_format = workbook.add_format({'num_format': 'yy/mm/dd'})
    
        # Get the column indices based on their labels
        date_posted_col_idx = df.columns.get_loc('Date Posted') + 1
        university_col_idx = df.columns.get_loc('University') + 1
        link_col_idx = df.columns.get_loc('Link') + 1
    
        # Apply the date format to the 'Date Posted' column
        worksheet.set_column(f'{chr(64 + date_posted_col_idx)}:{chr(64 + date_posted_col_idx)}', None, date_format)
        
        # Set the 'University' column to be twice as wide as other columns
        worksheet.set_column(f'{chr(64 + university_col_idx)}:{chr(64 + university_col_idx)}', 20)
            
        # Write the dates with the correct format
        for idx, date in enumerate(df['Date Posted']):
            # Check if the value is NaT (Not a Time)
            if pd.isna(date):
                # Optionally, write an empty cell or skip writing the date
                worksheet.write(f'{chr(64 + date_posted_col_idx)}{idx + 2}', '')
            else:
                # Write the valid date
                worksheet.write_datetime(f'{chr(64 + date_posted_col_idx)}{idx + 2}', date, date_format)
        
        # Iterate through the DataFrame and create hyperlinks
        for idx, url in enumerate(df['Link']):
            worksheet.write_url(f'{chr(64 + link_col_idx)}{idx + 2}', url, string=url)
    
    print(f"Job listings saved to {output_file_path}")
