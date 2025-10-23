# NJ 2025 Gubernatorial Race Transcript Explorer

A web application for exploring political speech transcripts from New Jersey's 2025 gubernatorial race candidates.

## Quick Start

### Prerequisites
- Python 3.9+ with pip
- Modern web browser
- DOCX files in `/app/data/` directory

### Setup Steps

1. **Install Python Dependencies**
   ```bash
   pip3 install python-docx
   ```

2. **Prepare DOCX Files**
   - Place all DOCX transcript files in `/app/data/` directory
   - Files should be named with date and candidate info (e.g., "Aug 27 - Sherrill speech.docx")
   - Files should have a youtube.com link inside them

3. **Generate JSON Data**
   ```bash
   cd /app
   python3 convert_docx_to_json.py
   ```
   This creates `transcripts.json` with all transcript data, including YouTube URLs.

4. **Start Web Server**
   ```bash
   python3 -m http.server 8001
   ```

5. **Open Application**
   - Navigate to `http://localhost:8001`
   - Search for keywords in transcripts
   - Click "Watch" buttons to view YouTube videos

## File Structure

```
/app/
├── index.html              # Main HTML file
├── style.css              # CSS styling
├── script.js              # JavaScript application logic
├── transcripts.json        # Generated transcript data (JSON)
├── convert_docx_to_json.py # DOCX to JSON converter script
├── data/                  # Directory containing DOCX files
│   ├── Aug 27 - Sherrill speech.docx
│   ├── Sep 2 - Ciattarelli speech.docx
│   └── ... (40 total files)
├── ngram_frequencies_by_week.csv  # N-gram analysis data
└── ngram_summary.csv      # N-gram summary data
```

## Features

- **Search Functionality**: Search across all transcript text
- **Candidate Filtering**: Filter results by candidate (Sherrill/Ciattarelli)
- **YouTube Integration**: Direct links to video sources
- **N-gram Analysis**: Interactive charts showing term frequency over time
- **Responsive Design**: Works on desktop and mobile devices

## Updating Transcripts

When adding new DOCX files:

1. Add new DOCX files to `/app/data/` directory
2. Run `python3 convert_docx_to_json.py` to regenerate JSON
3. Refresh the web application

## Data Processing

The `convert_docx_to_json.py` script:
- Extracts text content from DOCX files
- Parses filenames for metadata (date, candidate, location)
- Extracts YouTube URLs from transcript text
- Cleans and normalizes text for analysis
- Generates structured JSON output

## Technical Notes

- **Data Source**: DOCX files → JSON (no CSV parsing issues)
- **YouTube URLs**: Automatically extracted from transcript text
- **N-gram Charts**: Plotly.js integration for interactive visualizations
- **Search**: Case-insensitive with keyword highlighting
- **Caching**: Browser caching may require hard refresh (Ctrl+F5)

## Troubleshooting

- **No YouTube buttons**: Check that `transcripts.json` contains `youtubeUrl` fields
- **Search not working**: Verify `transcripts.json` is accessible at `http://localhost:8001/transcripts.json`
- **Charts not showing**: Ensure `ngram_frequencies_by_week.csv` is present
- **CORS errors**: Use HTTP server (`http://localhost:8001`) not file protocol (`file://`)

## Development

To modify the application:
- Edit `script.js` for functionality changes
- Edit `style.css` for styling updates
- Edit `convert_docx_to_json.py` for data processing changes
- Regenerate JSON after DOCX changes: `python3 convert_docx_to_json.py`
