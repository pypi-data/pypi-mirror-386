#!/usr/bin/env python3
"""
calcli — A simple, elegant terminal calculator with interactive mode.

Usage:
  calcli                    Enter interactive mode
  calcli "5 + 3"           Single calculation and exit
  calcli "32% of 2345454"  Percentage calculation and exit

In interactive mode:
  calcli> 5 + 3
  8
  calcli> 10 * 2.5
  25
  calcli> 32% of 100
  32
  calcli> 5 km to miles
  3.11 miles
  calcli> help
  calcli> exit
"""

import sys
import re
import pyperclip
import readline
from colorama import Fore, Style, init

init(autoreset=True)

# ======================================================================
# CONVERSIONS
# ======================================================================

CONVERSIONS = {
    "km to miles": 0.621371,
    "miles to km": 1.60934,
    "kg to lbs": 2.20462,
    "lbs to kg": 0.453592,
    "celsius to fahrenheit": lambda x: (x * 9/5) + 32,
    "fahrenheit to celsius": lambda x: (x - 32) * 5/9,
    "meters to feet": 3.28084,
    "feet to meters": 0.3048,
    "inches to cm": 2.54,
    "cm to inches": 0.393701,
    "liters to gallons": 0.264172,
    "gallons to liters": 3.78541,
    "ounces to grams": 28.3495,
    "grams to ounces": 0.035274,
}

# ======================================================================
# HISTORY
# ======================================================================

class Calculator:
    def __init__(self):
        self.history = []
    
    def add_to_history(self, expression, result):
        """Add calculation to history."""
        self.history.append({"expr": expression, "result": result})
    
    def print_history(self):
        """Display last 10 calculations."""
        if not self.history:
            print(f"{Fore.YELLOW}No history yet{Style.RESET_ALL}\n")
            return
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Recent Calculations:{Style.RESET_ALL}")
        # Show last 10
        for i, entry in enumerate(self.history[-10:], 1):
            print(f"  {i}. {Fore.CYAN}{entry['expr']}{Style.RESET_ALL} = {Fore.GREEN}{entry['result']}{Style.RESET_ALL}")
        print()

calc = Calculator()

# ======================================================================
# CALCULATOR LOGIC
# ======================================================================

def parse_percentage(expr):
    """Handle 'X% of Y' syntax."""
    match = re.match(r'(\d+(?:\.\d+)?)\s*%\s+of\s+(\d+(?:\.\d+)?)', expr.strip())
    if match:
        percentage = float(match.group(1))
        total = float(match.group(2))
        return (percentage / 100) * total
    return None

def parse_conversion(expr):
    """Handle 'X unit1 to unit2' syntax."""
    expr = expr.strip().lower()
    for conversion_key, factor in CONVERSIONS.items():
        pattern = rf'(\d+(?:\.\d+)?)\s+{conversion_key}'
        match = re.match(pattern, expr)
        if match:
            value = float(match.group(1))
            if callable(factor):
                result = factor(value)
            else:
                result = value * factor
            unit_from, unit_to = conversion_key.split(" to ")
            return f"{result:.2f} {unit_to}"
    return None

def calculate(expr):
    """Safely evaluate a mathematical expression."""
    try:
        # Check for percentage syntax first
        percent_result = parse_percentage(expr)
        if percent_result is not None:
            return percent_result
        
        # Check for conversion syntax
        conversion_result = parse_conversion(expr)
        if conversion_result is not None:
            return conversion_result
        
        # Otherwise, evaluate as math expression
        # Only allow safe characters
        if not re.match(r'^[\d\s+\-*/(). ]+$', expr):
            return None
        
        result = eval(expr)
        return result
    except:
        return None

def copy_to_clipboard(result):
    """Copy result to clipboard."""
    try:
        if isinstance(result, str):
            pyperclip.copy(result)
        else:
            # Clean up float display for clipboard
            if isinstance(result, float) and result == int(result):
                pyperclip.copy(str(int(result)))
            else:
                pyperclip.copy(str(result))
        return True
    except:
        return False

def format_result(result, expr):
    """Format and display result with color, then copy to clipboard."""
    if result is None:
        print(f"{Fore.RED}Invalid input. Try: 5 + 3, 32% of 100, or 5 km to miles{Style.RESET_ALL}")
        return
    
    if isinstance(result, str):
        print(f"{Fore.GREEN}{result}{Style.RESET_ALL}")
    else:
        # Clean up float display
        if isinstance(result, float):
            if result == int(result):
                result = int(result)
        print(f"{Fore.CYAN}{result}{Style.RESET_ALL}")
    
    # Auto-copy to clipboard
    if copy_to_clipboard(result):
        print(f"{Fore.YELLOW}(copied to clipboard){Style.RESET_ALL}")
    
    # Add to history
    calc.add_to_history(expr, result)

def print_banner():
    """Print welcome banner."""
    print(f"{Fore.BLUE}{Style.BRIGHT}")
    print("  ╔════════════════════════════════════════╗")
    print("             🧮 calcli v1.0.0 🧮             ")
    print("          Simple terminal calculator             ")
    print("  ╚════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Type 'help' for commands or 'q' to quit{Style.RESET_ALL}\n")

def print_help():
    """Print comprehensive help."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Commands & Syntax:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}Basic math{Style.RESET_ALL}")
    print(f"    5 + 3           (add)")
    print(f"    10 - 2          (subtract)")
    print(f"    4 * 5           (multiply)")
    print(f"    20 / 4          (divide)")
    print(f"    (5 + 3) * 2     (parentheses)")
    
    print(f"\n  {Fore.CYAN}Percentages{Style.RESET_ALL}")
    print(f"    15% of 100      (15% of 100 = 15)")
    print(f"    32% of 2345454  (calculate percentage)")
    
    print(f"\n  {Fore.CYAN}Conversions{Style.RESET_ALL}")
    print(f"    5 km to miles")
    print(f"    100 kg to lbs")
    print(f"    32 celsius to fahrenheit")
    print(f"    10 inches to cm")
    print(f"    5 liters to gallons")
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Available Conversions:{Style.RESET_ALL}")
    for conv in sorted(CONVERSIONS.keys()):
        print(f"  • {conv}")
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Special Commands:{Style.RESET_ALL}")
    print(f"  help     (show this message)")
    print(f"  h        (show calculation history)")
    print(f"  exit, quit or q     (quit calcli)\n")

def interactive_mode():
    """Run interactive calculator mode."""
    print_banner()
    
    while True:
        try:
            user_input = input(f"{Fore.MAGENTA}calcli>{Style.RESET_ALL} ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ('exit', 'quit', 'q'):
                print(f"{Fore.CYAN}Bye! 👋{Style.RESET_ALL}")
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            if user_input.lower() == 'h':
                calc.print_history()
                continue
            
            result = calculate(user_input)
            format_result(result, user_input)
        
        except KeyboardInterrupt:
            print(f"\n{Fore.CYAN}Bye! 👋{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

def main():
    """Entry point."""
    if len(sys.argv) > 1:
        # Single calculation mode
        expr = " ".join(sys.argv[1:])
        result = calculate(expr)
        format_result(result, expr)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()