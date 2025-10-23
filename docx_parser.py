#!/usr/bin/env python3
"""
Simple DOCX parser to extract transcript data and serve as JSON API.
This replaces the CSV approach with direct DOCX file parsing.
"""

import os
import re
import json
from pathlib import Path
from docx import Document
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def extract_date_from_filename(filename):
    """Extract date from filename for sorting and display."""
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
        return f"2025-{month_num}-{day}"
    
    return "2025-01-01"

def parse_filename_for_metadata(filename):
    """Parse filename to extract candidate, location, and other metadata."""
    name_without_ext = filename.replace('.docx', '')
    
    # Handle different filename patterns
    if name_without_ext.startswith(('Oct ', 'Sep ', 'Sept ', 'Aug ', 'Jul ', 'Jun ', 'May ', 'Apr ', 'Mar ', 'Feb ', 'Jan ', 'Dec ', 'Nov ')):
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
                # Handle case where there are no underscores
                if 'sherrill' in name_part.lower():
                    candidate = 'Sherrill'
                elif 'ciattarelli' in name_part.lower():
                    candidate = 'Ciattarelli'
                else:
                    candidate = 'Unknown'
                
                location = name_part.replace(candidate, '').strip()
                return candidate, location, date_part
    elif name_without_ext.startswith(('August ', 'September ', 'October ')):
        parts = name_without_ext.split(' - ', 1)
        if len(parts) == 2:
            date_part = parts[0]
            name_part = parts[1]
            
            if 'sherrill' in name_part.lower():
                candidate = 'Sherrill'
            elif 'ciattarelli' in name_part.lower():
                candidate = 'Ciattarelli'
            else:
                candidate = 'Unknown'
            
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

def extract_youtube_url(text):
    """Extract YouTube URL from text if present."""
    if not text:
        return ""
    
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return ""

def extract_text_from_docx(file_path):
    """Extract all text from a .docx file."""
    try:
        doc = Document(file_path)
        text_parts = []
        
        # Extract text from paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return ""

def clean_text_for_analysis(text):
    """Clean text for better analysis."""
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

def process_docx_files(directory_path):
    """Process all .docx files in the directory and return data."""
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Directory {directory_path} does not exist!")
        return []
    
    # Find all .docx files (excluding temp files)
    docx_files = [f for f in directory.glob("*.docx") 
                  if not f.name.startswith("~$")]
    
    if not docx_files:
        print(f"No .docx files found in {directory_path}")
        return []
    
    print(f"Found {len(docx_files)} Word documents to process")
    
    # Sort files by date for consistent output
    docx_files.sort(key=lambda x: extract_date_from_filename(x.name))
    
    # Process files
    transcripts = []
    
    for docx_file in docx_files:
        print(f"Processing: {docx_file.name}")
        
        try:
            # Parse filename for metadata
            candidate, location, date = parse_filename_for_metadata(docx_file.name)
            
            # Convert date to ISO format
            iso_date = extract_date_from_filename(date)
            
            # Extract text content
            text_content = extract_text_from_docx(docx_file)
            
            # Extract YouTube URL from text
            youtube_url = extract_youtube_url(text_content)
            
            # Clean text for analysis
            cleaned_text = clean_text_for_analysis(text_content)
            
            # Add to transcripts
            transcripts.append({
                'date': iso_date,
                'candidate': candidate,
                'location_or_title': location,
                'transcript_text': cleaned_text,
                'youtubeUrl': youtube_url,
                'youtubeId': youtube_url.split('v=')[1].split('&')[0] if youtube_url and 'v=' in youtube_url else ''
            })
            
            print(f"  Candidate: {candidate}")
            print(f"  Location/Title: {location}")
            print(f"  Date: {date}")
            print(f"  Word count: {len(cleaned_text.split()) if cleaned_text else 0}")
            if youtube_url:
                print(f"  YouTube URL: {youtube_url}")
            
        except Exception as e:
            print(f"  Error processing {docx_file.name}: {str(e)}")
    
    return transcripts

# Global variable to store processed transcripts
transcripts_data = []

@app.route('/api/transcripts', methods=['GET'])
def get_transcripts():
    """API endpoint to get all transcripts."""
    return jsonify(transcripts_data)

@app.route('/api/transcripts/reload', methods=['POST'])
def reload_transcripts():
    """API endpoint to reload transcripts from DOCX files."""
    global transcripts_data
    transcripts_data = process_docx_files('data')
    return jsonify({
        'message': f'Reloaded {len(transcripts_data)} transcripts',
        'count': len(transcripts_data)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'transcripts_loaded': len(transcripts_data)})

if __name__ == '__main__':
    # Process transcripts on startup
    print("Processing DOCX files...")
    transcripts_data = process_docx_files('data')
    print(f"Loaded {len(transcripts_data)} transcripts")
    
    # Start Flask server
    print("Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
