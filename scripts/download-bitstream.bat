@echo off
setlocal

REM ===============================
REM Run Vivado in batch mode
REM ===============================
vivado ^
  -mode batch ^
  -source download-bitstream.tcl 

endlocal
