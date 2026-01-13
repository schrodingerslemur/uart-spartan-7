read_verilog -sv "top.sv"
read_verilog -sv "SSegDisplayDriver.sv"
read_verilog -sv "uart.sv"
read_verilog -sv "uart_rx.sv"
read_verilog -sv "uart_tx.sv"

read_xdc "Boolean240.xdc"

synth_design -top "top" -part "xc7s50csga324-1"

opt_design
place_design
route_design

write_bitstream -force "top.bit"

open_hw_manager
connect_hw_server
current_hw_target
open_hw_target
set_property PROGRAM.FILE top.bit [current_hw_device]
program_hw_devices [current_hw_device]