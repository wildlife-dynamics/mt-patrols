# MT Patrols Report — PRD

## Goal
Replace the dashboard output with a Word document (`.docx`) containing patrol maps, bar charts, stats tables, and ranger summary tables.

## Current State
- Data pipeline: SMART → relocations → trajectories → filter/transform → split by mandate grouper → maps → dashboard
- Grouper: user-configurable, currently `patrol_mandate` (values: "Anti-animal Harassment", "Anti-Poaching")
- Key columns after trajectory processing: `patrol_id`, `patrol_mandate`, `patrol_transport`, `station`, `patrol_leader_name`, `timespan_seconds`, `dist_meters`, `segment_start`
- Transport types: "Vehicle", "Foot" (upcoming)
- Stations: Purungat, Oloololo, Iseiyia, Kilo 2, Ololaimutia
- Rangers: 25 unique (`patrol_leader_name`)

## Output: Word Document via `create_docx`

### A) Patrol Maps per Mandate (grouped images)
- Reuse existing ecomap pipeline: `split_patrol_traj_groups` → `patrol_traj_map_layers` → `traj_ecomap` → `traj_ecomap_html_urls`
- Feed persisted HTML URLs as `item_type: image` (grouped by mandate) to `create_docx`
- One map per mandate group

### B) Bar Chart by Transport Type (single image)
- `summarize_df` on trajectory data:
  - `groupby_cols: ["patrol_transport"]`
  - Summary params: total hours (sum timespan_seconds, s→h), total distance (sum dist_meters, m→km), patrol count (nunique patrol_id)
  - `reset_index: true`
- `draw_bar_chart`:
  - `category: "patrol_transport"` (x-axis: Vehicle, Foot)
  - `bar_chart_configs`: bars for "Total Hours" and "Total Distance (km)"
- `persist_text` the chart HTML
- Feed as `item_type: image` (single) to `create_docx`

### C) Transport Stats Table (single table)
- Reuse the same `summarize_df` output from (B)
- Feed DataFrame directly as `item_type: table` to `create_docx`
- Columns: patrol_transport, # Patrols, Total Hours, Total Distance (km)

### D) Ranger Tables per Station (grouped tables)
- **Separate station grouper** (fixed, not user-configurable):
  - `set_groupers` with `partial: groupers: [{index_name: "station"}]`
- `split_groups` by station grouper on the trajectory data
- `summarize_df` via `mapvalues` over station groups:
  - `groupby_cols: ["patrol_leader_name"]`
  - Summary params: # Patrols (nunique patrol_id), Total Hours (sum timespan_seconds, s→h), Total Distance (sum dist_meters, m→km)
  - `reset_index: true`
- Feed grouped DataFrames as `item_type: table` (grouped by station) to `create_docx`
- Produces one table per station, each showing all rangers

## Spec Changes

### Remove
- `traj_map_widgets_single_views` (create_map_widget_single_view)
- `traj_grouped_map_widget` (merge_widget_views)
- `patrol_dashboard` (gather_dashboard)

### Keep (modify output wiring)
- All tasks from `workflow_details` through `traj_ecomap_html_urls`
- `persist_patrol_traj` (data export)

### Add

#### Bar Chart Section
```yaml
- id: transport_summary
  task: summarize_df
  partial:
    df: ${{ workflow.sql_query_traj.return }}  # or traj_colormap, whichever has all needed cols
    groupby_cols: ["patrol_transport"]
    summary_params:
      - display_name: "# Patrols"
        aggregator: nunique
        column: patrol_id
      - display_name: "Total Hours"
        aggregator: sum
        column: timespan_seconds
      - display_name: "Total Distance (km)"
        aggregator: sum
        column: dist_meters
    reset_index: true

- id: patrol_bar_chart
  task: draw_bar_chart
  partial:
    dataframe: ${{ workflow.transport_summary.return }}
    category: "patrol_transport"
    bar_chart_configs:
      - label: "Total Hours"
        column: "Total Hours"
        agg: "sum"
      - label: "Total Distance (km)"
        column: "Total Distance (km)"
        agg: "sum"

- id: persist_bar_chart
  task: persist_text
  partial:
    text: ${{ workflow.patrol_bar_chart.return }}
    root_path: ${{ env.ECOSCOPE_WORKFLOWS_RESULTS }}
```

#### Ranger per Station Section
```yaml
- id: station_groupers
  task: set_groupers
  partial:
    groupers:
      - index_name: "station"

- id: split_by_station
  task: split_groups
  partial:
    df: ${{ workflow.sql_query_traj.return }}
    groupers: ${{ workflow.station_groupers.return }}

- id: ranger_summary
  task: summarize_df
  partial:
    groupby_cols: ["patrol_leader_name"]
    summary_params:
      - display_name: "# Patrols"
        aggregator: nunique
        column: patrol_id
      - display_name: "Total Hours"
        aggregator: sum
        column: timespan_seconds
      - display_name: "Total Distance (km)"
        aggregator: sum
        column: dist_meters
    reset_index: true
  mapvalues:
    argnames: df
    argvalues: ${{ workflow.split_by_station.return }}
```

#### Document Output
```yaml
- id: create_patrol_report
  task: create_docx
  partial:
    context:
      items:
        - item_type: text
          key: title
          value: "MT Patrols Report"
        - item_type: timerange
          key: report_date
          value: ${{ workflow.time_range.return }}
        - item_type: image
          key: patrol_maps
          value: ${{ workflow.traj_ecomap_html_urls.return }}
          screenshot_config:
            wait_for_timeout: 0
        - item_type: image
          key: bar_chart
          value: ${{ workflow.persist_bar_chart.return }}
          screenshot_config:
            wait_for_timeout: 0
        - item_type: table
          key: transport_stats
          value: ${{ workflow.transport_summary.return }}
        - item_type: table
          key: ranger_tables
          value: ${{ workflow.ranger_summary.return }}
    groupers: ${{ workflow.groupers.return }}
    output_dir: ${{ env.ECOSCOPE_WORKFLOWS_RESULTS }}
    filename_prefix: mt_patrols_report
```

## Grouper Handling
- **Mandate grouper** (`groupers` task): user-configurable, drives map grouping and docx grouped image sorting
- **Station grouper** (`station_groupers` task): fixed via `partial`, drives ranger table splitting
- These are independent — mandate grouper controls the report's map sections, station grouper controls ranger table sections
- The `create_docx` `groupers` param receives the mandate grouper for sorting grouped items

## Template
A basic `.docx` template is needed at `resources/templates/mt_patrols_template.docx` with Jinja2 placeholders:

```
{{ title }}
{{ report_date }}

Patrol Maps:
{% for item in patrol_maps %}
{{ item.title }}
{{ item.image }}
{% endfor %}

Patrol Summary by Transport Type:
{{ bar_chart }}

Transport Type Statistics:
{% for col in transport_stats.col_labels %}{{ col }}{% endfor %}
{% for row in transport_stats.tbl_contents %}{{ row.label }}{% for col in row.cols %}{{ col }}{% endfor %}{% endfor %}

Ranger Summary by Station:
{% for item in ranger_tables %}
{{ item.title }}
{% for col in item.col_labels %}{{ col }}{% endfor %}
{% for row in item.tbl_contents %}{{ row.label }}{% for col in row.cols %}{{ col }}{% endfor %}{% endfor %}
{% endfor %}
```

## Test Cases (test-cases.yaml updates)
Add params for new tasks:
```yaml
transport_summary:
  groupby_cols: ["patrol_transport"]
  summary_params:
    - display_name: "# Patrols"
      aggregator: nunique
      column: patrol_id
    - display_name: "Total Hours"
      aggregator: sum
      column: timespan_seconds
    - display_name: "Total Distance (km)"
      aggregator: sum
      column: dist_meters
  reset_index: true

patrol_bar_chart:
  category: "patrol_transport"
  bar_chart_configs:
    - label: "Total Hours"
      column: "Total Hours"
      agg: "sum"
    - label: "Total Distance (km)"
      column: "Total Distance (km)"
      agg: "sum"

station_groupers:
  groupers:
    - index_name: "station"

ranger_summary:
  groupby_cols: ["patrol_leader_name"]
  summary_params:
    - display_name: "# Patrols"
      aggregator: nunique
      column: patrol_id
    - display_name: "Total Hours"
      aggregator: sum
      column: timespan_seconds
    - display_name: "Total Distance (km)"
      aggregator: sum
      column: dist_meters
  reset_index: true

create_patrol_report:
  template_path: "resources/templates/mt_patrols_template.docx"
```

## Implementation Order
1. Add `summarize_df` tasks (transport + ranger) to spec.yaml
2. Add `draw_bar_chart` + `persist_text` for bar chart
3. Add station grouper + split for ranger tables
4. Remove dashboard tasks, add `create_docx`
5. Create basic `.docx` template
6. Update test-cases.yaml
7. Compile and test
