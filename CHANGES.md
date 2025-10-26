# HW4 Part 2 - County Data API

## Project Description
A REST API built with Flask and deployed on Vercel that provides access to county health data from a SQLite database.

## API Endpoints

### County Data Endpoint
- **POST** `/api/county_data` and `/county_data`
  - Accepts JSON body with `zip` (5-digit string) and `measure_name`
  - Returns health data for the specified zip code and measure
  - Special query parameter: `coffee=teapot` returns HTTP 418

### List Endpoints  
- **GET/POST** `/api/obesity`, `/api/poverty`, `/api/fpm`
- Also available without `/api` prefix
- Alternative paths: `/@../obesity.json`, `/@../poverty.json`, `/@../fpm.json`
- All return JSON arrays

## Files Structure
- `api/county_data.py` - Main API endpoint
- `api/static_lists.py` - List endpoints for obesity, poverty, and FPM data
- `csv_to_sqlite.py` - Tool to import CSV data into SQLite database
- `requirements.txt` - Python dependencies
- `vercel.json` - Vercel deployment configuration

## Data Files
- `data.db` - SQLite database containing county health rankings and zip code data
- `obesity.json`, `poverty.json`, `fpm.json` - JSON data files for list endpoints

