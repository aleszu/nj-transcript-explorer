#!/usr/bin/env python3
"""
Generate ngram_frequencies_by_week.csv from transcripts.json or DOCX files.

This script analyzes political transcripts and generates n-gram frequency data
grouped by week and candidate. It supports both 1-grams (single words), 
2-grams (word pairs), and 3-grams (word triplets).

Usage examples:
    # Basic usage - generate from transcripts.json
    python3 generate_ngram_frequencies.py
    
    # Generate from DOCX files directly
    python3 generate_ngram_frequencies.py --use-docx
    
    # Filter to specific terms only (create a terms.txt file with one term per line)
    python3 generate_ngram_frequencies.py --terms-file terms.txt
    
    # Only include terms that appear at least 2 times
    python3 generate_ngram_frequencies.py --min-freq 2
    
    # Custom output file
    python3 generate_ngram_frequencies.py --output my_ngrams.csv
"""

import json
import csv
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    print("Warning: python-docx not installed. Will only work with transcripts.json")


def get_week_start(date_str: str) -> str:
    """Get the Sunday of the week for a given date.
    
    Args:
        date_str: Date string in format YYYY-MM-DD
        
    Returns:
        Date string for Sunday of that week (YYYY-MM-DD)
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Get Sunday of the week (Sunday = 6, Monday = 0)
        # weekday() returns 0-6 where Monday=0, so Sunday=6
        weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
        # Convert to Sunday-based: Sunday=0, Monday=1, ..., Saturday=6
        days_since_sunday = (weekday + 1) % 7
        sunday = date_obj - timedelta(days=days_since_sunday)
        return sunday.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def clean_text(text: str) -> str:
    """Clean text for ngram extraction."""
    if not text:
        return ""
    
    # Remove YouTube URLs
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[^\s]+',
        r'https?://youtu\.be/[^\s]+',
        r'https?://(?:www\.)?youtube\.com/embed/[^\s]+',
    ]
    for pattern in youtube_patterns:
        text = re.sub(pattern, '', text)
    
    # Remove brackets and parentheses content (e.g., [laughter], (inaudible))
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    
    # Remove HTML entities
    text = text.replace('&#39;', "'")
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_ngrams(text: str, n: int) -> List[str]:
    """Extract n-grams from text.
    
    Args:
        text: Input text
        n: Size of n-gram (1, 2, or 3)
        
    Returns:
        List of n-gram strings
    """
    # Clean and tokenize
    text = clean_text(text.lower())
    
    # Remove punctuation but keep spaces for word boundaries
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Split into words and filter out empty strings
    words = [w.strip() for w in text.split() if w.strip()]
    
    if len(words) < n:
        return []
    
    # Generate n-grams
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.append(ngram)
    
    return ngrams


def load_transcripts_from_json(json_path: str) -> List[Dict]:
    """Load transcripts from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_transcripts_from_docx(data_dir: str) -> List[Dict]:
    """Load transcripts from DOCX files in directory."""
    if not HAS_DOCX:
        raise ImportError("python-docx is required to process DOCX files. Install with: pip install python-docx")
    
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Directory {data_dir} does not exist")
    
    transcripts = []
    
    # Reuse the parsing logic from convert_docx_to_json.py
    def extract_date_from_filename(filename):
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07',
            'aug': '08', 'august': '08',
            'sep': '09', 'sept': '09', 'september': '09',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12'
        }
        date_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(\d+)'
        match = re.search(date_pattern, filename.lower())
        if match:
            month_abbr = match.group(1)
            day = match.group(2).zfill(2)
            month_num = month_map.get(month_abbr, '12')
            return f"2025-{month_num}-{day}"
        return "2025-01-01"
    
    def parse_filename_for_metadata(filename):
        name_without_ext = filename.replace('.docx', '')
        if name_without_ext.startswith(('Oct ', 'Sep ', 'Sept ', 'Aug ', 'Jul ', 'Jun ', 'May ', 'Apr ', 'Mar ', 'Feb ', 'Jan ', 'Dec ', 'Nov ')):
            parts = name_without_ext.split(' - ', 1)
            if len(parts) == 2:
                date_part = parts[0]
                name_part = parts[1]
                name_parts = name_part.split('_')
                if len(name_parts) >= 2:
                    candidate = name_parts[0]
                    location = '_'.join(name_parts[1:-1]) if len(name_parts) > 2 else name_parts[1]
                    return candidate, location, date_part
                else:
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
        
        if 'sherrill' in filename.lower():
            candidate = 'Sherrill'
        elif 'ciattarelli' in filename.lower():
            candidate = 'Ciattarelli'
        else:
            candidate = 'Unknown'
        
        date_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d+)', name_without_ext.lower())
        if date_match:
            date_part = f"{date_match.group(1).title()} {date_match.group(2)}"
        else:
            date_part = "Unknown"
        
        location = name_without_ext.replace(candidate, '').strip('_').strip('-').strip()
        return candidate, location, date_part
    
    def extract_text_from_docx(file_path):
        try:
            doc = Document(file_path)
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return ""
    
    # Process all DOCX files
    docx_files = [f for f in data_path.glob("*.docx") if not f.name.startswith("~$")]
    
    for docx_file in sorted(docx_files):
        try:
            candidate, location, date = parse_filename_for_metadata(docx_file.name)
            iso_date = extract_date_from_filename(date)
            text_content = extract_text_from_docx(docx_file)
            
            transcripts.append({
                'date': iso_date,
                'candidate': candidate,
                'location_or_title': location,
                'transcript_text': text_content
            })
        except Exception as e:
            print(f"Error processing {docx_file.name}: {str(e)}")
    
    return transcripts


def count_words(text: str) -> int:
    """Count words in text."""
    text = clean_text(text)
    words = [w.strip() for w in text.split() if w.strip()]
    return len(words)


def generate_ngram_frequencies(
    transcripts: List[Dict],
    target_terms: Optional[List[str]] = None,
    min_frequency: int = 1
) -> List[Dict]:
    """Generate ngram frequency data grouped by week and candidate.
    
    Args:
        transcripts: List of transcript dictionaries
        target_terms: Optional list of terms to filter (if None, include all)
        min_frequency: Minimum frequency to include a term
        
    Returns:
        List of dictionaries with ngram frequency data
    """
    # Group transcripts by week and candidate
    week_data = defaultdict(lambda: {'texts': [], 'total_words': 0})
    
    for transcript in transcripts:
        date = transcript.get('date', '')
        candidate = transcript.get('candidate', 'Unknown')
        text = transcript.get('transcript_text', '')
        
        if not date or not candidate or not text:
            continue
        
        week = get_week_start(date)
        key = (week, candidate)
        
        week_data[key]['texts'].append(text)
    
    # Calculate total words for each week/candidate
    for key, data in week_data.items():
        combined_text = ' '.join(data['texts'])
        data['total_words'] = count_words(combined_text)
    
    # Extract ngrams and count frequencies
    results = []
    
    for (week, candidate), data in week_data.items():
        combined_text = ' '.join(data['texts'])
        total_words = data['total_words']
        
        if total_words == 0:
            continue
        
        # Extract ngrams for 1, 2, and 3 grams
        for n in [1, 2, 3]:
            ngrams = extract_ngrams(combined_text, n)
            ngram_counts = Counter(ngrams)
            
            # Filter by target_terms if provided
            if target_terms:
                # For ngrams, check if any target term appears in the ngram
                if n == 1:
                    # For 1-grams, check exact match
                    filtered_counts = {
                        term: count for term, count in ngram_counts.items()
                        if term.lower() in [t.lower() for t in target_terms]
                    }
                else:
                    # For multi-word ngrams, check if any target term appears
                    filtered_counts = {
                        term: count for term, count in ngram_counts.items()
                        if any(t.lower() in term.lower() for t in target_terms)
                    }
            else:
                filtered_counts = ngram_counts
            
            # Add to results
            for term, count in filtered_counts.items():
                if count >= min_frequency:
                    normalized_freq = (count / total_words) * 1000 if total_words > 0 else 0
                    
                    results.append({
                        'week': week,
                        'candidate': candidate,
                        'term': term,
                        'count': count,
                        'total_words': total_words,
                        'normalized_freq': normalized_freq,
                        'ngram_type': f'{n}-gram'
                    })
    
    # Sort results
    results.sort(key=lambda x: (x['week'], x['candidate'], x['ngram_type'], x['term']))
    
    return results


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate ngram frequencies CSV from transcripts')
    parser.add_argument(
        '--json',
        default='transcripts.json',
        help='Path to transcripts.json file (default: transcripts.json)'
    )
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Path to directory with DOCX files (default: data)'
    )
    parser.add_argument(
        '--output',
        default='ngram_frequencies_by_week.csv',
        help='Output CSV file (default: ngram_frequencies_by_week.csv)'
    )
    parser.add_argument(
        '--terms-file',
        help='Optional file with target terms (one per line)'
    )
    parser.add_argument(
        '--min-freq',
        type=int,
        default=1,
        help='Minimum frequency to include a term (default: 1)'
    )
    parser.add_argument(
        '--use-docx',
        action='store_true',
        help='Use DOCX files instead of JSON (requires python-docx)'
    )
    
    args = parser.parse_args()
    
    # Load target terms if provided
    target_terms = None
    if args.terms_file:
        with open(args.terms_file, 'r', encoding='utf-8') as f:
            target_terms = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(target_terms)} target terms from {args.terms_file}")
    
    # Load transcripts
    if args.use_docx:
        print(f"Loading transcripts from DOCX files in {args.data_dir}...")
        transcripts = load_transcripts_from_docx(args.data_dir)
    else:
        json_path = Path(args.json)
        if not json_path.exists():
            print(f"Warning: {args.json} not found. Trying DOCX files...")
            transcripts = load_transcripts_from_docx(args.data_dir)
        else:
            print(f"Loading transcripts from {args.json}...")
            transcripts = load_transcripts_from_json(args.json)
    
    print(f"Loaded {len(transcripts)} transcripts")
    
    # Generate ngram frequencies
    print("Generating ngram frequencies...")
    results = generate_ngram_frequencies(
        transcripts,
        target_terms=target_terms,
        min_frequency=args.min_freq
    )
    
    print(f"Generated {len(results)} ngram frequency records")
    
    # Write to CSV
    print(f"Writing to {args.output}...")
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        if results:
            fieldnames = ['week', 'candidate', 'term', 'count', 'total_words', 'normalized_freq', 'ngram_type']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    print(f"✅ Successfully wrote {len(results)} records to {args.output}")
    
    # Print summary
    weeks = sorted(set(r['week'] for r in results))
    candidates = sorted(set(r['candidate'] for r in results))
    
    print(f"\nSummary:")
    print(f"  Weeks: {len(weeks)} ({weeks[0]} to {weeks[-1]})")
    print(f"  Candidates: {', '.join(candidates)}")
    print(f"  Total records: {len(results)}")


if __name__ == "__main__":
    main()

