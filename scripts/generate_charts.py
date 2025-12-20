#!/usr/bin/env python3
"""
Crime Statistics Visualization Script
Generates comprehensive charts from Azerbaijan crime statistics (1993-2024)

Author: Data Analytics Team
Date: December 2024
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure matplotlib
matplotlib.use('Agg')  # Non-interactive backend
plt.style.use('seaborn-v0_8-darkgrid')

# Set default chart parameters
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

# Create charts directory if it doesn't exist
os.makedirs('charts', exist_ok=True)

print("="*80)
print("CRIME STATISTICS VISUALIZATION GENERATOR")
print("="*80)
print()

# ==================== CHART 1: Total Crimes Over Time ====================
def generate_chart_01():
    """Generate total crimes trend chart (1993-2024)"""
    print("1. Generating total crimes trend chart...")

    df1 = pd.read_excel('data/003_1.xls', sheet_name='3.1')
    years = df1.iloc[2, 2:].values.astype(int)
    total_crimes = df1.iloc[3, 2:].values.astype(int)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(years, total_crimes, marker='o', linewidth=2.5, markersize=6, color='#2E86AB')
    ax.fill_between(years, total_crimes, alpha=0.3, color='#2E86AB')

    # Add value labels for key years
    key_years_idx = [0, 10, 20, 30, 31]  # 1993, 2003, 2013, 2023, 2024
    for idx in key_years_idx:
        if idx < len(years):
            ax.annotate(f'{int(total_crimes[idx]):,}',
                       xy=(years[idx], total_crimes[idx]),
                       xytext=(0, 10), textcoords='offset points',
                       ha='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

    ax.set_xlabel('Year', fontweight='bold')
    ax.set_ylabel('Number of Crimes', fontweight='bold')
    ax.set_title('Total Registered Crimes in Azerbaijan (1993-2024)', fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))

    plt.tight_layout()
    plt.savefig('charts/01_total_crimes_trend.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/01_total_crimes_trend.png")


# ==================== CHART 2: Crime Types Distribution 2024 ====================
def generate_chart_02():
    """Generate crime types distribution chart for 2024"""
    print("2. Generating crime types distribution chart (2024)...")

    df1 = pd.read_excel('data/003_1.xls', sheet_name='3.1')

    crime_types = [
        'Murder & Attempt',
        'Serious Harm',
        'Rape & Attempt',
        'Theft',
        'Fraud',
        'Robbery',
        'Banditry',
        'Hooliganism',
        'Drug Crimes',
        'Traffic Violations'
    ]
    crime_values_2024 = [
        df1.iloc[5, -1],   # Murder & attempt
        df1.iloc[7, -1],   # Serious harm
        df1.iloc[8, -1],   # Rape
        df1.iloc[9, -1],   # Theft
        df1.iloc[10, -1],  # Fraud
        df1.iloc[11, -1],  # Robbery
        df1.iloc[12, -1],  # Banditry
        df1.iloc[13, -1],  # Hooliganism
        df1.iloc[14, -1],  # Drug crimes
        df1.iloc[15, -1],  # Traffic
    ]

    # Sort by value
    sorted_indices = np.argsort(crime_values_2024)[::-1]
    sorted_types = [crime_types[i] for i in sorted_indices]
    sorted_values = [crime_values_2024[i] for i in sorted_indices]

    fig, ax = plt.subplots(figsize=(14, 10))
    colors = plt.cm.Spectral(np.linspace(0, 1, len(sorted_types)))
    bars = ax.barh(sorted_types, sorted_values, color=colors, edgecolor='black', linewidth=0.7)

    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, sorted_values)):
        width = bar.get_width()
        ax.text(width + 100, bar.get_y() + bar.get_height()/2,
                f'{int(value):,}',
                ha='left', va='center', fontweight='bold', fontsize=11)

    ax.set_xlabel('Number of Crimes', fontweight='bold')
    ax.set_title('Crime Types Distribution in Azerbaijan - 2024', fontsize=16, fontweight='bold', pad=20)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig('charts/02_crime_types_2024.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/02_crime_types_2024.png")


# ==================== CHART 3: Top Crimes Trend (2014-2024) ====================
def generate_chart_03():
    """Generate top crimes trend chart (2014-2024)"""
    print("3. Generating top crimes trend chart...")

    df1 = pd.read_excel('data/003_1.xls', sheet_name='3.1')
    years_recent = df1.iloc[2, -11:].values.astype(int)  # Last 11 years
    theft = df1.iloc[9, -11:].values.astype(float)
    fraud = df1.iloc[10, -11:].values.astype(float)
    drugs = df1.iloc[14, -11:].values.astype(float)
    traffic = df1.iloc[15, -11:].values.astype(float)

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(years_recent, theft, marker='o', linewidth=2.5, markersize=7, label='Theft', color='#E63946')
    ax.plot(years_recent, fraud, marker='s', linewidth=2.5, markersize=7, label='Fraud', color='#F77F00')
    ax.plot(years_recent, drugs, marker='^', linewidth=2.5, markersize=7, label='Drug Crimes', color='#06A77D')
    ax.plot(years_recent, traffic, marker='d', linewidth=2.5, markersize=7, label='Traffic Violations', color='#4361EE')

    # Add final year value labels
    for data, label, color in [(theft, 'Theft', '#E63946'),
                                (fraud, 'Fraud', '#F77F00'),
                                (drugs, 'Drug Crimes', '#06A77D'),
                                (traffic, 'Traffic', '#4361EE')]:
        ax.annotate(f'{int(data[-1]):,}',
                   xy=(years_recent[-1], data[-1]),
                   xytext=(10, 0), textcoords='offset points',
                   ha='left', fontsize=10, fontweight='bold',
                   color=color)

    ax.set_xlabel('Year', fontweight='bold')
    ax.set_ylabel('Number of Crimes', fontweight='bold')
    ax.set_title('Top Crime Categories Trend (2014-2024)', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))

    plt.tight_layout()
    plt.savefig('charts/03_top_crimes_trend.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/03_top_crimes_trend.png")


# ==================== CHART 4: Demographics - Gender & Age ====================
def generate_chart_04():
    """Generate criminal demographics chart (gender & age)"""
    print("4. Generating demographics chart (Gender & Age)...")

    df11 = pd.read_excel('data/003_11.xls', sheet_name='3.11')

    # Gender data
    males_2024 = df11.iloc[6, -1]
    females_2024 = df11.iloc[7, -1]
    total_gender = males_2024 + females_2024

    # Age data
    age_14_15 = df11.iloc[9, -1]
    age_16_17 = df11.iloc[10, -1]
    age_18_24 = df11.iloc[11, -1]
    age_25_29 = df11.iloc[12, -1]
    age_30_plus = df11.iloc[13, -1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 10))

    # Gender pie chart
    gender_data = [males_2024, females_2024]
    colors_gender = ['#4361EE', '#F72585']
    explode_gender = (0.05, 0.05)

    wedges, texts, autotexts = ax1.pie(gender_data, autopct='%1.1f%%',
                                         colors=colors_gender, explode=explode_gender,
                                         shadow=True, startangle=90, pctdistance=0.85,
                                         textprops={'fontsize': 13, 'fontweight': 'bold', 'color': 'white'})

    ax1.set_title('Criminals by Gender - 2024', fontsize=15, fontweight='bold', pad=20)

    # Legend with values
    legend_labels_gender = [
        f'Males: {int(males_2024):,} ({males_2024/total_gender*100:.1f}%)',
        f'Females: {int(females_2024):,} ({females_2024/total_gender*100:.1f}%)'
    ]
    ax1.legend(wedges, legend_labels_gender, loc='upper left', bbox_to_anchor=(-0.2, 1),
              fontsize=12, frameon=True, fancybox=True, shadow=True)

    # Age distribution bar chart
    age_labels = ['14-15', '16-17', '18-24', '25-29', '30+']
    age_data = [age_14_15, age_16_17, age_18_24, age_25_29, age_30_plus]
    total_age = sum(age_data)
    colors_age = plt.cm.viridis(np.linspace(0.2, 0.9, len(age_labels)))

    bars = ax2.bar(age_labels, age_data, color=colors_age, edgecolor='black', linewidth=1.5)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}\n({height/total_age*100:.1f}%)',
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax2.set_ylabel('Number of Criminals', fontweight='bold')
    ax2.set_xlabel('Age Group', fontweight='bold')
    ax2.set_title('Criminals by Age Group - 2024', fontsize=15, fontweight='bold', pad=20)
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('charts/04_demographics_gender_age.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/04_demographics_gender_age.png")


# ==================== CHART 5: Employment Status ====================
def generate_chart_05():
    """Generate employment status chart"""
    print("5. Generating employment status chart...")

    df11 = pd.read_excel('data/003_11.xls', sheet_name='3.11')

    employment_categories = [
        'Workers',
        'Employees',
        'Agr. Workers',
        'Business',
        'Finance/Bank',
        'Government',
        'Students',
        'Unemployed',
        'Other'
    ]
    employment_data = [
        df11.iloc[15, -1],  # Workers
        df11.iloc[16, -1],  # Employees
        df11.iloc[17, -1],  # Agriculture
        df11.iloc[18, -1],  # Business
        df11.iloc[19, -1],  # Finance
        df11.iloc[20, -1],  # Government
        df11.iloc[21, -1],  # Students
        df11.iloc[22, -1],  # Unemployed
        df11.iloc[23, -1],  # Other
    ]

    # Sort by value
    sorted_indices = np.argsort(employment_data)[::-1]
    sorted_categories = [employment_categories[i] for i in sorted_indices]
    sorted_employment = [employment_data[i] for i in sorted_indices]

    fig, ax = plt.subplots(figsize=(14, 10))
    colors = plt.cm.Paired(np.linspace(0, 1, len(sorted_categories)))
    bars = ax.barh(sorted_categories, sorted_employment, color=colors, edgecolor='black', linewidth=0.8)

    # Add value labels and percentages
    total_employment = sum(sorted_employment)
    for i, (bar, value) in enumerate(zip(bars, sorted_employment)):
        width = bar.get_width()
        percentage = (value / total_employment) * 100
        ax.text(width + 200, bar.get_y() + bar.get_height()/2,
                f'{int(value):,} ({percentage:.1f}%)',
                ha='left', va='center', fontweight='bold', fontsize=11)

    ax.set_xlabel('Number of Criminals', fontweight='bold')
    ax.set_title('Employment Status of Criminals - 2024', fontsize=16, fontweight='bold', pad=20)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig('charts/05_employment_status.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/05_employment_status.png")


# ==================== CHART 6: Criminal Code Categories ====================
def generate_chart_06():
    """Generate Criminal Code categories chart"""
    print("6. Generating Criminal Code categories chart...")

    df3 = pd.read_excel('data/003_3.xls', sheet_name='3.3')

    categories = [
        'Against Personality',
        'Economic Crimes',
        'Public Safety & Order',
        'Against State Power',
        'Other Crimes'
    ]
    categories_data = [
        df3.iloc[5, -1],   # Against personality
        df3.iloc[12, -1],  # Economic
        df3.iloc[16, -1],  # Public safety
        df3.iloc[24, -1],  # State power
        df3.iloc[30, -1],  # Other
    ]

    fig, ax = plt.subplots(figsize=(14, 9))
    colors_cat = ['#E63946', '#F77F00', '#06A77D', '#4361EE', '#9D4EDD']
    bars = ax.bar(categories, categories_data, color=colors_cat, edgecolor='black', linewidth=1.5, width=0.6)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        percentage = (height / sum(categories_data)) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.set_ylabel('Number of Criminals', fontweight='bold')
    ax.set_title('Criminals by Criminal Code Chapters - 2024', fontsize=16, fontweight='bold', pad=20)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=15, ha='right')

    plt.tight_layout()
    plt.savefig('charts/06_criminal_code_categories.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/06_criminal_code_categories.png")


# ==================== CHART 7: Crime Subcategories ====================
def generate_chart_07():
    """Generate detailed crime subcategories chart"""
    print("7. Generating detailed crime subcategories chart...")

    df3 = pd.read_excel('data/003_3.xls', sheet_name='3.3')

    subcategories = {
        'Against Personality': [
            ('Life & Health', df3.iloc[7, -1]),
            ('Freedom & Dignity', df3.iloc[8, -1]),
            ('Sexual Crimes', df3.iloc[9, -1]),
            ('Constitutional Rights', df3.iloc[10, -1]),
            ('Minors & Family', df3.iloc[11, -1])
        ],
        'Public Safety': [
            ('Public Safety', df3.iloc[18, -1]),
            ('Drug Crimes', df3.iloc[19, -1]),
            ('Public Morality', df3.iloc[20, -1]),
            ('Ecological', df3.iloc[21, -1]),
            ('Traffic Safety', df3.iloc[22, -1]),
            ('Cybercrimes', df3.iloc[23, -1])
        ]
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 10))

    # Against Personality - Bar Chart
    labels1 = [item[0] for item in subcategories['Against Personality']]
    values1 = [item[1] for item in subcategories['Against Personality']]
    colors1 = plt.cm.Reds(np.linspace(0.4, 0.9, len(labels1)))
    total1 = sum(values1)

    # Sort by value
    sorted_idx1 = np.argsort(values1)[::-1]
    labels1_sorted = [labels1[i] for i in sorted_idx1]
    values1_sorted = [values1[i] for i in sorted_idx1]
    colors1_sorted = [colors1[i] for i in sorted_idx1]

    bars1 = ax1.barh(labels1_sorted, values1_sorted, color=colors1_sorted, edgecolor='black', linewidth=1.2)

    # Add value labels
    for bar, value in zip(bars1, values1_sorted):
        width = bar.get_width()
        percentage = (value / total1) * 100
        ax1.text(width + 50, bar.get_y() + bar.get_height()/2,
                f'{int(value):,} ({percentage:.1f}%)',
                ha='left', va='center', fontweight='bold', fontsize=11)

    ax1.set_xlabel('Number of Criminals', fontweight='bold')
    ax1.set_title('Crimes Against Personality - Subcategories (2024)', fontsize=15, fontweight='bold', pad=20)
    ax1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax1.grid(axis='x', alpha=0.3)

    # Public Safety - Bar Chart
    labels2 = [item[0] for item in subcategories['Public Safety']]
    values2 = [item[1] for item in subcategories['Public Safety']]
    colors2 = plt.cm.Greens(np.linspace(0.4, 0.9, len(labels2)))
    total2 = sum(values2)

    # Sort by value
    sorted_idx2 = np.argsort(values2)[::-1]
    labels2_sorted = [labels2[i] for i in sorted_idx2]
    values2_sorted = [values2[i] for i in sorted_idx2]
    colors2_sorted = [colors2[i] for i in sorted_idx2]

    bars2 = ax2.barh(labels2_sorted, values2_sorted, color=colors2_sorted, edgecolor='black', linewidth=1.2)

    # Add value labels
    for bar, value in zip(bars2, values2_sorted):
        width = bar.get_width()
        percentage = (value / total2) * 100
        ax2.text(width + 80, bar.get_y() + bar.get_height()/2,
                f'{int(value):,} ({percentage:.1f}%)',
                ha='left', va='center', fontweight='bold', fontsize=11)

    ax2.set_xlabel('Number of Criminals', fontweight='bold')
    ax2.set_title('Public Safety & Order - Subcategories (2024)', fontsize=15, fontweight='bold', pad=20)
    ax2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax2.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig('charts/07_crime_subcategories.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/07_crime_subcategories.png")


# ==================== CHART 8: Crimes vs Criminals ====================
def generate_chart_08():
    """Generate crimes vs criminals comparison chart"""
    print("8. Generating crimes vs criminals comparison chart...")

    df1 = pd.read_excel('data/003_1.xls', sheet_name='3.1')
    df10 = pd.read_excel('data/003_10.xls', sheet_name='3.10')

    years_comparison = df1.iloc[2, -11:].values.astype(int)  # Last 11 years
    total_crimes = df1.iloc[3, -11:].values.astype(float)
    total_criminals = df10.iloc[3, -11:].values.astype(float)

    fig, ax1 = plt.subplots(figsize=(16, 9))

    color1 = '#E63946'
    ax1.set_xlabel('Year', fontweight='bold', fontsize=13)
    ax1.set_ylabel('Number of Crimes', color=color1, fontweight='bold', fontsize=13)
    line1 = ax1.plot(years_comparison, total_crimes, marker='o', linewidth=3, markersize=8,
                     label='Total Crimes', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    color2 = '#4361EE'
    ax2.set_ylabel('Number of Criminals', color=color2, fontweight='bold', fontsize=13)
    line2 = ax2.plot(years_comparison, total_criminals, marker='s', linewidth=3, markersize=8,
                     label='Total Criminals', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))

    # Add annotations
    ax1.annotate(f'{int(total_crimes[-1]):,}',
                xy=(years_comparison[-1], total_crimes[-1]),
                xytext=(10, 10), textcoords='offset points',
                ha='left', fontsize=11, fontweight='bold',
                color=color1,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

    ax2.annotate(f'{int(total_criminals[-1]):,}',
                xy=(years_comparison[-1], total_criminals[-1]),
                xytext=(10, -20), textcoords='offset points',
                ha='left', fontsize=11, fontweight='bold',
                color=color2,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

    crimes_per_criminal = total_crimes[-1] / total_criminals[-1]
    ax1.set_title(f'Total Crimes vs Total Criminals (2014-2024)\n2024: {crimes_per_criminal:.2f} Crimes per Criminal',
                 fontsize=16, fontweight='bold', pad=20)

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=12, framealpha=0.9)

    plt.tight_layout()
    plt.savefig('charts/08_crimes_vs_criminals.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/08_crimes_vs_criminals.png")


# ==================== CHART 9: Year-over-Year Change ====================
def generate_chart_09():
    """Generate year-over-year change chart (2023 -> 2024)"""
    print("9. Generating year-over-year change chart...")

    df1 = pd.read_excel('data/003_1.xls', sheet_name='3.1')

    crime_types_yoy = [
        'Total Crimes',
        'Murder & Attempt',
        'Serious Harm',
        'Rape & Attempt',
        'Theft',
        'Fraud',
        'Robbery',
        'Banditry',
        'Hooliganism',
        'Drug Crimes',
        'Traffic Violations'
    ]

    values_2023 = [
        df1.iloc[3, -2],   # Total
        df1.iloc[5, -2],   # Murder
        df1.iloc[7, -2],   # Harm
        df1.iloc[8, -2],   # Rape
        df1.iloc[9, -2],   # Theft
        df1.iloc[10, -2],  # Fraud
        df1.iloc[11, -2],  # Robbery
        df1.iloc[12, -2],  # Banditry
        df1.iloc[13, -2],  # Hooliganism
        df1.iloc[14, -2],  # Drugs
        df1.iloc[15, -2],  # Traffic
    ]

    values_2024 = [
        df1.iloc[3, -1],   # Total
        df1.iloc[5, -1],   # Murder
        df1.iloc[7, -1],   # Harm
        df1.iloc[8, -1],   # Rape
        df1.iloc[9, -1],   # Theft
        df1.iloc[10, -1],  # Fraud
        df1.iloc[11, -1],  # Robbery
        df1.iloc[12, -1],  # Banditry
        df1.iloc[13, -1],  # Hooliganism
        df1.iloc[14, -1],  # Drugs
        df1.iloc[15, -1],  # Traffic
    ]

    # Calculate percentage change
    pct_change = [(v24 - v23) / v23 * 100 for v23, v24 in zip(values_2023, values_2024)]

    fig, ax = plt.subplots(figsize=(14, 10))
    colors = ['#06A77D' if pc < 0 else '#E63946' for pc in pct_change]
    bars = ax.barh(crime_types_yoy, pct_change, color=colors, edgecolor='black', linewidth=0.8)

    # Add value labels
    for i, (bar, pct) in enumerate(zip(bars, pct_change)):
        width = bar.get_width()
        label_x_pos = width + 0.5 if width > 0 else width - 0.5
        ha_align = 'left' if width > 0 else 'right'
        ax.text(label_x_pos, bar.get_y() + bar.get_height()/2,
                f'{pct:+.1f}%',
                ha=ha_align, va='center', fontweight='bold', fontsize=11)

    ax.axvline(x=0, color='black', linewidth=1.5)
    ax.set_xlabel('Percentage Change (%)', fontweight='bold')
    ax.set_title('Year-over-Year Change in Crime Statistics (2023 → 2024)', fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#06A77D', edgecolor='black', label='Decrease'),
        Patch(facecolor='#E63946', edgecolor='black', label='Increase')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=11)

    plt.tight_layout()
    plt.savefig('charts/09_year_over_year_change.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/09_year_over_year_change.png")


# ==================== CHART 10: Drug Crimes Evolution ====================
def generate_chart_10():
    """Generate drug crimes evolution chart (1993-2024)"""
    print("10. Generating drug crimes evolution chart...")

    df1 = pd.read_excel('data/003_1.xls', sheet_name='3.1')
    years_all = df1.iloc[2, 2:].values.astype(int)
    drug_crimes = df1.iloc[14, 2:].values.astype(float)

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(years_all, drug_crimes, marker='o', linewidth=3, markersize=7, color='#06A77D', label='Drug Crimes')
    ax.fill_between(years_all, drug_crimes, alpha=0.3, color='#06A77D')

    # Highlight key years
    key_indices = [0, 10, 20, 30, 31]  # 1993, 2003, 2013, 2023, 2024
    for idx in key_indices:
        if idx < len(years_all):
            ax.annotate(f'{int(drug_crimes[idx]):,}',
                       xy=(years_all[idx], drug_crimes[idx]),
                       xytext=(0, 15), textcoords='offset points',
                       ha='center', fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', color='black', lw=1))

    # Calculate growth rate
    growth_rate = ((drug_crimes[-1] - drug_crimes[0]) / drug_crimes[0]) * 100

    ax.set_xlabel('Year', fontweight='bold')
    ax.set_ylabel('Number of Drug Crimes', fontweight='bold')
    ax.set_title(f'Drug Crimes Evolution in Azerbaijan (1993-2024)\nOverall Growth: {growth_rate:+.1f}%',
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.legend(loc='upper left', fontsize=12)

    plt.tight_layout()
    plt.savefig('charts/10_drug_crimes_evolution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ Saved: charts/10_drug_crimes_evolution.png")


# ==================== MAIN EXECUTION ====================
def main():
    """Main function to generate all charts"""
    try:
        generate_chart_01()
        generate_chart_02()
        generate_chart_03()
        generate_chart_04()
        generate_chart_05()
        generate_chart_06()
        generate_chart_07()
        generate_chart_08()
        generate_chart_09()
        generate_chart_10()

        print()
        print("="*80)
        print("ALL CHARTS GENERATED SUCCESSFULLY!")
        print("="*80)
        print()
        print("Total charts created: 10")
        print()
        print("Chart list:")
        for i in range(1, 11):
            print(f"  {i:2d}. charts/{i:02d}_*.png")
        print()
        print("="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
