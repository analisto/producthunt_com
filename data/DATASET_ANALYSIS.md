# Crime Statistics Dataset Analysis - Azerbaijan
## Complete Analysis of In-Row Aggregation Patterns

---

## Overview
This repository contains **5 Excel datasets** with crime statistics from Azerbaijan, covering various time periods from 1993 to 2024. All datasets contain **critical in-row aggregation patterns** that must be carefully understood to avoid double-counting and misinterpretation.

---

## Dataset Summary

### 1. **003_1.xls** - Registered Crimes by Main Crime Types (1993-2024)
- **Sheet Name:** 3.1
- **Dimensions:** 18 rows × 34 columns (years from 1993-2024)
- **Primary Language:** Azerbaijani

#### Data Structure:
```
Row 0:  Title header
Row 2:  Year labels (1993, 1994, ..., 2023, 2024)
Row 3:  TOTAL CRIMES REGISTERED ⚠️ GRAND TOTAL
Row 4:  "onlardan:" (of which:) ← AGGREGATION INDICATOR
Row 5:  Murder and attempted murder (SUBTOTAL)
Row 6:    ↳ "onlardan qəsdən adam öldürmə" (of which: intentional murder) ⚠️ SUBSET OF ROW 5
Row 7:  Intentional serious harm to health
Row 8:  Rape and attempted rape
Row 9:  Theft
Row 10: Fraud
Row 11: Robbery
Row 12: Banditry
Row 13: Hooliganism
Row 14: Illegal drug trafficking
Row 15: Traffic violations (SUBTOTAL)
Row 16:   ↳ "onlardan" (of which: resulting in death) ⚠️ SUBSET OF ROW 15
Row 17: Footnote
```

#### IN-ROW AGGREGATION PATTERN:
- **Row 3 = TOTAL** (36,811 crimes in 2023, 33,379 in 2024)
- **Rows 5, 7-15 are main categories** that approximately sum to row 3
- **Row 6 is a SUBSET of row 5** - DO NOT count separately
- **Row 16 is a SUBSET of row 15** - DO NOT count separately

#### Key Statistics (2024):
- Total crimes: 33,379
- Murder & attempted murder: 218 (of which actual murder: 161)
- Theft: 4,219
- Fraud: 6,972
- Drug crimes: 8,551
- Traffic violations: 2,685 (of which resulting in death: 621)

---

### 2. **003_3.xls** - Criminals by Criminal Code Chapters (2005-2024)
- **Sheet Name:** 3.3
- **Dimensions:** 31 rows × 22 columns (years from 2005-2024)
- **Primary Language:** Azerbaijani

#### Data Structure:
```
Row 3:  TOTAL CRIMINALS ⚠️ GRAND TOTAL
Row 4:  "o cümlədən:" (including:) ← AGGREGATION INDICATOR

SECTION 1: Crimes Against Personality
Row 5:  Crimes against personality (SECTION TOTAL)
Row 6:    "o cümlədən:" (including:) ← NESTED AGGREGATION
Row 7:      ↳ Life and health crimes ⚠️ SUBSET
Row 8:      ↳ Freedom and dignity crimes ⚠️ SUBSET
Row 9:      ↳ Sexual crimes ⚠️ SUBSET
Row 10:     ↳ Constitutional rights crimes ⚠️ SUBSET
Row 11:     ↳ Minors and family crimes ⚠️ SUBSET

SECTION 2: Economic Crimes
Row 12: Economic crimes (SECTION TOTAL)
Row 13:   "o cümlədən:" (including:) ← NESTED AGGREGATION
Row 14:     ↳ Property crimes ⚠️ SUBSET
Row 15:     ↳ Economic activity crimes ⚠️ SUBSET

SECTION 3: Public Safety and Order
Row 16: Public safety and order crimes (SECTION TOTAL)
Row 17:   "o cümlədən:" (including:) ← NESTED AGGREGATION
Row 18:     ↳ Public safety crimes ⚠️ SUBSET
Row 19:     ↳ Drug crimes ⚠️ SUBSET
Row 20:     ↳ Public morality crimes ⚠️ SUBSET
Row 21:     ↳ Ecological crimes ⚠️ SUBSET
Row 22:     ↳ Traffic safety crimes ⚠️ SUBSET
Row 23:     ↳ Cybercrimes ⚠️ SUBSET

SECTION 4: Crimes Against State Power
Row 24: Crimes against state power (SECTION TOTAL)
Row 25:   "o cümlədən:" (including:) ← NESTED AGGREGATION
Row 26:     ↳ Constitutional system crimes ⚠️ SUBSET
Row 27:     ↳ Justice crimes ⚠️ SUBSET
Row 28:     ↳ Corruption crimes ⚠️ SUBSET
Row 29:     ↳ Management crimes ⚠️ SUBSET

Row 30: Other crimes
```

#### IN-ROW AGGREGATION PATTERN:
**HIERARCHICAL STRUCTURE:**
```
Row 3 (TOTAL) ≈ Row 5 + Row 12 + Row 16 + Row 24 + Row 30

Where:
  Row 5 ≈ Row 7 + Row 8 + Row 9 + Row 10 + Row 11
  Row 12 ≈ Row 14 + Row 15
  Row 16 ≈ Row 18 + Row 19 + Row 20 + Row 21 + Row 22 + Row 23
  Row 24 ≈ Row 26 + Row 27 + Row 28 + Row 29
```

#### Key Statistics (2024):
- Total criminals: 22,485
  - Crimes against personality: 5,084
    - Life and health: 4,767
    - Sexual crimes: 166
  - Economic crimes: 5,621
    - Property crimes: 5,212
  - Public safety crimes: 11,028
    - Drug crimes: 7,245
    - Traffic: 2,573

---

### 3. **003_4.xls** - Crimes by Specific Types of Perpetrators (1993-2024)
- **Sheet Name:** 3.4
- **Dimensions:** 15 rows × 34 columns (years from 1993-2024)
- **Primary Language:** Azerbaijani

#### Data Structure:
```
Row 3:  "Törədilmiş cinayətlərdən:" (Of the committed crimes:) ← IMPORTANT!
Row 4:  By children aged 14-17
Row 5:  By repeat offenders
Row 6:  By a group of persons
Row 7:  By pre-organized group
Row 8:  By organized gang
Row 9:  While intoxicated
Row 10: Recidivist crimes
Row 11: Under narcotic influence
Row 12: By drug addicts
Row 13: Footnote
```

#### ⚠️ CRITICAL AGGREGATION PATTERN - OVERLAPPING CATEGORIES:
**THIS DATASET IS DIFFERENT!** Unlike others, this does NOT have a total row.

**These are OVERLAPPING, NON-EXCLUSIVE categories:**
- A single crime can appear in MULTIPLE rows
- Example: A crime by a repeat offender (Row 5) who was intoxicated (Row 9) counts in BOTH rows
- **DO NOT SUM these rows** - they are characteristics, not exclusive categories

#### Key Statistics (2024):
- Crimes by/with children aged 14-17: 279
- Crimes by repeat offenders: 6,123
- Crimes by pre-organized groups: 1,657
- Crimes while intoxicated: 168
- Crimes by drug addicts: 3,879

**Note:** These numbers can overlap - same crime may be counted in multiple categories.

---

### 4. **003_10.xls** - Criminals by Crime Types (1993-2024)
- **Sheet Name:** 3.10
- **Dimensions:** 19 rows × 34 columns (years from 1993-2024)
- **Primary Language:** Azerbaijani

#### Data Structure:
```
Row 3:  TOTAL CRIMINALS ⚠️ GRAND TOTAL
Row 4:  "onlardan cinayət növləri üzrə:" (of which by crime types:) ← AGGREGATION INDICATOR
Row 5:  Murder and attempted murder
Row 6:  Intentional serious harm to health
Row 7:  Rape and attempted rape
Row 8:  Theft
Row 9:  Fraud
Row 10: Robbery
Row 11: Banditry
Row 12: Hooliganism
Row 13: Bribery crimes
Row 14: Illegal drug trafficking
Row 15: Traffic violations (SUBTOTAL)
Row 16:   ↳ "onlardan" (of which: resulting in death) ⚠️ SUBSET OF ROW 15
Row 18: Footnote
```

#### IN-ROW AGGREGATION PATTERN:
- **Row 3 = TOTAL** (25,006 criminals in 2023, 22,485 in 2024)
- **Rows 5-15 are main crime categories** that approximately sum to row 3
- **Row 16 is a SUBSET of row 15** - DO NOT count separately

#### Key Statistics (2024):
- Total criminals: 22,485
- Murder & attempted murder: 234
- Theft: 2,097
- Fraud: 2,238
- Drug trafficking: 7,245
- Traffic violations: 2,558 (of which resulting in death: 425)

---

### 5. **003_11.xls** - Criminals by Socio-Demographic Characteristics (1993-2024)
- **Sheet Name:** 3.11
- **Dimensions:** 24 rows × 34 columns (years from 1993-2024)
- **Primary Language:** Azerbaijani

#### Data Structure:
```
Row 3:  TOTAL CRIMINALS ⚠️ GRAND TOTAL
Row 4:  "onlardan" (of which:) ← AGGREGATION INDICATOR

BREAKDOWN 1: By Gender
Row 5:  "cinsinə görə:" (by gender:) ← CATEGORY HEADER
Row 6:    Males
Row 7:    Females
        ⚠️ Row 6 + Row 7 = Row 3

BREAKDOWN 2: By Age
Row 8:  "yaşına görə:" (by age:) ← CATEGORY HEADER
Row 9:    14-15 years old
Row 10:   16-17 years old
Row 11:   18-24 years old
Row 12:   25-29 years old
Row 13:   30+ years old
        ⚠️ Rows 9-13 should sum to Row 3

BREAKDOWN 3: By Employment
Row 14: "məşğulluğuna görə:" (by employment:) ← CATEGORY HEADER
Row 15:   Workers
Row 16:   Employees
Row 17:   Agricultural workers
Row 18:   Business owners
Row 19:   Financial/bank workers
Row 20:   Government workers
Row 21:   Students
Row 22:   Unemployed (working age)
Row 23:   Other employment types
        ⚠️ Rows 15-23 should sum to Row 3
```

#### ⚠️ CRITICAL AGGREGATION PATTERN - MULTIPLE INDEPENDENT BREAKDOWNS:
**THIS IS A CROSS-CLASSIFICATION DATASET!**

The same total (Row 3) is broken down in **THREE DIFFERENT WAYS**:
1. **Gender breakdown** (rows 6-7): Mutually exclusive, sum to total
2. **Age breakdown** (rows 9-13): Mutually exclusive, sum to total
3. **Employment breakdown** (rows 15-23): Mutually exclusive, sum to total

**⚠️ DO NOT ADD ACROSS DIFFERENT BREAKDOWNS!**
- Example: Males (23,707) + 14-15 year olds (107) = WRONG! Double counting!
- The 23,707 males are DISTRIBUTED across all age groups
- The same people are counted in each breakdown, just categorized differently

#### Key Statistics (2024):
- Total criminals: 22,485
- **By Gender:**
  - Males: 21,250 (94.5%)
  - Females: 1,235 (5.5%)
- **By Age:**
  - 14-15 years: 120
  - 16-17 years: 352
  - 18-24 years: 2,344
  - 25-29 years: 3,240
  - 30+ years: 16,429 (73.1%)
- **By Employment:**
  - Workers: 1,157
  - Students: 35
  - Unemployed: 12,510 (55.6%)
  - Other: 8,100

---

## Data Validation Summary

### Aggregation Indicators in Azerbaijani:
- **"onlardan"** = "of which" (indicates subset follows)
- **"o cümlədən:"** = "including:" (indicates subcategories follow)
- **"onlardan cinayət növləri üzrə:"** = "of which by crime types:"
- **"cinsinə görə:"** = "by gender:"
- **"yaşına görə:"** = "by age:"
- **"məşğulluğuna görə:"** = "by employment:"

### Critical Rules for Analysis:

1. **Hierarchical Aggregation** (003_1.xls, 003_3.xls, 003_10.xls):
   - Total row at top
   - "onlardan" or "o cümlədən" indicates breakdown follows
   - Subcategories sum to parent category
   - **Never double-count nested rows**

2. **Overlapping Categories** (003_4.xls):
   - No total row
   - Each row is a characteristic that can co-occur
   - **Cannot sum rows** - would severely overcount
   - Use for cross-tabulation analysis only

3. **Cross-Classification** (003_11.xls):
   - One total, multiple independent breakdowns
   - Each breakdown sums to total separately
   - **Never add across different breakdowns** - represents same people

4. **Subset Indicators:**
   - Look for "onlardan" immediately before indented or related rows
   - These are ALWAYS subsets of the row above
   - Example: Row 16 in 003_1.xls (deaths from traffic) is subset of Row 15 (all traffic violations)

---

## Data Quality Notes

### Missing Data Indicators:
- **"…"** symbol indicates data not collected for that year
- **NaN** in header/separator rows is expected
- Some early years (1993-2000s) have incomplete data for certain categories

### Footnotes:
- Most datasets include footnotes explaining specific indicators
- Traffic violation data specifically notes it only covers criminal traffic incidents (not all violations)

---

## Recommended Analysis Approach

### For Time Series Analysis:
1. Use only the TOTAL rows to track overall trends
2. For subcategories, ensure you're comparing equivalent categories across years
3. Be aware of data collection changes (indicated by "…" symbols)

### For Compositional Analysis:
1. Calculate percentages using appropriate totals
2. For 003_11.xls, calculate percentages within each breakdown separately
3. Never mix categories from different aggregation levels

### For Comparative Analysis:
1. 003_1.xls vs 003_10.xls: Crimes vs Criminals (some crimes have multiple perpetrators)
2. 003_3.xls: Legal categorization by Criminal Code chapters
3. 003_4.xls: Cross-cutting characteristics (use for flag analysis, not summation)

---

## Key Insights from 2024 Data

1. **Total Crimes Registered**: 33,379 (003_1.xls)
2. **Total Criminals Identified**: 22,485 (003_10.xls, 003_11.xls)
3. **Crimes per Criminal**: ~1.48 (some criminals commit multiple crimes)

4. **Top Crime Categories**:
   - Drug crimes: 8,551 crimes / 7,245 criminals
   - Fraud: 6,972 crimes / 2,238 criminals
   - Theft: 4,219 crimes / 2,097 criminals

5. **Demographic Profile**:
   - 94.5% male, 5.5% female
   - 73.1% aged 30+
   - 55.6% unemployed

6. **Concerning Trends**:
   - High unemployment rate among criminals
   - Significant drug-related crime burden
   - Fraud increasing significantly

---

## Data Integrity Warnings

⚠️ **CRITICAL: Always check for "onlardan", "o cümlədən" indicators before summing rows**

⚠️ **CRITICAL: Verify which dataset type you're working with before analysis**

⚠️ **CRITICAL: Never assume all rows at the same indentation level can be summed**

⚠️ **CRITICAL: Footnotes contain important methodological information - read them**

---

## File Information

- **All files**: Excel .xls format (older Excel format)
- **Encoding**: UTF-8 with Azerbaijani characters
- **Decimal separator**: Period (.)
- **Empty cells**: Represent true missing data, not zeros
- **Repository**: `/Users/ismatsamadov/crime_types_analyse/data/`

---

**Analysis Date**: December 20, 2024
**Status**: ✅ Complete and Validated
