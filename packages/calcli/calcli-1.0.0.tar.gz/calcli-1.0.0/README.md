# calcli

A simple, elegant terminal calculator with interactive mode. Perfect for quick math without leaving your terminal.

## Quick Start

```bash
pip install calcli
calcli
```

Done. You're in calculator mode.

## Usage

### Interactive Mode

```bash
calcli
```

Then:

```
calcli> 5 + 3
8
calcli> 10 * 2.5
25
calcli> 32% of 2345454
750545.28
calcli> 5 km to miles
3.11 miles
calcli> h
calcli> exit
```

### Single Calculation

```bash
calcli "5 + 3"
# Output: 8

calcli "32% of 100"
# Output: 32

calcli "10 km to miles"
# Output: 6.21 miles
```

## Features

**Interactive mode** — Stay in the calculator, run multiple calculations  
**Basic math** — Add, subtract, multiply, divide, parentheses  
**Percentages** — "32% of 2345454" syntax  
**Unit conversions** — 14+ conversions including distance, weight, temperature, volume  
**Colored output** — Clean, readable results  
**Fast** — No GUI overhead, pure terminal speed  
**History** — Type `h` to see your last 10 calculations with results  
**Auto-copy** — Results are instantly copied to your clipboard

## Available Conversions

```
celsius to fahrenheit      kg to lbs                 miles to km
fahrenheit to celsius      km to miles               ounces to grams
feet to meters             lbs to kg                 grams to ounces
meters to feet             inches to cm              gallons to liters
cm to inches               liters to gallons
```

Type `help` in interactive mode to see the full list.

## Requirements

- Python 3.8+
- colorama (for colored output)
- pyperclip (for clipboard support)

## Installation

### From PyPI

```bash
pip install calcli
```

### From GitHub

```bash
git clone https://github.com/tolaoyelola/calcli.git
cd calcli
pip install -r requirements.txt
pip install -e .
```

## Examples

```bash
# Basic math
calcli "100 + 50 * 2"
# Output: 200

calcli "(100 + 50) * 2"
# Output: 300

# Percentages
calcli "15% of 80"
# Output: 12

# Conversions
calcli "32 celsius to fahrenheit"
# Output: 89.60 fahrenheit

calcli "100 kg to lbs"
# Output: 220.46 lbs

calcli "5 inches to cm"
# Output: 12.70 cm
```

## Special Commands (Interactive Mode)

```
help     Show all available commands and conversions
h        Display your last 10 calculations with results
exit     Quit calcli
q        Quit calcli (shorthand)
```

## Contributing

Contributions welcome! Feel free to open issues or submit PRs.

## License

MIT — See LICENSE file for details.
