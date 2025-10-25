# G-Code Test Examples

Comprehensive collection of G-code NC files for testing the GCodeClean MCP server across various CNC controller types and machining operations.

## Directory Structure

Files are organized by controller type:

- **`generic/`** - Standard ISO G-code compatible with multiple controllers (Fanuc, Haas, etc.)
- **`linuxcnc/`** - LinuxCNC-specific examples from official repository
- **`siemens/`** - Siemens SINUMERIK format files (.mpf/.spf)
- **`marlin/`** - 3D printer G-code (Marlin firmware)
- **`fanuc/`** - Fanuc-specific examples (currently empty, see generic/)

## Contents by Directory

### generic/ - Standard ISO G-code (10 files)

**Basic Examples**

**circle.nc**
- Simple 1-inch diameter circle milling
- Source: DIY Machining

**simple-square.ngc**
- Basic square geometry

**3circles.ngc**
- Three circle pattern using G41/G42
- Tests cutter radius compensation

**subroutine-sample.ngc**
- Demonstrates G-code subroutine calls
- Tests program flow control

**var-circles.ngc**
- Variable-based circular patterns
- Tests parameter programming

**bottle-3axis.ngc** (172KB)
- 3-axis bottle contour
- High-speed machining

**building-brick.ngc**
- Building brick geometry
- Tests pocketing operations

**CNC_2023.ngc** (10KB)
- Modern CNC programming example
- Mixed operations

**G61-example.ngc**
- Exact stop mode demonstration
- Tests path control modes

**Sample_M1.ngc**
- M-code demonstrations
- Optional program stop

### linuxcnc/ - LinuxCNC Examples (13 files)

**Advanced Milling**

**3D_Chips.ngc** (196KB)
- Complex 3D profiling
- Extensive toolpath

**arcspiral.ngc** (30KB)
- Spiral arc interpolation
- Tests continuous arc commands

**daisy.ngc**
- Decorative daisy pattern
- Complex arc interpolation

**circular-pocket.ngc**
- Circular pocket milling wizard output
- LinuxCNC wizard generated

**hole-circle.ngc**
- Circular hole pattern
- Tests canned cycles

**Lathe Operations**

**lathe-g76-threading.ngc**
- G76 threading cycle
- Multiple thread passes

**lathe-spiral.ngc**
- Spiral turning operation

**lathe_pawn.ngc**
- Chess pawn turning profile
- Complex lathe geometry

**lathecomp.ngc**
- Lathe tool nose radius compensation
- Tests G41/G42 on lathe

**threading.ngc**
- Threading operations
- Various thread pitches

**Specialized Operations**

**gridprobe.ngc**
- Grid probing routine
- Workpiece measurement

**plasmatest.ngc** (13KB)
- Plasma cutting test
- 2D cutting operations

**spiral.ngc**
- Spiral toolpath
- Mathematical curve generation

### siemens/ - SINUMERIK (1 file)

**sinumerik-example.mpf**
- Siemens SINUMERIK format
- MPF main program file
- Demonstrates Siemens-specific syntax

### marlin/ - 3D Printer (1 archive)

**prusa-mk3s-samples.zip** (5.1MB)
- Prusa MK3S+ sample G-code files
- FDM 3D printing operations
- Marlin-based firmware
- Extract to access multiple .gcode files

## File Format Reference

### Extensions

- `.nc` / `.ngc` - Generic CNC / LinuxCNC G-code
- `.mpf` - Siemens SINUMERIK main program
- `.spf` - Siemens SINUMERIK subprogram
- `.gcode` - 3D printer G-code (Marlin, RepRap)
- `.eia` - Mazak EIA/ISO format

### Controller Types Represented

- **Fanuc** - Industry standard (most .nc/.ngc files)
- **LinuxCNC** - Open source CNC control
- **Siemens SINUMERIK** - High-end industrial (.mpf)
- **Haas** - Popular vertical mills/lathes
- **Marlin** - 3D printer firmware (.gcode files)
- **ISO 6983-1** - International standard (general .nc files)

## Operation Types

- Milling (2D, 2.5D, 3D)
- Turning/Lathe
- Threading
- Drilling/Tapping
- Pocketing
- Probing
- Plasma cutting
- Additive (3D printing)

## Sources

- LinuxCNC official repository (github.com/LinuxCNC/linuxcnc)
- thecooltool/example-gcode (github.com/thecooltool/example-gcode)
- Prusa Research (prusa3d.com)
- DIY Machining
- Various CNC educational resources

## Summary Statistics

- **Total Files**: 24 G-code files + 1 archive
- **generic/**: 10 files (standard ISO G-code)
- **linuxcnc/**: 13 files (LinuxCNC repository examples)
- **siemens/**: 1 file (SINUMERIK .mpf format)
- **marlin/**: 1 archive (3D printer samples)
- **Size Range**: 14 bytes to 196KB per file

## Usage

These files are suitable for:
- Testing G-code parsers
- Validating G-code cleaning operations
- CNC machine simulation
- Educational purposes
- Benchmarking G-code processors
- Multi-controller compatibility testing

## Notes

- Files organized by controller type for easy testing
- Most files use standard ISO G-code (generic/)
- LinuxCNC examples include advanced features and wizards
- Siemens files use MPF format (different syntax from ISO)
- 3D printer G-code includes temperature/extrusion commands
- Always verify compatibility before running on actual machines
- Generic folder contains Fanuc/Haas/ISO compatible files
