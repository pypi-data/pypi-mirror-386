set project_name "$::env(PROJECT_NAME)"
set device "$::env(DEVICE)"
set source_type "$::env(SOURCE_TYPE)"

set top_module "${project_name}"
set output_dir "./output_${project_name}"

create_project $project_name "${output_dir}/$project_name" -force -part $device

set_property DEFAULT_LIB work [current_project]

if { $source_type != "vhdl" && $source_type != "verilog" } {
    puts "Error: SOURCE_TYPE must be either 'vhdl' or 'verilog'."
    exit 1
}

if { $source_type == "vhdl" } {
    set_property TARGET_LANGUAGE VHDL [current_project]

    foreach file [glob -nocomplain "src/static/*.vhd"] {
        read_vhdl -vhdl2008 $file
    }

    read_vhdl -vhdl2008 "src/${project_name}.vhd"
    foreach file [glob -nocomplain "src/${project_name}_stage*.vhd"] {
        read_vhdl -vhdl2008 $file
    }
} else {
    set_property TARGET_LANGUAGE Verilog [current_project]

    foreach file [glob -nocomplain "src/static/*.v"] {
        read_verilog $file
    }

    read_verilog "src/${project_name}.v"
    foreach file [glob -nocomplain "src/${project_name}_stage*.v"] {
        read_verilog $file
    }
}


set mems [glob -nocomplain "src/memfiles/*.mem"]

# VHDL only uses relative path to working dir apparently...
if { $source_type == "vhdl" } {
    foreach f $mems {
        file copy -force $f [file tail $f]
    }
    set mems [glob -nocomplain "*.mem"]
}

foreach f $mems {
    add_files -fileset [current_fileset] $f
    set_property used_in_synthesis true [get_files $f]
}

# Add XDC constraint if it exists
if { [file exists "src/${project_name}.xdc"] } {
    read_xdc "src/${project_name}.xdc" -mode out_of_context
}

set_property top $top_module [current_fileset]

file mkdir $output_dir
file mkdir "${output_dir}/reports"

# synth
synth_design -top $top_module -mode out_of_context -global_retiming on \
    -flatten_hierarchy full -resource_sharing auto -directive PerformanceOptimized

write_checkpoint -force "${output_dir}/${project_name}_post_synth.dcp"

report_timing_summary -file "${output_dir}/reports/${project_name}_post_synth_timing.rpt"
report_power -file "${output_dir}/reports/${project_name}_post_synth_power.rpt"
report_utilization -file "${output_dir}/reports/${project_name}_post_synth_util.rpt"

# opt_design -directive ExploreSequentialArea
opt_design -directive ExploreWithRemap

report_design_analysis -congestion -file "${output_dir}/reports/${project_name}_post_opt_congestion.rpt"

# place
place_design -directive SSI_HighUtilSLRs -fanout_opt
report_design_analysis -congestion -file "${output_dir}/reports/${project_name}_post_place_congestion_initial.rpt"

phys_opt_design -directive AggressiveExplore
write_checkpoint -force "${output_dir}/${project_name}_post_place.dcp"
file delete -force "${output_dir}/${project_name}_post_synth.dcp"

report_design_analysis -congestion -file "${output_dir}/reports/${project_name}_post_place_congestion_final.rpt"

report_timing_summary -file "${output_dir}/reports/${project_name}_post_place_timing.rpt"
report_utilization -hierarchical -file "${output_dir}/reports/${project_name}_post_place_util.rpt"

# route
route_design -directive NoTimingRelaxation
write_checkpoint -force "${output_dir}/${project_name}_post_route.dcp"
file delete -force "${output_dir}/${project_name}_post_place.dcp"


report_timing_summary -file "${output_dir}/reports/${project_name}_post_route_timing.rpt"
report_timing -sort_by group -max_paths 100 -path_type summary -file "${output_dir}/reports/${project_name}_post_route_timing_paths.rpt"
report_clock_utilization -file "${output_dir}/reports/${project_name}_post_route_clock_util.rpt"
report_utilization -file "${output_dir}/reports/${project_name}_post_route_util.rpt"
report_power -file "${output_dir}/reports/${project_name}_post_route_power.rpt"
report_drc -file "${output_dir}/reports/${project_name}_post_route_drc.rpt"

report_utilization -format xml -hierarchical -file "${output_dir}/reports/${project_name}_post_route_util.xml"
report_power -xpe "${output_dir}/reports/${project_name}_post_route_power.xml"

# Generate Verilog netlist for simulation
# write_verilog -force "${output_dir}/${project_name}_impl_netlist.v" -mode timesim -sdf_anno true

puts "Implementation complete. Results saved in ${output_dir}"
