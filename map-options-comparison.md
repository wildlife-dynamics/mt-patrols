# Map Generation: Lonboard vs Pydeck

## Task Mapping

| Step | Lonboard (ext-ecoscope) | Pydeck (ext-custom) |
|------|------------------------|---------------------|
| Base maps | `set_base_maps` | `set_base_maps_pydeck` |
| Create layers | `create_polyline_layer` | `create_path_layer` |
| Render map | `draw_ecomap` | `draw_map` |
| Persist HTML | `persist_text` | `persist_text` |

## Key Differences

| | Lonboard | Pydeck |
|---|---------|--------|
| **HTML size** | ~2-5 MB (binary serialization) | **~837 MB** (inline JSON) |
| **Rendering** | Self-contained, fast load | CDN-dependent (deck.gl JS) |
| **Screenshot** | Works with Playwright | Hangs — file too large to render |
| **Tooltips** | `tooltip_columns` param to filter | Shows all columns (no filter) |
| **Color accessor** | `color_column` on layer style | `get_color` on layer style |
| **North arrow** | Configurable via `north_arrow_style` | Built-in default widget |
| **Base map config** | `layer_name: "TERRAIN"` | Raw URL required |
| **Custom widgets** | No | Yes (legend, scale, save image) |
| **Package** | ecoscope-workflows-ext-ecoscope | ecoscope-workflows-ext-custom |

## Blocker for Pydeck

Pydeck's `to_html()` serializes the full GeoDataFrame as inline JSON. With patrol
trajectory data (~Feb 2026 month), this produces an **837 MB HTML file** that:
- Cannot be opened in a browser
- Causes Playwright screenshot to hang
- Would need a data-reduction strategy (simplify geometry, downsample) to be viable

## Lonboard spec (current working version)

```yaml
      - name: "Set Patrol Map Title"
        id: set_patrol_map_title
        task: set_string_var
        partial:
          var: "Patrol Trajectories Map"

      - name: " "
        id: base_map_defs
        task: set_base_maps
        partial:
          base_maps:
            - layer_name: "TERRAIN"
              opacity: 1

      - name: Create Trajectory Map Layers
        id: patrol_traj_map_layers
        task: create_polyline_layer
        skipif:
          conditions:
            - any_is_empty_df
            - any_dependency_skipped
            - all_geometry_are_none
        partial:
          layer_style:
            get_width: 3
            width_units: "pixels"
            color_column: "patrol_traj_colormap"
          legend: null
          tooltip_columns: ["Start Time", "Duration (s)", "Speed (kph)"]
        mapvalues:
          argnames: geodataframe
          argvalues: ${{ workflow.rename_traj_display_columns.return }}

      - name: Draw Ecomaps
        id: traj_ecomap
        task: draw_ecomap
        partial:
          title: null
          tile_layers: ${{ workflow.base_map_defs.return }}
          north_arrow_style:
            placement: "top-left"
          legend_style: null
          static: false
          max_zoom: 20
        mapvalues:
          argnames: geo_layers
          argvalues: ${{ workflow.patrol_traj_map_layers.return }}
```

## Pydeck spec (blocked by HTML size)

```yaml
      - name: " "
        id: base_map_defs
        task: ecoscope_workflows_ext_custom.tasks.results.set_base_maps_pydeck
        partial:
          base_maps:
            - url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
              opacity: 1

      - name: Create Trajectory Map Layers
        id: patrol_traj_map_layers
        task: ecoscope_workflows_ext_custom.tasks.results.create_path_layer
        skipif:
          conditions:
            - any_is_empty_df
            - any_dependency_skipped
            - all_geometry_are_none
        partial:
          layer_style:
            get_width: 3
            width_units: "pixels"
            get_color: "patrol_traj_colormap"
          legend: null
        mapvalues:
          argnames: geodataframe
          argvalues: ${{ workflow.rename_traj_display_columns.return }}

      - name: Draw Ecomaps
        id: traj_ecomap
        task: ecoscope_workflows_ext_custom.tasks.results.draw_map
        partial:
          title: null
          tile_layers: ${{ workflow.base_map_defs.return }}
          legend_style: null
          static: false
          max_zoom: 20
        mapvalues:
          argnames: geo_layers
          argvalues: ${{ workflow.patrol_traj_map_layers.return }}
```
