#!/usr/bin/env python3

import argparse
import csv
import sys
from datetime import datetime, timedelta
import calendar
from math import sqrt, floor

# Failsafe imports
try:
    import numpy as np
    from scipy.stats import t
    _SCIPY_INSTALLED = True
except ImportError:
    _SCIPY_INSTALLED = False

try:
    import pandas as pd
    _PANDAS_INSTALLED = True
except ImportError:
    _PANDAS_INSTALLED = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.patheffects as patheffects
    from packaging.version import parse as parse_version
    _MATPLOTLIB_INSTALLED = True
except ImportError:
    _MATPLOTLIB_INSTALLED = False

# --- Statistical Helper Functions (for fallback) ---
T_VALUES = {
    2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201
}

def mean(data):
    return sum(data) / len(data)

def std(data):
    n = len(data)
    if n < 2:
        return 0
    m = mean(data)
    ss = sum((x - m) ** 2 for x in data)
    return sqrt(ss / (n - 1))

def percentile(data, p):
    sorted_data = sorted(data)
    n = len(sorted_data)
    idx = (p / 100) * (n - 1)
    if idx.is_integer():
        return sorted_data[int(idx)]
    else:
        lower_idx = floor(idx)
        upper_idx = lower_idx + 1
        fraction = idx - lower_idx
        return sorted_data[lower_idx] + (sorted_data[upper_idx] - sorted_data[lower_idx]) * fraction

def iqr(data):
    q1 = percentile(data, 25)
    q3 = percentile(data, 75)
    return q3 - q1

def median(data):
    return percentile(data, 50)

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="A simple period tracker.")
    parser.add_argument("file", nargs="?", default="--",
                        help="Path to the CSV file with period dates. Use '--' to read from stdin.")
    parser.add_argument("--luteal-phase", type=int, default=None,
                        help="Days between ovulation and period (default: 14, or calculated from data).")
    parser.add_argument("--safe-days-buffer", type=int, default=5,
                        help="Days after ovulation confidence interval to start 'safe' days (default: 5).")
    parser.add_argument("--period-duration", type=int, default=4,
                        help="Default period duration in days (default: 4).")
    parser.add_argument("--calendar", action="store_true",
                        help="Display an ASCII calendar with predictions.")
    parser.add_argument("--months", type=int, default=3, choices=range(1, 4),
                        help="Number of months to display in the calendar (1-3, default: 3).")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable color output in the calendar.")
    parser.add_argument("--hatch", action="store_true",
                        help="Use hatch patterns instead of filled colors for events in the figure.")
    parser.add_argument("--figure-path", type=str, default=None,
                        help="Path to save the calendar as a PDF figure.")
    parser.add_argument("--ci-method", type=str, default="minmax", choices=["minmax", "normal"],
                        help="Method for period/ovulation confidence interval: 'minmax' (default, uses last year's min/max cycle length) or 'normal' (uses a 95%% prediction interval based on a normal distribution).")

    return parser.parse_args()

def read_from_stdin():
    """Reads dates from standard input."""
    dates = []
    add_period_end = input("Do you want to add period end dates? (y/N): ").strip().lower() == 'y'
    add_ovulation = input("Do you want to add ovulation dates? (y/N): ").strip().lower() == 'y'

    print("Enter period start dates (YYYY-MM-DD), one per line. Finish with a blank line.")
    while True:
        period_date = sys.stdin.readline().strip()
        if not period_date:
            break
        
        period_end_date = ''
        if add_period_end:
            period_end_date = input(f"  Period end date for start {period_date} (optional, YYYY-MM-DD): ").strip()

        ovulation_date = ''
        if add_ovulation:
            ovulation_date = input(f"  Ovulation date for period starting {period_date} (optional, YYYY-MM-DD): ").strip()

        dates.append((period_date, period_end_date, ovulation_date))
    
    return dates

def read_from_file(filepath):
    """Reads dates from a CSV file with resilience."""
    if _PANDAS_INSTALLED:
        try:
            # Using a comment character '#' to allow for comments in the file
            df = pd.read_csv(filepath, comment='#', skip_blank_lines=True)
            df = df.dropna(how='all') # Drop rows that are all NaN
            df.columns = [str(col).lower().strip() for col in df.columns]

            column_map = {'start': None, 'end': None, 'ovulation': None}
            
            # Try to map columns by header names
            for col in df.columns:
                if 'period_start' in col or ('period' in col and 'end' not in col):
                    column_map['start'] = col
                elif 'period_end' in col:
                    column_map['end'] = col
                elif 'ovulation' in col:
                    column_map['ovulation'] = col

            # If headers are not recognized or missing, assume order
            if column_map['start'] is None:
                if len(df.columns) > 0: column_map['start'] = df.columns[0]
                if len(df.columns) > 1: column_map['end'] = df.columns[1]
                if len(df.columns) > 2: column_map['ovulation'] = df.columns[2]

            dates = []
            for _, row in df.iterrows():
                start = row[column_map['start']] if column_map['start'] and not pd.isna(row[column_map['start']]) else ''
                end = row[column_map['end']] if column_map['end'] and not pd.isna(row[column_map['end']]) else ''
                ovulation = row[column_map['ovulation']] if column_map['ovulation'] and not pd.isna(row[column_map['ovulation']]) else ''
                
                if start:
                    # Taking only the date part if datetime is provided
                    dates.append((str(start).split()[0], str(end).split()[0], str(ovulation).split()[0]))
            return dates
        except Exception as e:
            print(f"Pandas read failed: {e}, falling back to basic CSV reader.", file=sys.stderr)

    # Fallback to basic CSV reader
    with open(filepath, 'r') as f:
        lines = [line for line in f if line.strip() and not line.strip().startswith('#')]

    if not lines:
        return []

    reader = csv.reader(lines)
    all_rows = list(reader)

    header = [h.lower().strip() for h in all_rows[0]]
    data_rows = all_rows
    
    start_idx, end_idx, ovulation_idx = 0, 1, 2 # Default column order

    # Check for known header keys to override default order
    if any(key in header for key in ['period', 'period_start', 'period_end', 'ovulation']):
        data_rows = all_rows[1:]
        start_idx, end_idx, ovulation_idx = -1, -1, -1
        for i, h in enumerate(header):
            if 'period_start' in h or ('period' in h and 'end' not in h):
                start_idx = i
            elif 'period_end' in h:
                end_idx = i
            elif 'ovulation' in h:
                ovulation_idx = i
        if start_idx == -1: start_idx = 0 # Default to first column if no start date found in header

    dates = []
    for row in data_rows:
        if not row: continue
        start = row[start_idx] if start_idx < len(row) else ''
        end = row[end_idx] if end_idx != -1 and end_idx < len(row) else ''
        ovulation = row[ovulation_idx] if ovulation_idx != -1 and ovulation_idx < len(row) else ''
        if start.strip():
            dates.append((start.strip(), end.strip(), ovulation.strip()))
            
    return dates

def calculate_cycle_lengths(dates):
    """Calculates cycle lengths from a list of dates."""
    if len(dates) < 2:
        return []
    
    cycle_lengths = []
    for i in range(1, len(dates)):
        cycle_length = (dates[i] - dates[i-1]).days
        cycle_lengths.append(cycle_length)
    return cycle_lengths

def generate_calendar_text(start_date, months, predictions, use_color, last_period_duration, predicted_period_duration):
    """Generates an ASCII calendar with predictions."""
    colors = {
        'L': '\033[91m', 'P': '\033[95m', 'p': '\033[31m',
        'O': '\033[94m', 'o': '\033[34m', 'S': '\033[92m', 'END': '\033[0m'
    }
    if not use_color or sys.platform == 'win32':
        colors = {k: '' for k in colors}

    cal_text = "\n--- Calendar ---\n"
    cal_text += f"Legend: {colors['L']}[L]ast Period{colors['END']}, {colors['P']}[P]redicted Period{colors['END']}, {colors['p']}[p]eriod CI{colors['END']}, {colors['O']}[O]vulation{colors['END']}, {colors['o']}[o]vulation CI{colors['END']}, {colors['S']}[S]afe Days{colors['END']}\n\n"

    current_month = start_date.month
    current_year = start_date.year

    for _ in range(months):
        cal_text += f"{calendar.month_name[current_month]} {current_year}\n"
        cal_text += " Mo  Tu  We  Th  Fr  Sa  Su\n"
        
        month_cal = calendar.monthcalendar(current_year, current_month)

        for week in month_cal:
            week_text = ""
            for day in week:
                if day == 0:
                    week_text += "    "
                    continue

                date = datetime(current_year, current_month, day)
                marker, color_key = " ", ''

                if date.date() >= predictions['safe_days_start'].date() and date.date() < predictions['next_period_ci_low'].date():
                    marker, color_key = "S", 'S'
                if predictions['ovulation_ci_low'].date() <= date.date() <= predictions['ovulation_ci_high'].date():
                    marker, color_key = "o", 'o'
                if predictions['next_period_ci_low'].date() <= date.date() <= predictions['next_period_ci_high'].date():
                    marker, color_key = "p", 'p'
                
                predicted_period_end_date = predictions['next_period_est'].date() + timedelta(days=predicted_period_duration - 1)
                if predictions['next_period_est'].date() <= date.date() <= predicted_period_end_date:
                    marker, color_key = "P", 'P'

                last_period_end_date = predictions['last_period'].date() + timedelta(days=last_period_duration - 1)
                if predictions['last_period'].date() <= date.date() <= last_period_end_date:
                    marker, color_key = "L", 'L'

                if predictions['ovulation_est'].date() == date.date():
                    marker, color_key = "O", 'O'

                if marker != " ":
                    entry = f"{marker}{day}"
                    week_text += f"{colors[color_key]}{entry: >3}{colors['END']} "
                else:
                    entry = str(day)
                    week_text += f"{entry: >3} "

            cal_text += week_text.rstrip() + "\n"
        cal_text += "\n"

        current_month = (current_month % 12) + 1
        if current_month == 1:
            current_year += 1
            
    return cal_text

def generate_calendar_figure(start_date, months, predictions, all_parsed_dates, figure_path, last_period_duration, predicted_period_duration, use_hatch=False):
    """Generates a graphical calendar and saves it as a PDF."""
    if not _MATPLOTLIB_INSTALLED:
        print("Matplotlib not installed. Cannot generate figure.", file=sys.stderr)
        return

    fig, axes = plt.subplots(months, 1, figsize=(4, 2.5 * months), layout='constrained') # Adjusted figsize for better aspect ratio
    if months == 1:
        axes = [axes]

    # Colors matching the text calendar
    color_map = {
        'L': 'indianred',      # Past Period - red
        'P': 'deeppink',       # Predicted Period - magenta
        'p': 'lightpink',      # Period CI - light red
        'O': 'indigo',         # Ovulation (from data) - blue
        'O_est': 'darkviolet', # Ovulation (estimated)
        'o': 'cornflowerblue', # Ovulation CI - light blue
        'S': 'limegreen',      # Safe Days - green
    }
    # Hatches for different event types
    universal_hatch = '///' # Define a single hatch pattern
    hatch_map = {
        'L': universal_hatch,
        'P': universal_hatch,
        'p': universal_hatch,
        'O': universal_hatch,
        'O_est': universal_hatch,
        'o': universal_hatch,
        'S': universal_hatch,
    }
    
    current_month = start_date.month
    current_year = start_date.year
    today = datetime.now().date()

    for i in range(months):
        ax = axes[i]
        ax.set_ylabel(f"{calendar.month_name[current_month]} {current_year}", fontsize=14, labelpad=10)
        ax.set_xticks([]) # No ticks on x-axis
        ax.set_yticks([]) # No ticks on y-axis
        ax.invert_yaxis() # Days start from top

        # Add weekday labels to the top of the first month's calendar
        if i == 0:
            for day_idx, day_name in enumerate(['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']):
                color = 'firebrick' if day_idx in [5, 6] else 'black'
                ax.text(day_idx, -1, day_name, ha='center', va='center',
                        fontsize=10, fontweight='bold', color=color)

        month_cal = calendar.monthcalendar(current_year, current_month)
        
        for week_idx, week in enumerate(month_cal):
            for day_idx, day in enumerate(week):
                if day == 0:
                    # Make empty days white
                    rect = patches.Rectangle((day_idx - 0.5, week_idx - 0.5), 1, 1,
                                             facecolor='white', edgecolor='none')
                    ax.add_patch(rect)
                    continue
                
                date = datetime(current_year, current_month, day)
                event_color = 'none'
                is_ovulation_day = False
                color_key = None
                
                # Color precedence should be from least specific to most specific
                # Safe days
                if predictions['safe_days_start'].date() <= date.date() < predictions['next_period_ci_low'].date():
                    color_key = 'S'
                
                # Confidence intervals
                if predictions['ovulation_ci_low'].date() <= date.date() <= predictions['ovulation_ci_high'].date():
                    color_key = 'o'
                if predictions['next_period_ci_low'].date() <= date.date() <= predictions['next_period_ci_high'].date():
                    color_key = 'p'

                # Predicted period
                predicted_period_end_date = predictions['next_period_est'].date() + timedelta(days=predicted_period_duration - 1)
                if predictions['next_period_est'].date() <= date.date() <= predicted_period_end_date:
                    color_key = 'P'

                # Exact predictions
                if predictions['ovulation_est'].date() == date.date():
                    color_key = 'O'
                    is_ovulation_day = True
                
                # Historical data (always on top, overriding future predictions if they overlap)
                # Determine the most specific historical event for this day.
                historical_color_key = None
                is_past_period = any(
                    e.get('start') and e.get('end') and e['start'].date() <= date.date() <= e['end'].date()
                    for e in all_parsed_dates
                )
                
                # Check for ovulation, distinguishing between provided and estimated
                past_ovulation_event = next((e for e in all_parsed_dates if e.get('ovulation') and e['ovulation'].date() == date.date()), None)

                if is_past_period:
                    historical_color_key = 'L'
                elif past_ovulation_event:
                    if past_ovulation_event.get('ovulation_estimated'):
                        historical_color_key = 'O_est'
                    else:
                        historical_color_key = 'O'
                
                if historical_color_key: color_key = historical_color_key

                rect_props = {'facecolor': 'none', 'edgecolor': 'gray', 'linestyle': ':', 'linewidth': 0.5}
                if color_key:
                    event_color = color_map[color_key]
                    if use_hatch:
                        rect_props.update(facecolor='none', hatch=hatch_map.get(color_key, universal_hatch), edgecolor=event_color, alpha=0.3)
                    else:
                        rect_props.update(facecolor=event_color, alpha=0.3)
                
                rect = patches.Rectangle((day_idx - 0.5, week_idx - 0.5), 1, 1, **rect_props)
                ax.add_patch(rect)

                # Highlight weekends
                text_props = {'ha': 'center', 'va': 'center'}
                if day_idx in [5, 6]: # Saturday or Sunday
                    text_props['fontweight'] = 'bold'
                    text_props['color'] = 'firebrick'
                
                txt = ax.text(day_idx, week_idx, str(day), **text_props)

                # Underline predicted ovulation day
                if is_ovulation_day:
                    # Draw a simple horizontal line under the ovulation day number.
                    # This is more robust than using patheffects across matplotlib versions.
                    ax.plot([day_idx - 0.2, day_idx + 0.2], [week_idx + 0.2, week_idx + 0.2], color=color_map['O'], linewidth=1, alpha=0.5)

                # Highlight today's date by drawing a new box over it
                if date.date() == today:
                    highlight_rect = patches.Rectangle((day_idx - 0.5, week_idx - 0.5), 1, 1,
                                                       facecolor='none', edgecolor='dimgray',
                                                       linewidth=2, linestyle='solid',
                                                       alpha=1, zorder=5)
                    ax.add_patch(highlight_rect)

        # Adjust contour of the months
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        ax.set_xlim(-0.5, 6.5)
        if i == 0:
            ax.set_ylim(len(month_cal) - 0.5, -1.5) # Adjust ylim to make space for weekday labels
        else:
            ax.set_ylim(len(month_cal) - 0.25, -0.75) # Tighter ylim for subsequent months

        current_month = (current_month % 12) + 1
        if current_month == 1:
            current_year += 1

    # Create legend
    legend_patches = []
    legend_items = [
        ('Past Period', 'L'), ('Predicted Period', 'P'), ('Period CI', 'p'),
        ('Past Ovulation', 'O'), ('Ovulation (est)', 'O_est'),
        ('Ovulation CI', 'o'), ('Safe Days', 'S')
    ]
    for label, key in legend_items:
        color = color_map[key]
        if use_hatch:
            patch = patches.Patch(facecolor='white', edgecolor=color, hatch=hatch_map.get(key, universal_hatch), label=label, alpha=0.3)
        else:
            patch = patches.Patch(facecolor=color, label=label, alpha=0.3)
        legend_patches.append(patch)

    # Add a patch for "Today"
    today_patch = patches.Patch(facecolor='none', edgecolor='dimgray', linewidth=2, linestyle='solid', label='Today')
    legend_patches.append(today_patch)

    
    # Adjust subplots to make room for the legend, reduce space between months, and reduce top margin
    # With layout='constrained', manual adjustments like subplots_adjust are not needed.

    fig.legend(handles=legend_patches, loc='outside lower center', ncol=2)
    
    plt.savefig(figure_path, format='pdf')
    print(f"\nCalendar figure saved to {figure_path}")

def main():
    """Main function."""
    args = parse_arguments()

    raw_dates = read_from_file(args.file) if args.file != '--' else read_from_stdin()

    if not raw_dates:
        print("No dates provided. Exiting.")
        return

    parsed_dates = []
    for start_str, end_str, ovulation_str in raw_dates:
        try:
            start = datetime.fromisoformat(start_str) if start_str else None
            end = datetime.fromisoformat(end_str) if end_str else None
            ovulation = datetime.fromisoformat(ovulation_str) if ovulation_str else None
            if start:
                parsed_dates.append({'start': start, 'end': end, 'ovulation': ovulation})
        except ValueError:
            print(f"Skipping row with invalid date format: {(start_str, end_str, ovulation_str)}", file=sys.stderr)
            continue
    
    if not parsed_dates:
        print("No valid dates found. Exiting.")
        return

    parsed_dates.sort(key=lambda d: d['start'])
    period_dates = sorted([d['start'] for d in parsed_dates])

    period_durations = []
    for d in parsed_dates:
        if d['start'] and d['end']:
            duration = (d['end'] - d['start']).days + 1
            if duration > 0:
                period_durations.append(duration)

    # Estimate missing end dates for historical periods before rendering
    median_period_duration = int(median(period_durations)) if period_durations else args.period_duration
    for entry in parsed_dates:
        if entry['start'] and not entry['end']:
            entry['end'] = entry['start'] + timedelta(days=median_period_duration - 1)


    luteal_phase_durations = []
    for i in range(len(parsed_dates) - 1):
        if parsed_dates[i]['ovulation'] and parsed_dates[i+1]['start']:
            duration = (parsed_dates[i+1]['start'] - parsed_dates[i]['ovulation']).days
            if duration > 0:
                luteal_phase_durations.append(duration)

    if len(period_dates) < 2:
        print("Not enough data to calculate cycle lengths (need at least 2 dates).")
        return

    all_cycle_lengths = calculate_cycle_lengths(period_dates)

    last_year_cutoff = period_dates[-1] - timedelta(days=365)
    recent_dates = [d for d in period_dates if d >= last_year_cutoff]
    recent_cycle_lengths = calculate_cycle_lengths(recent_dates) if len(recent_dates) > 1 else all_cycle_lengths
    
    if not recent_cycle_lengths:
        print("Not enough data to make predictions.")
        return

    if _SCIPY_INSTALLED and _PANDAS_INSTALLED:
        mean_length, std_length = np.mean(recent_cycle_lengths), np.std(recent_cycle_lengths, ddof=1)
        median_length, iqr_val = np.median(recent_cycle_lengths), np.subtract(*np.percentile(recent_cycle_lengths, [75, 25]))
        min_12m, max_12m = np.min(recent_cycle_lengths), np.max(recent_cycle_lengths)
        min_all, max_all = np.min(all_cycle_lengths), np.max(all_cycle_lengths)
        
        df = len(recent_cycle_lengths) - 1
        t_val = t.ppf(0.975, df) if df > 0 else 1.96
        ci_low = mean_length - t_val * std_length
        ci_high = mean_length + t_val * std_length
    else:
        mean_length, std_length = mean(recent_cycle_lengths), std(recent_cycle_lengths)
        median_length, iqr_val = median(recent_cycle_lengths), iqr(recent_cycle_lengths)
        min_12m, max_12m = min(recent_cycle_lengths), max(recent_cycle_lengths)
        min_all, max_all = min(all_cycle_lengths), max(all_cycle_lengths)

        df = len(recent_cycle_lengths) - 1
        if df in T_VALUES:
            t_val = T_VALUES[df]
            ci_low = mean_length - t_val * std_length
            ci_high = mean_length + t_val * std_length
        else:
            ci_low, ci_high = "N/A", "N/A"

    # --- Luteal Phase Calculation ---
    luteal_phase_range_low, luteal_phase_range_high = None, None
    if args.luteal_phase is not None:
        luteal_phase_for_prediction = args.luteal_phase
    else:
        if luteal_phase_durations:
            luteal_phase_for_prediction = int(median(luteal_phase_durations))
            # Calculate range for luteal phase if enough data, respecting ci-method
            if len(luteal_phase_durations) >= 3:
                if args.ci_method == 'normal':
                    if _SCIPY_INSTALLED:
                        luteal_mean = np.mean(luteal_phase_durations)
                        luteal_std = np.std(luteal_phase_durations, ddof=1)
                        luteal_df = len(luteal_phase_durations) - 1
                        luteal_t_val = t.ppf(0.975, luteal_df)
                        margin = luteal_t_val * luteal_std / sqrt(luteal_df + 1)
                        luteal_phase_range_low = luteal_mean - margin
                        luteal_phase_range_high = luteal_mean + margin
                    else: # Fallback for normal
                        luteal_df = len(luteal_phase_durations) - 1
                        if luteal_df in T_VALUES:
                            luteal_mean = mean(luteal_phase_durations)
                            luteal_std = std(luteal_phase_durations)
                            luteal_t_val = T_VALUES[luteal_df]
                            margin = luteal_t_val * luteal_std / sqrt(luteal_df + 1)
                            luteal_phase_range_low = luteal_mean - margin
                            luteal_phase_range_high = luteal_mean + margin
                else: # minmax
                    luteal_phase_range_low = min(luteal_phase_durations)
                    luteal_phase_range_high = max(luteal_phase_durations)
        else:
            luteal_phase_for_prediction = 14

    # Estimate missing historical ovulation dates
    for i in range(len(parsed_dates) - 1):
        if parsed_dates[i]['start'] and not parsed_dates[i]['ovulation']:
            next_period_start = parsed_dates[i+1]['start']
            # Ovulation is estimated relative to the *next* period's start
            parsed_dates[i]['ovulation'] = next_period_start - timedelta(days=luteal_phase_for_prediction)
            parsed_dates[i]['ovulation_estimated'] = True

    last_period_date = period_dates[-1]
    next_period_est = last_period_date + timedelta(days=int(median_length))

    if args.ci_method == 'normal' and ci_low != "N/A":
        # Use a 95% prediction interval for the next cycle length.
        # PI = mean +/- t * s * sqrt(1 + 1/n)
        n = len(recent_cycle_lengths)
        prediction_margin = t_val * std_length * sqrt(1 + 1/n)
        pi_low = mean_length - prediction_margin
        pi_high = mean_length + prediction_margin
        next_period_ci_low = last_period_date + timedelta(days=int(pi_low))
        next_period_ci_high = last_period_date + timedelta(days=int(pi_high))
    else: # Default to minmax
        next_period_ci_low = last_period_date + timedelta(days=int(min_12m))
        next_period_ci_high = last_period_date + timedelta(days=int(max_12m))

    # --- Ovulation Prediction ---
    ovulation_est = next_period_est - timedelta(days=luteal_phase_for_prediction) # Based on median

    if luteal_phase_range_low is not None and luteal_phase_range_high is not None:
        ovulation_ci_low = next_period_ci_low - timedelta(days=int(round(luteal_phase_range_high)))
        ovulation_ci_high = next_period_ci_high - timedelta(days=int(round(luteal_phase_range_low)))
    else: # Use single value for luteal phase
        ovulation_ci_low = next_period_ci_low - timedelta(days=luteal_phase_for_prediction)
        ovulation_ci_high = next_period_ci_high - timedelta(days=luteal_phase_for_prediction)

    safe_days_start = ovulation_ci_high + timedelta(days=args.safe_days_buffer)

    print("\n--- Period Statistics (last 12 months) ---")
    print(f"Mean cycle length: {mean_length:.2f} days")
    print(f"Std dev of cycle length: {std_length:.2f} days")
    if ci_low != "N/A":
        print(f"95% Confidence Interval for mean: [{ci_low:.2f}, {ci_high:.2f}] days")
    print(f"Median cycle length: {median_length:.2f} days")
    print(f"Interquartile Range (IQR): {iqr_val:.2f} days")
    print(f"Min/Max cycle length (12m): {min_12m} / {max_12m} days")
    print(f"Min/Max cycle length (all time): {min_all} / {max_all} days")

    if period_durations:
        print("\n--- Period Duration Statistics ---")
        print(f"Mean period duration: {mean(period_durations):.2f} days")
        print(f"Median period duration: {median(period_durations):.2f} days")
        print(f"Std dev of period duration: {std(period_durations):.2f} days")
        print(f"Min/Max period duration: {min(period_durations)} / {max(period_durations)} days")

    if luteal_phase_durations:
        print("\n--- Luteal Phase Statistics ---")
        print(f"Median luteal phase duration: {median(luteal_phase_durations):.2f} days")
        if luteal_phase_range_low is not None:
            if args.ci_method == 'normal':
                print(f"95% Confidence Interval for mean: [{luteal_phase_range_low:.2f}, {luteal_phase_range_high:.2f}] days")
            else: # minmax
                print(f"Min/Max luteal phase duration: {luteal_phase_range_low} / {luteal_phase_range_high} days")


    print("\n--- Next Cycle Predictions ---")
    print(f"Next Period Estimate: {next_period_est.strftime('%Y-%m-%d')}")
    print(f"  Confidence Interval: [{next_period_ci_low.strftime('%Y-%m-%d')} to {next_period_ci_high.strftime('%Y-%m-%d')}]")
    print(f"Estimated Ovulation: {ovulation_est.strftime('%Y-%m-%d')}")
    print(f"  Confidence Interval: [{ovulation_ci_low.strftime('%Y-%m-%d')} to {ovulation_ci_high.strftime('%Y-%m-%d')}]")
    print(f"'Safe' days likely start after: {safe_days_start.strftime('%Y-%m-%d')}")

    # Determine period durations for calendar
    last_period_duration = args.period_duration
    if parsed_dates[-1]['end']:
        last_period_duration = (parsed_dates[-1]['end'] - parsed_dates[-1]['start']).days + 1
    elif period_durations:
        last_period_duration = int(median(period_durations))

    predicted_period_duration = int(median(period_durations)) if period_durations else args.period_duration

    if args.calendar:
        predictions = {
            'last_period': last_period_date, 'next_period_est': next_period_est,
            'next_period_ci_low': next_period_ci_low, 'next_period_ci_high': next_period_ci_high,
            'ovulation_est': ovulation_est, 'ovulation_ci_low': ovulation_ci_low,
            'ovulation_ci_high': ovulation_ci_high, 'safe_days_start': safe_days_start
        }
        calendar_text = generate_calendar_text(last_period_date, args.months, predictions, not args.no_color, last_period_duration, predicted_period_duration)
        print(calendar_text)

    if args.figure_path:
        if not _MATPLOTLIB_INSTALLED:
            print("\nMatplotlib is not installed. Please install it to generate figures.", file=sys.stderr)
        else:
            predictions = {
                'last_period': last_period_date, 'next_period_est': next_period_est,
                'next_period_ci_low': next_period_ci_low, 'next_period_ci_high': next_period_ci_high,
                'ovulation_est': ovulation_est, 'ovulation_ci_low': ovulation_ci_low,
                'ovulation_ci_high': ovulation_ci_high, 'safe_days_start': safe_days_start
            }
        generate_calendar_figure(last_period_date, args.months, predictions, parsed_dates, args.figure_path, last_period_duration, predicted_period_duration, use_hatch=args.hatch)

if __name__ == "__main__":
    main()