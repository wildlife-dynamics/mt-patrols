# MT Patrols Workflow

## Introduction

This workflow helps you to process, visualize, and summarize SMART patrol data for the Mara Triangle conservancy.

**What this workflow does:**
- Loads patrol observation data from a file (Parquet, CSV, GeoJSON, GeoPackage, or Shapefile)
- Processes observations by converting timezones, filtering coordinates, and building trajectory segments
- Generates interactive maps showing patrol trajectories color-coded by station
- Summarizes patrol activity by transport type, mandate, station, and individual ranger
- Creates bar charts comparing station-level distance and duration
- Exports data and summary tables in multiple formats (CSV, Parquet, GeoParquet, GPKG)
- Generates a Word (.docx) report with maps, charts, and summary tables

**Who should use this:**
- Conservation managers monitoring ranger patrol coverage in the Mara Triangle
- Operations staff tracking patrol effort by station, mandate, or transport type
- Anyone needing to visualize and report on SMART patrol trajectory data

---

## Prerequisites

Before using this workflow, you need:

1. **Ecoscope Desktop** installed on your computer
   - If you haven't installed it yet, please follow the installation instructions for Ecoscope Desktop

2. **Patrol observation data** exported as a supported file format
   - Supported formats: Parquet, GeoParquet, GeoJSON, JSON, GeoPackage, CSV, or Shapefile
   - The file should contain patrol relocation data with columns such as `fixtime`, `patrol_id`, `station`, `patrol_mandate`, `patrol_transport`, and `patrol_leader_name`
   - You'll need to know the full file path on your computer

3. **A Word template file** (.docx) for report generation
   - This template uses Jinja2 placeholders to insert maps, charts, and tables
   - A default template is provided with the workflow in the `resources/templates/` folder

---

## Installation

1. Select "Workflow Templates" tab
2. Click "+ Add Template"
3. Copy and paste this URL https://github.com/wildlife-dynamics/mt-patrols and wait for the workflow template to be downloaded and initialized
4. The template will now appear in your available template list

---

## Configuration Guide

### Basic Configuration

#### 1. Workflow Details
Add information that will help to differentiate this workflow from another.

- **Workflow Name** (required): A name to identify this workflow run
  - Example: `"MT Patrols"`
- **Workflow Description** (optional): A short description of the workflow
  - Example: `"SMART patrol trajectories workflow"`

#### 2. Time Range
Choose the period of time to analyze.

- **Since** (required): The start date and time for the analysis period
  - Example: `2026-02-01T00:00:00Z`
- **Until** (required): The end date and time for the analysis period
  - Example: `2026-02-28T23:59:59Z`
- **Timezone** (optional): The timezone to use for displaying dates and times in outputs. If not set, times remain in UTC.
  - Example: `Africa/Nairobi (UTC+03:00)`

#### 3. Load Patrol Observations
Provide the patrol observation data file to process.

- **File Path** (required): The full path to the file on your computer
  - Example: `"/Users/you/data/mt_patrol_reloc.parquet"`
  - Supported formats: `.parquet`, `.geoparquet`, `.geojson`, `.json`, `.gpkg`, `.csv`, `.shp`
- **Layer** (optional, advanced): Layer name for GeoPackage files. Only needed if your `.gpkg` file contains multiple layers.

#### 4. Persist Patrol Trajectories
Choose the output format(s) for your processed patrol trajectory data.

- **Filetypes** (optional): Select one or more output formats
  - Default: `["parquet"]`
  - Options: `csv`, `parquet`

#### 5. Create Patrol Report
Configure the Word report output.

- **Template Path** (required): Path or URL to the Word template (.docx) file with Jinja2 placeholders
  - Example: `/Users/you/mt-patrols/resources/templates/mt_patrols_report_template.docx`
  - Note: Supports both local file paths and remote URLs (http://, https://)

### Advanced Configuration

These optional settings provide additional control over your workflow:

#### Trajectory Segment Filter
Filter track data by setting limits on segment length, duration, and speed. Segments outside these bounds are removed, reducing noise and focusing on meaningful movement patterns.

- **Minimum Segment Length (Meters)**: Default `0.001`
- **Maximum Segment Length (Meters)**: Default `100000`
- **Minimum Segment Duration (Seconds)**: Default `1`
- **Maximum Segment Duration (Seconds)**: Default `172800` (48 hours)
- **Minimum Segment Speed (km/h)**: Default `0.01`
- **Maximum Segment Speed (km/h)**: Default `500`

#### Base Maps
Select tile layers to use as base layers in map outputs. The first layer in the list will be the bottommost layer displayed.

- **Preset options**: Open Street Map, Roadmap, Satellite, Terrain, LandDx, USGS Hillshade
- **Custom Layer (Advanced)**: Provide the URL of a publicly accessible tiled raster service
- Default: Terrain (World Topo Map)

---

## Running the Workflow

Once you've configured all the settings:

1. **Review your configuration**
   - Double-check your time range, file path, and template path

2. **Save and run**
   - Click "Submit" and the workflow will show up in the "My Workflows" table
   - Click "Run" and the workflow will begin processing

3. **Monitor progress and wait for completion**
   - You'll see status updates as the workflow runs
   - Processing time depends on:
     - The size of your date range
     - Number of patrol observations in the file
     - Number of stations and patrols
   - The workflow completes with status "Success" or "Failed"

---

## Understanding Your Results

After the workflow completes successfully, you'll find your outputs in the designated output folder.

### Data Outputs

#### Patrol Trajectory Data
Processed patrol trajectories saved in the format(s) you selected.

- **File formats**: CSV, Parquet, GeoParquet, and/or GPKG (based on your selection)
- **Opens in**: Microsoft Excel, Google Sheets (CSV), Python/R (Parquet/GeoParquet), QGIS/ArcGIS (GPKG)
- **Contents**: Each row represents a trajectory segment between two consecutive patrol relocations
  - `segment_start`: Start time of the segment
  - `timespan_seconds`: Duration of the segment in seconds
  - `speed_kmhr`: Speed during the segment in km/h
  - `dist_meters`: Distance of the segment in meters
  - `station`: The station the patrol belongs to
  - `patrol_mandate`: The mandate type of the patrol
  - `patrol_transport`: The transport mode used
  - `patrol_id`: Unique identifier for the patrol
  - `patrol_leader_name`: Name of the patrol leader

#### Summary Tables (CSV)
Three summary tables are exported:

- **Transport Summary**: Patrol count, total distance (km), and total duration (hours) grouped by transport type
- **Mandate Summary**: Patrol count, total distance (km), and total duration (hours) grouped by mandate type
- **Ranger Summary**: Patrol count, total distance (km), and total duration (hours) per ranger leader, split by station

### Visual Outputs

#### Patrol Trajectory Maps
- **Format**: Interactive HTML maps (one per patrol mandate group)
- **Features**:
  - Polyline layers showing patrol paths, color-coded by station
  - Hover tooltips showing Start Time, Duration (s), and Speed (kph) for each segment
  - Configurable base map layer (default: Terrain)
  - North arrow and legend

#### Station Bar Chart
- **Format**: Interactive bar chart
- **Features**:
  - X-axis: Station name
  - Bars: Total Distance (km) in green, Total Duration (hours) in blue
  - Hover: Shows exact values for each station

### Report Output

#### Word Report (.docx)
A formatted Word document containing:
- Report date range
- Patrol trajectory maps (as images)
- Station bar chart (as image)
- Transport summary table
- Mandate summary table
- Ranger summary tables

---

## Common Use Cases & Examples

Here are some typical scenarios and how to configure the workflow for each:

### Example 1: Monthly Patrol Summary
**Goal**: Generate a complete patrol report for February 2026.

**Configuration**:
- **Workflow Name**: `"MT Patrols"`
- **Workflow Description**: `"SMART patrol trajectories workflow"`
- **Time Range**:
  - Since: `2026-02-01T00:00:00Z`
  - Until: `2026-02-28T23:59:59Z`
- **File Path**: `"/path/to/mt_patrol_reloc.parquet"`
- **Template Path**: `/path/to/mt_patrols_report_template.docx`
- **Filetypes**: `["parquet"]`

**Result**:
- Patrol trajectory maps grouped by mandate
- Summary tables for transport types, mandates, and rangers
- Bar chart comparing distance and duration across stations
- A Word report combining all outputs

---


## Troubleshooting

### Common Issues and Solutions

#### Workflow Fails to Start
**Problem**: The workflow does not begin processing after clicking "Run".

**Solutions**:
- Verify that Ecoscope Desktop is running and up to date
- Check that all required fields are filled in (Workflow Name, Time Range, File Path, Template Path)
- Restart Ecoscope Desktop and try again

#### File Not Found Error
**Problem**: The workflow fails with a "file not found" error.

**Solutions**:
- Verify the file path is correct and the file exists at the specified location
- Check that the file extension matches a supported format (`.parquet`, `.geoparquet`, `.geojson`, `.json`, `.gpkg`, `.csv`, `.shp`)
- Ensure you have read permissions for the file
- Use the full absolute path, not a relative path

#### No Data in Results
**Problem**: The workflow completes but outputs are empty or missing.

**Solutions**:
- Confirm that your time range covers the period when patrol data was collected
- Check that the input file contains data within your specified time range
- Verify the input file has the expected columns (`fixtime`, `patrol_id`, `station`, etc.)

#### Maps Are Empty or Missing
**Problem**: The patrol trajectory maps show no data or are not generated.

**Solutions**:
- Check that patrol observations have valid GPS coordinates (not at 0,0 or 180,90)
- The workflow automatically filters out known invalid coordinates (0,0), (1,1), and (180,90)
- Verify that trajectory segments pass the segment filter criteria (length, duration, speed)
- Try relaxing the trajectory segment filter settings under Advanced Configuration

#### Workflow Runs Very Slowly
**Problem**: The workflow takes much longer than expected.

**Solutions**:
- Large date ranges with many patrols will take longer to process
- The first run after installation may be slower as the environment initializes ("warm-up")
- Try running with a smaller date range first to verify the configuration works
- Consider splitting very large datasets into smaller time periods

#### Word Report Generation Fails
**Problem**: The workflow fails at the "Create Patrol Report" step.

**Solutions**:
- Verify the template path points to a valid `.docx` file
- If using a URL, ensure it is accessible and points to a valid Word document
- Check that the template file is not open in another application
- Try using the default template provided in `resources/templates/`

#### Unexpected Trajectory Segments
**Problem**: The maps show unrealistic patrol routes (very long or fast segments).

**Solutions**:
- Adjust the Trajectory Segment Filter under Advanced Configuration
- Lower the **Maximum Segment Speed** to filter out GPS jumps (e.g., set to `80` km/h for foot/vehicle patrols)
- Lower the **Maximum Segment Length** to remove unrealistically long segments
- Lower the **Maximum Segment Duration** to remove segments with large time gaps
