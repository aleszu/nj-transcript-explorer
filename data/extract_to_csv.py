#!/usr/bin/env python3
"""
Script to extract data from Word documents and create a CSV for text analysis.
Processes .docx files and extracts: date, candidate, location/title, transcript text and YouTube URL
"""

import os
import re
import csv
from pathlib import Path
from docx import Document
from datetime import datetime

def extract_date_from_filename(filename):
    """
    Extract date from filename for sorting and CSV.
    Looks for patterns like "Oct 2", "Sep 29", "Aug 28", etc.
    """
    # Month abbreviations mapping
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 
        'aug': '08', 'august': '08',
        'sep': '09', 'sept': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }
    
    # Look for date patterns like "Oct 2", "Sep 29", "Aug 28", "August 21", "September 5"
    date_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(\d+)'
    match = re.search(date_pattern, filename.lower())
    
    if match:
        month_abbr = match.group(1)
        day = match.group(2).zfill(2)
        month_num = month_map.get(month_abbr, '12')
        # Assume current year (2025) for sorting
        return f"2025-{month_num}-{day}"
    
    # If no date found, return a very early date for sorting
    return "2025-01-01"

def parse_filename_for_metadata(filename):
    """
    Parse filename to extract candidate, location, and other metadata.
    Handles various filename formats.
    """
    # Remove .docx extension
    name_without_ext = filename.replace('.docx', '')
    
    # Handle different filename patterns
    if name_without_ext.startswith(('Oct ', 'Sep ', 'Sept ', 'Aug ', 'Jul ', 'Jun ', 'May ', 'Apr ', 'Mar ', 'Feb ', 'Jan ', 'Dec ', 'Nov ')):
        # Format: "Oct 3 - Candidate_Location_Date.docx"
        parts = name_without_ext.split(' - ', 1)
        if len(parts) == 2:
            date_part = parts[0]
            name_part = parts[1]
            
            # Parse the name part
            name_parts = name_part.split('_')
            if len(name_parts) >= 2:
                candidate = name_parts[0]
                location = '_'.join(name_parts[1:-1]) if len(name_parts) > 2 else name_parts[1]
                return candidate, location, date_part
            else:
                # Handle case where there are no underscores (e.g., "Sherrill appearance on Democracy Docket")
                # Extract candidate from name part
                if 'sherrill' in name_part.lower():
                    candidate = 'Sherrill'
                elif 'ciattarelli' in name_part.lower():
                    candidate = 'Ciattarelli'
                else:
                    candidate = 'Unknown'
                
                # Location is the rest of the name part
                location = name_part.replace(candidate, '').strip()
                return candidate, location, date_part
    elif name_without_ext.startswith(('August ', 'September ', 'October ')):
        # Format: "August 21 - Sherrill speech on energy.docx"
        parts = name_without_ext.split(' - ', 1)
        if len(parts) == 2:
            date_part = parts[0]
            name_part = parts[1]
            
            # Extract candidate from name part
            if 'sherrill' in name_part.lower():
                candidate = 'Sherrill'
            elif 'ciattarelli' in name_part.lower():
                candidate = 'Ciattarelli'
            else:
                candidate = 'Unknown'
            
            # Location is the rest of the name part
            location = name_part.replace(candidate, '').strip()
            return candidate, location, date_part
    else:
        # Format: "Candidate_Location_Date.docx" or other patterns
        parts = name_without_ext.split('_')
        if len(parts) >= 2:
            candidate = parts[0]
            location = '_'.join(parts[1:-1]) if len(parts) > 2 else parts[1]
            return candidate, location, "Unknown"
    
    # Fallback - try to extract candidate name and date from filename
    if 'sherrill' in filename.lower():
        candidate = 'Sherrill'
    elif 'ciattarelli' in filename.lower():
        candidate = 'Ciattarelli'
    else:
        candidate = 'Unknown'
    
    # Try to extract date from filename
    date_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d+)', name_without_ext.lower())
    if date_match:
        date_part = f"{date_match.group(1).title()} {date_match.group(2)}"
    else:
        date_part = "Unknown"
    
    # Extract location/title from filename
    location = name_without_ext.replace(candidate, '').strip('_').strip('-').strip()
    
    return candidate, location, date_part

def convert_date_to_iso(date_str):
    """
    Convert date string to ISO format (YYYY-MM-DD) for 2025.
    Handles formats like "Oct 3", "Sep 29", "Aug 28", etc.
    """
    if date_str == "Unknown":
        return "2025-01-01"  # Default date
    
    # Month abbreviations mapping
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 
        'aug': '08', 'august': '08',
        'sep': '09', 'sept': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }
    
    # Look for date patterns like "Oct 3", "Sep 29", "Aug 28", "August 21", "September 5"
    date_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(\d+)'
    match = re.search(date_pattern, date_str.lower())
    
    if match:
        month_abbr = match.group(1)
        day = match.group(2).zfill(2)
        month_num = month_map.get(month_abbr, '01')
        return f"2025-{month_num}-{day}"
    
    return "2025-01-01"  # Default if parsing fails

def extract_text_from_docx(file_path):
    """
    Extract all text from a .docx file.
    """
    try:
        doc = Document(file_path)
        text_parts = []
        
        # Extract text from paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Only add non-empty paragraphs
                text_parts.append(paragraph.text.strip())
        
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return ""

def extract_youtube_url(text):
    """
    Extract YouTube URL from text if present.
    Returns the URL if found, empty string otherwise.
    """
    if not text:
        return ""
    
    # YouTube URL patterns
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, text)
        if match:
            # Return the full URL, not just the video ID
            return match.group(0)
    
    return ""

def clean_text_for_analysis(text):
    """
    Clean text for better analysis.
    """
    if not text:
        return ""
    
    # Remove YouTube URLs from text
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in youtube_patterns:
        text = re.sub(pattern, '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove HTML entities
    text = text.replace('&#39;', "'")
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    
    # Remove common transcript artifacts
    text = re.sub(r'\[.*?\]', '', text)  # Remove [laughter], [applause], etc.
    text = re.sub(r'\(.*?\)', '', text)  # Remove (inaudible), etc.
    
    return text.strip()

def process_docx_files(directory_path, output_csv):
    """
    Process all .docx files in the directory and create CSV.
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Directory {directory_path} does not exist!")
        return
    
    # Find all .docx files (excluding output files and temp files)
    docx_files = [f for f in directory.glob("*.docx") 
                  if not f.name.startswith("~$") 
                  and not f.name.startswith("Combined_")
                  and f.name != "requirements.docx"]
    
    if not docx_files:
        print(f"No .docx files found in {directory_path}")
        return
    
    print(f"Found {len(docx_files)} Word documents to process:")
    
    # Sort files by date for consistent output
    docx_files.sort(key=lambda x: extract_date_from_filename(x.name))
    
    # Prepare CSV data
    csv_data = []
    
    for docx_file in docx_files:
        print(f"\nProcessing: {docx_file.name}")
        
        try:
            # Parse filename for metadata
            candidate, location, date = parse_filename_for_metadata(docx_file.name)
            
            # Convert date to ISO format
            iso_date = convert_date_to_iso(date)
            
            # Extract text content
            text_content = extract_text_from_docx(docx_file)
            
            # Extract YouTube URL from text
            youtube_url = extract_youtube_url(text_content)
            
            # Clean text for analysis
            cleaned_text = clean_text_for_analysis(text_content)
            
            # Add to CSV data
            csv_data.append({
                'date': iso_date,
                'candidate': candidate,
                'location_or_title': location,
                'transcript_text': cleaned_text,
                'youtubeUrl': youtube_url
            })
            
            print(f"  Candidate: {candidate}")
            print(f"  Location/Title: {location}")
            print(f"  Date: {date}")
            print(f"  Word count: {len(cleaned_text.split()) if cleaned_text else 0}")
            if youtube_url:
                print(f"  YouTube URL: {youtube_url}")
            
        except Exception as e:
            print(f"  Error processing {docx_file.name}: {str(e)}")
    
    # Write to CSV
    if csv_data:
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'candidate', 'location_or_title', 'transcript_text', 'youtubeUrl']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            
            # Write header
            writer.writeheader()
            
            # Write data
            for row in csv_data:
                # Clean the transcript text to handle commas and special characters
                cleaned_row = row.copy()
                if 'transcript_text' in cleaned_row:
                    # Replace problematic characters that could break CSV parsing
                    cleaned_row['transcript_text'] = cleaned_row['transcript_text'].replace('\n', ' ').replace('\r', ' ')
                    # Remove any remaining control characters
                    cleaned_row['transcript_text'] = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned_row['transcript_text'])
                    # Replace problematic characters that could break CSV structure
                    cleaned_row['transcript_text'] = cleaned_row['transcript_text'].replace('"', "'")  # Replace quotes with single quotes
                    cleaned_row['transcript_text'] = cleaned_row['transcript_text'].replace('\t', ' ')  # Replace tabs with spaces
                    # Clean up multiple spaces
                    cleaned_row['transcript_text'] = re.sub(r'\s+', ' ', cleaned_row['transcript_text']).strip()
                
                # Clean other fields too
                for key, value in cleaned_row.items():
                    if isinstance(value, str):
                        cleaned_row[key] = value.replace('"', "'").replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                        cleaned_row[key] = re.sub(r'\s+', ' ', cleaned_row[key]).strip()
                
                writer.writerow(cleaned_row)
        
        print(f"\n✅ CSV created successfully: {output_csv}")
        print(f"📊 Total records: {len(csv_data)}")
        print(f"📝 Total words: {sum(len(row['transcript_text'].split()) for row in csv_data):,}")
        
        # Show summary by candidate
        candidate_counts = {}
        for row in csv_data:
            candidate = row['candidate']
            candidate_counts[candidate] = candidate_counts.get(candidate, 0) + 1
        
        print(f"\n📈 Records by candidate:")
        for candidate, count in sorted(candidate_counts.items()):
            print(f"  {candidate}: {count} records")
        
        # Show YouTube URL summary
        youtube_count = sum(1 for row in csv_data if row['youtubeUrl'])
        print(f"\n🎥 Records with YouTube URLs: {youtube_count}")
        if youtube_count > 0:
            print("  YouTube URLs found:")
            for row in csv_data:
                if row['youtubeUrl']:
                    print(f"    {row['candidate']} - {row['location_or_title']}: {row['youtubeUrl']}")
    
    else:
        print("No data to write to CSV")

def main():
    """
    Main function to run the script.
    """
    # Get the directory where the script is located
    script_dir = Path(__file__).parent
    directory_path = str(script_dir)
    
    # Output CSV filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"transcript_analysis_data_{timestamp}.csv"
    
    print("Word Document to CSV Extractor")
    print("=" * 50)
    print(f"Processing files in: {directory_path}")
    print(f"Output CSV: {output_csv}")
    print()
    
    process_docx_files(directory_path, output_csv)
    
    print("\n" + "=" * 50)
    print("Processing complete!")
    print(f"CSV file ready for text analysis: {output_csv}")

if __name__ == "__main__":
    main()
