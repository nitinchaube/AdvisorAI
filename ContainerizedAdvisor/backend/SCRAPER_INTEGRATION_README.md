# Job Scraper Integration with Flask App

## Overview

The job scraper has been integrated into the main Flask application (`app.py`) to run automatically in the background every 2 hours. This ensures that job and internship data is continuously updated without manual intervention.

## How It Works

### 1. Background Threading

- The scraper runs in a separate daemon thread to avoid blocking the Flask application
- Uses Python's `threading` module for concurrent execution
- The thread starts when the Flask app launches

### 2. Automatic Scheduling

- **Initial Run**: Scraper runs immediately when the Flask app starts
- **Recurring Runs**: Scraper runs every 2 hours (7200 seconds) automatically
- **Error Handling**: If a scraping cycle fails, the next cycle will still run

### 3. Integration Components

#### Functions Added to app.py:

- `run_background_scraper()`: Main background function that handles the scraping loop
- `start_background_scraper()`: Initializes and starts the background thread

#### API Endpoints Added:

- `GET /api/scraper/status`: Check if the background scraper is running
- `POST /api/scraper/trigger`: Manually trigger a scraping cycle

### 4. Error Handling

- Individual scraping errors don't stop the background thread
- All errors are logged using Python's logging module
- Critical errors are caught and logged without crashing the app

## Usage

### Starting the App

```bash
cd /path/to/backend
python app.py
```

The scraper will start automatically when the Flask app launches.

### Monitoring the Scraper

#### Check Status (requires JWT authentication):

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:5003/api/scraper/status
```

#### Manual Trigger (requires JWT authentication):

```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:5003/api/scraper/trigger
```

### Log Monitoring

The scraper logs are integrated with the Flask app logs. Look for these log messages:

- `🤖 Starting background job scraper...`
- `✅ Initial scraping completed`
- `🔄 Running scheduled job scraping...`
- `✅ Scheduled scraping completed`
- `❌ Error during scheduled scraping: ...`

## Files Modified

### Primary Integration:

- `app.py`: Main Flask application with integrated scraper

### Supporting Files:

- `github_jobs_unified_scraper.py`: The scraper class (unchanged)
- `run_unified_scraper.py`: Standalone runner (still works independently)

## Benefits

1. **Automated Data Updates**: Job data stays current without manual intervention
2. **Non-blocking Operation**: Flask app performance is not affected
3. **Error Resilience**: Scraper continues running even if individual cycles fail
4. **Manual Control**: Can manually trigger scraping via API when needed
5. **Monitoring**: Can check scraper status via API

## Technical Details

### Thread Configuration:

- **Type**: Daemon thread (dies when main process dies)
- **Interval**: 7200 seconds (2 hours)
- **Error Recovery**: Individual failures don't stop the thread

### Memory Management:

- Single scraper instance is reused across all cycles
- Thread cleanup is handled automatically by Python's threading module

### Dependencies:

- All existing scraper dependencies are maintained
- No additional packages required

## Troubleshooting

### Scraper Not Running:

1. Check Flask app logs for startup messages
2. Use `/api/scraper/status` endpoint to verify thread status
3. Check for import errors in the logs

### Scraping Failures:

1. Check logs for specific error messages
2. Verify internet connectivity
3. Check if GitHub repositories are accessible

### Performance Issues:

1. Monitor CPU usage during scraping cycles
2. Check log file sizes and rotate if necessary
3. Verify that scraping doesn't coincide with high Flask traffic

## Future Enhancements

Potential improvements could include:

- Configurable scraping intervals via environment variables
- More detailed status reporting (last run time, success rate)
- Database integration for storing scraper metrics
- Web-based dashboard for monitoring scraper status
