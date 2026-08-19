# MT Patrols Workflow

## Introduction

This workflow helps you to process, visualize, and summarize ranger patrol activity for the Mara Triangle and the Maasai Mara National Reserve using patrol data stored in **EarthRanger**.

**What this workflow does:**
- Downloads patrols, patrol observations, and **patrol_info** events from your EarthRanger site
- Enriches each patrol with its ranger, team, mandate, and transport attributes from the **patrol_info** event
- Assigns every patrol to a patrol area (**Mara Triangle** or **Reserve**) based on its patrol type
- Builds patrol trajectories and generates interactive maps for each patrol area and mandate, color-coded by team
- Summarizes patrol effort (distance and duration) by transport type, mandate, and team for each area
- Creates bar charts comparing team-level distance and duration per area
- Lists individual ranger totals per team in each area
- Exports data and summary tables (CSV, Parquet)
- Generates a Word (.docx) report with three chapters: Trajectory Maps, Patrol Summary, and Ranger Summary

**Who should use this:**
- Conservation managers monitoring ranger patrol coverage in the Mara Triangle and the Reserve
- Operations staff tracking patrol effort by team, mandate, or transport type
- Anyone needing a recurring patrol activity report from EarthRanger patrol data

---

## Prerequisites

Before using this workflow, you need:

1. **Ecoscope Desktop** installed on your computer
   - If you haven't installed it yet, please follow the installation instructions for Ecoscope Desktop

2. **EarthRanger Data Source** configured in Ecoscope Desktop
   - You must have already set up a connection to your EarthRanger server
   - Your data source should be configured with proper authentication credentials
   - You'll need to know the name of your configured data source (e.g., `"mmnr"`)

3. **Patrols with `patrol_info` events** set up in EarthRanger
   - Each patrol should have a **patrol_info** event attached that records the ranger name, patrol leader, team members, team name, mandate, and transport
   - Patrols without a **patrol_info** event still appear in the report with their attributes shown as `Unknown`
   - Patrol types must follow the site's naming convention that distinguishes Mara Triangle patrol types from Reserve patrol types (e.g., `law_enforcement_reserve` for the Reserve)
   - You can review patrol and event types at `https://<your-site>.pamdas.org/admin/activity/eventtype/`

4. **A Word template file** (.docx) for report generation
   - This template uses Jinja2 placeholders to insert maps, charts, and tables
   - A default template is provided with the workflow in the `resources/templates/` folder and is preconfigured — you only need to change it for a custom report design

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
  - Example: `"Mara Triangle Patrol Report"`
- **Workflow Description** (optional): A short description of the workflow
  - Example: `"Patrol activity from EarthRanger (mmnr)"`

#### 2. Data Source
Select the EarthRanger connection to pull patrol data from.

- **Data Source** (required): The name of your configured EarthRanger data source
  - Example: `"mmnr"`
  - Note: The **patrol_info** event type must exist on the selected server

#### 3. Time Range
Set the reporting period. Patrols overlapping this range are included, and observations are truncated to the range.

- **Since**: `2026-07-01T00:00:00`
- **Until**: `2026-07-31T23:59:59`
- **Timezone**: `Africa/Nairobi (UTC+03:00)`
  - Note: All report dates and times are shown in the timezone you select here

#### 4. Report Scope
Choose which areas the report covers.

- **Report Scope** (required): One of:
  - `"Mara Triangle & Reserve"` (default) — both areas, each as its own subsection in every chapter
  - `"Mara Triangle only"`
  - `"Reserve only"`

#### 5. Persist Patrol Trajectories
Choose the file format(s) for the trajectory data export.

- **Filetypes**: `parquet` (default) and/or `csv`
  - **CSV**: Quick review in spreadsheets
  - **Parquet**: Efficient for large datasets, programmatic analysis

#### 6. Create Patrol Report
Controls the final Word report.

- **Template Path**: The report template to use
  - Default: the template bundled with this workflow (leave unchanged unless you have a custom template)
- **Skip** (advanced): Skip report generation entirely
- **Missing Text** (advanced): Text inserted where a report item has no data

### Advanced Configuration

These optional settings provide additional control over your workflow:

#### Patrol Type Lists (Report Scope)
The workflow decides whether a patrol belongs to the Mara Triangle or the Reserve by its patrol type. The two lists are prefilled with the standard **mmnr** patrol type values.

- **Mara Triangle Patrol Types**: Patrol type values counted as Mara Triangle
  - Default includes: `rhino_monitoring_patrol`, `general_law_enforcement`, `anti_harass_patrol`, `community_outreach`, `k9_deploy`, `rabies_vaccine`, and their vehicle variants
- **Reserve Patrol Types**: Patrol type values counted as Reserve
  - Default includes: `rhino_monitor_patrol_reserve`, `rhino_monitoring_veh_patrol_reserve`, `law_enforcement_veh_reserve`, `anti_harass_veh_reserve`
  - Note: Enter the patrol type *value* (not the display name), one per field. Patrols whose type is in neither list are excluded from the report

#### Trajectory Segment Filter (Process Patrol Observations)
Removes implausible trajectory segments before distance and duration are calculated.

- **Trajectory Segment Filter**: Bounds on segment length, duration, and speed
  - Default: `0.001–10000 m`, `1 s – 48 h`, `0.01–500 km/h`

#### Base Maps (Generate Maps)
The background map used behind patrol trajectories.

- **Base Maps**: Default is the ArcGIS World Topo basemap; you can add other tile URLs

---

## Running the Workflow

Once you've configured all the settings:

1. **Review your configuration**
   - Double-check your time range, data source, and report scope

2. **Save and run**
   - Click the "Submit" and the workflow will show up in "My Workflows" table button in Ecoscope Desktop
   - Click on "Run" and the workflow will begin processing

3. **Monitor progress and wait for completion**
   - You'll see status updates as the workflow runs
   - Processing time depends on:
     - The size of your date range
     - Number of patrols and observations in the period
     - Number of patrol areas in scope
   - The workflow completes with status "Success" or "Failed"

---

## Understanding Your Results

After the workflow completes successfully, you'll find your outputs in the designated output folder.

### Data Outputs

#### Patrol Trajectories (one file per patrol area)

- **File formats**: Parquet and/or CSV (based on your selection)
- **Opens in**: Python/R (Parquet), Microsoft Excel or Google Sheets (CSV)
- **Contents**: One row per trajectory segment with patrol attributes joined on
  - `patrol_id`: The EarthRanger patrol the segment belongs to
  - `patrol_area`: `Mara Triangle` or `Reserve`
  - `team_name`, `ranger_name`, `patrol_mandate`, `patrol_transport`: From the patrol's **patrol_info** event (or `Unknown` if the patrol has none)
  - `dist_meters`, `timespan_seconds`, `speed_kmhr`, `segment_start`, `segment_end`: Movement metrics

#### Summary Tables (CSV, one per patrol area)

- **Transport summary** (`transport_summary_*.csv`): Distance and duration totals by transport type
- **Mandate summary** (`mandate_summary_*.csv`): Distance and duration totals by patrol mandate
- **Team summary** (`team_summary_*.csv`): Distance and duration totals by team
- **Ranger summary** (`ranger_summary_*.csv`, one per area × team): Distance and duration totals per ranger

### Visual Outputs

This is a report-driven workflow — the dashboard is intentionally empty. Maps and charts are produced as standalone files and embedded in the Word report:

#### Patrol Trajectory Maps (one per patrol area × mandate)
- **Format**: Interactive HTML map
- **Features**:
  - Patrol trajectories drawn over the basemap, color-coded by team with a team legend (bottom-right)
  - North arrow (top-left)
  - Interactive hover: Team, Ranger, Start Time, Duration, and Speed for each segment

#### Team Activity Bar Charts (one per patrol area)
- **Format**: Interactive HTML bar chart
- **Features**:
  - X-axis: Team
  - Y-axis: Total distance (km) and total duration (hours), as paired bars

#### Word Report (`mt_patrols_report_*.docx`)

The report has three chapters, each with one subsection per patrol area in scope:

1. **Trajectory Maps** — one map per mandate in each area
2. **Patrol Summary** — transport, mandate, and team totals tables plus the team bar chart for each area
3. **Ranger Summary** — one ranger totals table per team in each area

---

## Common Use Cases & Examples

Here are some typical scenarios and how to configure the workflow for each:

### Example 1: Monthly patrol report for both areas
**Goal**: The standard monthly report covering the Mara Triangle and the Reserve

**Configuration**:
- **Time Range**:
  - Since: `2026-07-01T00:00:00`
  - Until: `2026-07-31T23:59:59`
  - Timezone: `Africa/Nairobi (UTC+03:00)`
- **Data Source**: `"mmnr"`
- **Report Scope**: `"Mara Triangle & Reserve"`

**Result**:
- A Word report with Mara Triangle and Reserve subsections in every chapter
- Trajectory parquet files, summary CSVs, maps, and bar charts for both areas

---

### Example 2: Mara Triangle only
**Goal**: A report restricted to Mara Triangle patrol activity

**Configuration**:
- **Time Range**: as above
- **Data Source**: `"mmnr"`
- **Report Scope**: `"Mara Triangle only"`

**Result**:
- Only patrols whose type is in the **Mara Triangle Patrol Types** list are fetched and reported
- Each chapter contains a single Mara Triangle subsection

---

### Example 3: Focus on law-enforcement patrols
**Goal**: Report only law-enforcement activity in both areas

**Configuration**:
- **Report Scope**: `"Mara Triangle & Reserve"`
- **Mara Triangle Patrol Types** (advanced): `general_law_enforcement`, `law_enforcement_vehicle`
- **Reserve Patrol Types** (advanced): `law_enforcement_veh_reserve`

**Result**:
- Only the listed patrol types are included; maps, summaries, and ranger tables reflect just those patrols

---

### Example 4: Custom report template
**Goal**: Use your organization's own report design

**Configuration**:
- **Create Patrol Report → Template Path**: URL or path to your custom `.docx` template
- All other settings as in Example 1

**Result**:
- The same data rendered into your custom template layout

---

## Troubleshooting

### Common Issues and Solutions

#### Workflow fails to start
**Problem**: The workflow fails immediately with a connection or authentication error

**Solutions**:
- Verify your EarthRanger data source is configured correctly in Ecoscope Desktop
- Check that your EarthRanger username and password are still valid
- Confirm the data source name matches your configured connection (e.g., `"mmnr"`)

#### No patrols returned
**Problem**: The workflow completes but the report is mostly empty

**Solutions**:
- Widen your time range — only patrols overlapping the range are included
- Check that patrols in EarthRanger have status "done" for the period
- Verify the patrol types used in your EarthRanger site appear in the **Mara Triangle Patrol Types** or **Reserve Patrol Types** lists — patrols with other types are excluded

#### Patrol attributes show "Unknown"
**Problem**: Teams, rangers, mandates, or transport appear as `Unknown` in the report

**Solutions**:
- The affected patrols have no **patrol_info** event attached in EarthRanger — add one to each patrol
- Check that the **patrol_info** event's details (ranger, team, mandate, transport) are filled in
- Note: This is expected behavior, not an error — patrols are never dropped for missing attributes

#### An area subsection is missing from the report
**Problem**: The report only shows one of the two areas

**Solutions**:
- Check the **Report Scope** setting — `"Mara Triangle only"` and `"Reserve only"` intentionally omit the other area
- If scope is `"Mara Triangle & Reserve"`, confirm the missing area actually had patrols (of the configured types) during the time range

#### Workflow runs very slowly
**Problem**: The workflow takes a long time to complete

**Solutions**:
- Use a shorter time range — patrol observation volume grows quickly with the period length
- The first run after installation is slower while the workflow environment warms up; later runs are faster

#### Report template errors
**Problem**: The workflow fails at the report generation step

**Solutions**:
- If you supplied a custom template, verify it is a valid `.docx` file and its placeholders match the workflow's report items (`patrol_maps`, `transport_summary`, `mandate_summary`, `team_summary`, `team_bar_chart`, `ranger_summary`, `report_date`)
- If using a URL, confirm the file is reachable from your machine
- Revert to the default template to confirm the rest of the workflow is healthy
