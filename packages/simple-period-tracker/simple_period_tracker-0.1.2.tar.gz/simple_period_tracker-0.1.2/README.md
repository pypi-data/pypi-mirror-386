# Simple Period Tracker

[GitLab Repository](https://gitlab.com/aufildelanuit/period-tracker)


A simple, command-line period tracker with statistical analysis and prediction.

## Features

-   Calculates cycle lengths and provides statistics (mean, median, standard deviation).
-   Predicts next period and ovulation dates with confidence intervals.
-   Displays an ASCII calendar in the terminal with predictions.
-   Generates a graphical calendar as a PDF file.
-   Reads data from CSV files or standard input.
-   Optional support for `pandas`, `numpy`, `scipy`, and `matplotlib` for more advanced analysis and visualization.

## Installation

You can install `simple-period-tracker` using `pip`:

```bash
pip install simple-period-tracker
```

Or, if you have cloned the repository, you can install it with `poetry`:

```bash
poetry install
```

## Usage

```bash
simple-period-tracker [OPTIONS] [FILE]
```

### Arguments

-   `FILE`: Path to the CSV file with period dates. Use `--` to read from stdin.

### Options

-   `--luteal-phase DAYS`: Days between ovulation and period (default: 14, or calculated from data).
-   `--safe-days-buffer DAYS`: Days after ovulation confidence interval to start 'safe' days (default: 5).
-   `--period-duration DAYS`: Default period duration in days (default: 4).
-   `--calendar`: Display an ASCII calendar with predictions.
-   `--months MONTHS`: Number of months to display in the calendar (1-3, default: 3).
-   `--no-color`: Disable color output in the calendar.
-   `--hatch`: Use hatch patterns instead of filled colors for events in the figure.
-   `--figure-path PATH`: Path to save the calendar as a PDF figure.
-   `--ci-method METHOD`: Method for period/ovulation confidence interval: 'minmax' (default) or 'normal'.

### CSV File Format

The CSV file should have a header row and at least one column for the period start dates. The columns can be in any order, but the header must contain `period_start`, `period_end`, and `ovulation`.

Example:

```csv
period_start,period_end,ovulation
2023-01-01,2023-01-05,2023-01-15
2023-01-30,2023-02-03,2023-02-13
```

## License

This project is licensed under the MIT License.
