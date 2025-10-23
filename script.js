class TranscriptExplorer {
    constructor() {
        this.transcripts = [];
        this.filteredTranscripts = [];
        this.currentSearchTerm = '';
        this.currentTranscript = null;
        this.isSecondarySearch = false;
        this.ngramData = [];
        this.ngramSummary = [];
        
        this.initializeElements();
        this.bindEvents();
        this.loadTranscripts();
        this.loadNgramData();
    }

    initializeElements() {
        this.searchInput = document.getElementById('searchInput');
        this.clearSearchBtn = document.getElementById('clearSearch');
        this.filterSherrill = document.getElementById('filterSherrill');
        this.filterCiattarelli = document.getElementById('filterCiattarelli');
        this.searchResults = document.getElementById('searchResults');
        this.resultCount = document.getElementById('resultCount');
        this.transcriptView = document.getElementById('transcriptView');
        this.miniChart = document.getElementById('miniChart');
    }

    bindEvents() {
        // Search input with debouncing
        let searchTimeout;
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.handleSearch(e.target.value);
            }, 300);
        });

        // Clear search button
        this.clearSearchBtn.addEventListener('click', () => {
            this.clearSearch();
        });

        // Candidate filters
        this.filterSherrill.addEventListener('change', () => {
            this.applyFilters();
        });

        this.filterCiattarelli.addEventListener('change', () => {
            this.applyFilters();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSearch();
            }
        });
    }

    async loadTranscripts() {
        try {
            this.showLoading();
            
            const response = await fetch('transcripts.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const transcripts = await response.json();
            
            // Process and normalize the data
            this.transcripts = transcripts.map(row => ({
                date: row.date,
                candidate: this.normalizeCandidateName(row.candidate),
                location_or_title: row.location_or_title,
                transcript_text: row.transcript_text,
                youtubeUrl: row.youtubeUrl || '',
                youtubeId: row.youtubeId || ''
            })).filter(row => row.transcript_text && row.transcript_text.trim());

            this.filteredTranscripts = [...this.transcripts];
            this.hideLoading();
            
            console.log(`Loaded ${this.transcripts.length} transcripts`);
            
        } catch (error) {
            console.error('Error loading transcripts:', error);
            this.showError('Failed to load transcript data. Please check that the JSON file exists.');
        }
    }

    async loadNgramData() {
        try {
            // Load n-gram frequency data
            const response = await fetch('ngram_frequencies_by_week.csv');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const csvText = await response.text();
            const parsed = Papa.parse(csvText, {
                header: true,
                skipEmptyLines: true
            });

            this.ngramData = parsed.data.map(row => ({
                week: new Date(row.week),
                candidate: row.candidate,
                term: row.term,
                count: parseInt(row.count),
                total_words: parseInt(row.total_words),
                normalized_freq: parseFloat(row.normalized_freq),
                ngram_type: row.ngram_type
            }));

            // Load n-gram summary for reference
            const summaryResponse = await fetch('ngram_summary.csv');
            if (summaryResponse.ok) {
                const summaryText = await summaryResponse.text();
                const summaryParsed = Papa.parse(summaryText, {
                    header: true,
                    skipEmptyLines: true
                });

                this.ngramSummary = summaryParsed.data;
            }

            console.log(`Loaded ${this.ngramData.length} n-gram frequency records`);
            
        } catch (error) {
            console.error('Error loading n-gram data:', error);
        }
    }


    updateChart(selectedTerm) {
        if (!selectedTerm || !this.ngramData.length) return;

        // Filter data for selected term
        const termData = this.ngramData.filter(d => d.term === selectedTerm);
        
        if (termData.length === 0) {
            this.miniChart.innerHTML = '';
            return;
        }

        // Group by candidate
        const sherrillData = termData.filter(d => d.candidate === 'Sherrill');
        const ciattarelliData = termData.filter(d => d.candidate === 'Ciattarelli');

        // Create traces for each candidate
        const traces = [];

        if (sherrillData.length > 0) {
            traces.push({
                x: sherrillData.map(d => d.week),
                y: sherrillData.map(d => d.normalized_freq),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Sherrill',
                line: { color: '#007bff', width: 2 },
                marker: { size: 3 }
            });
        }

        if (ciattarelliData.length > 0) {
            traces.push({
                x: ciattarelliData.map(d => d.week),
                y: ciattarelliData.map(d => d.normalized_freq),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Ciattarelli',
                line: { color: '#dc3545', width: 2 },
                marker: { size: 3 }
            });
        }

        const layout = {
            xaxis: {
                showticklabels: false,
                showgrid: false,
                zeroline: false
            },
            yaxis: {
                showticklabels: false,
                showgrid: false,
                zeroline: false
            },
            margin: { t: 0, r: 0, b: 0, l: 0 },
            showlegend: false,
            plot_bgcolor: 'transparent',
            paper_bgcolor: 'transparent'
        };

        const config = {
            responsive: true,
            displayModeBar: false,
            staticPlot: true
        };

        Plotly.newPlot(this.miniChart, traces, layout, config);
    }

    checkAndShowChart(searchTerm) {
        if (!searchTerm || !this.ngramData.length) {
            this.hideChart();
            return;
        }

        // Normalize search term for matching
        const normalizedTerm = searchTerm.toLowerCase().trim();
        
        // Check if the search term exists in our n-gram data
        const matchingTerms = this.ngramData.filter(d => 
            d.term.toLowerCase() === normalizedTerm ||
            d.term.toLowerCase().includes(normalizedTerm) ||
            normalizedTerm.includes(d.term.toLowerCase())
        );

        if (matchingTerms.length > 0) {
            // Get the most relevant term (exact match first, then most frequent)
            const exactMatch = matchingTerms.find(d => d.term.toLowerCase() === normalizedTerm);
            const termToShow = exactMatch ? exactMatch.term : matchingTerms[0].term;
            
            this.showChart(termToShow);
        } else {
            this.hideChart();
        }
    }

    showChart(term) {
        this.updateChart(term);
    }

    hideChart() {
        this.miniChart.innerHTML = '';
    }

    normalizeCandidateName(candidate) {
        if (!candidate) return 'Unknown';
        
        const normalized = candidate.toLowerCase().trim();
        if (normalized.includes('sherrill') || normalized.includes('mikie')) {
            return 'Sherrill';
        } else if (normalized.includes('ciattarelli') || normalized.includes('jack')) {
            return 'Ciattarelli';
        }
        return candidate;
    }

    extractYouTubeUrl(text) {
        if (!text) return null;
        
        const youtubeRegex = /https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = text.match(youtubeRegex);
        return match ? match[0] : null;
    }

    extractYouTubeId(text) {
        if (!text) return null;
        
        const youtubeRegex = /https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = text.match(youtubeRegex);
        return match ? match[1] : null;
    }

    handleSearch(searchTerm) {
        this.currentSearchTerm = searchTerm.toLowerCase().trim();
        
        if (!this.currentSearchTerm) {
            this.clearSearch();
            return;
        }

        if (this.isSecondarySearch && this.currentTranscript) {
            this.searchWithinTranscript(this.currentSearchTerm);
        } else {
            this.searchAllTranscripts(this.currentSearchTerm);
        }
    }

    searchAllTranscripts(searchTerm) {
        this.isSecondarySearch = false;
        
        // Clear any existing highlights in the current transcript
        if (this.currentTranscript) {
            this.clearHighlights();
        }
        
        const results = [];
        
        this.filteredTranscripts.forEach((transcript, index) => {
            const text = transcript.transcript_text.toLowerCase();
            const searchIndex = text.indexOf(searchTerm);
            
            if (searchIndex !== -1) {
                const excerpt = this.createExcerpt(transcript.transcript_text, searchTerm);
                results.push({
                    ...transcript,
                    excerpt,
                    searchIndex,
                    originalIndex: index
                });
            }
        });

        // Sort results by date (most recent first)
        results.sort((a, b) => new Date(b.date) - new Date(a.date));

        this.displaySearchResults(results);
        
        // Show chart if search term exists in n-gram data
        this.checkAndShowChart(searchTerm);
    }

    searchWithinTranscript(searchTerm) {
        if (!this.currentTranscript) return;
        
        const text = this.currentTranscript.transcript_text.toLowerCase();
        const searchIndex = text.indexOf(searchTerm);
        
        if (searchIndex !== -1) {
            this.highlightTextInTranscript(searchTerm);
        } else {
            this.clearHighlights();
        }
    }

    createExcerpt(text, searchTerm, contextLength = 150) {
        const searchIndex = text.toLowerCase().indexOf(searchTerm.toLowerCase());
        
        if (searchIndex === -1) return text.substring(0, 200) + '...';
        
        const start = Math.max(0, searchIndex - contextLength);
        const end = Math.min(text.length, searchIndex + searchTerm.length + contextLength);
        
        let excerpt = text.substring(start, end);
        
        // Add ellipsis if we're not at the beginning/end
        if (start > 0) excerpt = '...' + excerpt;
        if (end < text.length) excerpt = excerpt + '...';
        
        return excerpt;
    }

    displaySearchResults(results) {
        this.resultCount.textContent = `${results.length} result${results.length !== 1 ? 's' : ''}`;
        
        // Clear any previous selected states
        this.searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        if (results.length === 0) {
            this.searchResults.innerHTML = `
                <div class="no-results">
                    <p>No results found for "${this.currentSearchTerm}"</p>
                </div>
            `;
            return;
        }

        this.searchResults.innerHTML = results.map((result, index) => `
            <div class="search-result-item" data-index="${result.originalIndex}">
                <div class="result-header">
                    <div class="result-title">${this.escapeHtml(result.location_or_title)}</div>
                    <div class="result-date">${this.formatDate(result.date)}</div>
                </div>
                <div class="result-candidate">
                    <span class="candidate-tag ${result.candidate.toLowerCase()}">${result.candidate}</span>
                </div>
                <div class="result-excerpt">${this.highlightText(result.excerpt, this.currentSearchTerm)}</div>
            </div>
        `).join('');

        // Add click handlers to result items
        this.searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.displayTranscript(this.filteredTranscripts[index]);
                
                // Update selected state
                this.searchResults.querySelectorAll('.search-result-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
            });
        });
    }

    displayTranscript(transcript) {
        this.currentTranscript = transcript;
        this.isSecondarySearch = true;
        
        
        const transcriptHtml = `
            <div class="transcript-header">
                <h2 class="transcript-title">${this.escapeHtml(transcript.location_or_title)}</h2>
                <div class="transcript-meta">
                    <div class="transcript-date">${this.formatDate(transcript.date)}</div>
                    ${transcript.youtubeUrl ? `
                        <a href="${transcript.youtubeUrl}" target="_blank" rel="noopener noreferrer" class="watch-button">
                            Watch
                        </a>
                    ` : ''}
                    <div class="result-candidate">
                        <span class="candidate-tag ${transcript.candidate.toLowerCase()}">${transcript.candidate}</span>
                    </div>
                </div>
                ${transcript.youtubeId ? `
                    <div class="youtube-thumbnail">
                        <a href="${transcript.youtubeUrl}" target="_blank" rel="noopener noreferrer">
                            <img src="https://img.youtube.com/vi/${transcript.youtubeId}/0.jpg" 
                                 alt="YouTube video thumbnail" 
                                 title="Click to view on YouTube">
                        </a>
                    </div>
                ` : ''}
            </div>
            <div class="transcript-text" id="transcriptText">
                ${this.escapeHtml(transcript.transcript_text)}
            </div>
        `;
        
        this.transcriptView.innerHTML = transcriptHtml;
        
        // Scroll to top of transcript
        this.transcriptView.scrollTop = 0;
        
        // If there's a current search term, highlight it in the transcript
        if (this.currentSearchTerm) {
            this.highlightTextInTranscript(this.currentSearchTerm);
        }
    }

    highlightTextInTranscript(searchTerm) {
        const transcriptElement = document.getElementById('transcriptText');
        if (!transcriptElement) return;
        
        const text = transcriptElement.textContent;
        const highlightedText = this.highlightText(text, searchTerm);
        transcriptElement.innerHTML = highlightedText;
        
        // Scroll to first highlight
        const firstHighlight = transcriptElement.querySelector('.highlight');
        if (firstHighlight) {
            firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    highlightText(text, searchTerm) {
        if (!searchTerm) return this.escapeHtml(text);
        
        const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
        return this.escapeHtml(text).replace(regex, '<span class="highlight">$1</span>');
    }

    clearHighlights() {
        const transcriptElement = document.getElementById('transcriptText');
        if (!transcriptElement) return;
        
        const text = transcriptElement.textContent;
        transcriptElement.innerHTML = this.escapeHtml(text);
    }

    applyFilters() {
        const showSherrill = this.filterSherrill.checked;
        const showCiattarelli = this.filterCiattarelli.checked;
        
        this.filteredTranscripts = this.transcripts.filter(transcript => {
            if (transcript.candidate === 'Sherrill' && showSherrill) return true;
            if (transcript.candidate === 'Ciattarelli' && showCiattarelli) return true;
            return false;
        });
        
        // Re-run current search if there is one
        if (this.currentSearchTerm && !this.isSecondarySearch) {
            this.searchAllTranscripts(this.currentSearchTerm);
        }
    }

    clearSearch() {
        this.currentSearchTerm = '';
        this.isSecondarySearch = false;
        this.searchInput.value = '';
        
        this.searchResults.innerHTML = `
            <div class="no-results">
                <p>Enter a search term to explore political speech transcripts</p>
            </div>
        `;
        
        this.resultCount.textContent = '0 results';
        
        // Clear highlights in current transcript
        if (this.currentTranscript) {
            this.clearHighlights();
        }
        
        // Show welcome message when clearing search
        this.showWelcomeMessage();
        
        // Hide chart when clearing search
        this.hideChart();
        
        // Remove selected state from all result items
        this.searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.classList.remove('selected');
        });
    }

    showLoading() {
        this.transcriptView.innerHTML = `
            <div class="loading">
                Loading transcripts...
            </div>
        `;
    }

    hideLoading() {
        // Show welcome message when data is loaded but no search performed
        this.showWelcomeMessage();
    }

    showWelcomeMessage() {
        this.transcriptView.innerHTML = `
            <div class="welcome-message">
                <h2>Political Speech Explorer</h2>
                <p>Search for keywords in political speech transcripts from New Jersey's 2025 gubernatorial race.</p>
                <div class="features">
                    <h3>How to get started:</h3>
                    <ul>
                        <li><strong>Search for topics</strong> - Try keywords like "education", "energy", "taxes", or "healthcare"</li>
                        <li><strong>Filter by candidate</strong> - Use the checkboxes to show Sherrill or Ciattarelli speeches</li>
                        <li><strong>View full transcripts</strong> - Click any search result to read the complete speech</li>
                        <li><strong>Watch videos</strong> - Click YouTube thumbnails to view the original speeches</li>
                        <li><strong>Search within transcripts</strong> - After opening a transcript, search for specific terms within it</li>
                    </ul>
                    <div class="search-tips">
                        <h4>💡 Search Tips:</h4>
                        <p>• Try searching for policy topics, names, or specific issues<br>
                        • Use the "Clear" button to reset your search<br>
                        • Press Escape to quickly clear the search bar</p>
                    </div>
                </div>
            </div>
        `;
    }

    showError(message) {
        this.transcriptView.innerHTML = `
            <div class="error">
                <h2>Error</h2>
                <p>${message}</p>
            </div>
        `;
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown date';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return dateString;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TranscriptExplorer();
});
