# Patient Readmission Risk Analysis — synthetic SQL demo

This project recreates the analytical workflow described on my resume: validate discharge records, explore readmissions with SQL, compare departments, segment encounters, and prepare dashboard-ready outputs. It deliberately uses generated, non-identifiable data. It does **not** include hospital records, a Power BI `.pbix` file, or a clinically validated prediction model.

## Run it

Python 3.9+; no third-party packages required.

```bash
python3 generate_data.py --rows 10000
python3 analyze.py
python3 -m unittest -v
```

Open `outputs/dashboard.html` in a browser. The script also writes `department_summary.csv`, `risk_segments.csv`, and `monthly_trends.csv` for Power BI or another BI tool. To exercise the larger scale referenced in the resume, run `python3 generate_data.py --rows 70000` before analysis; this still produces synthetic records.

## Interpretation

The source data is generated from a seeded probability model. The High/Medium/Low segments are transparent descriptive rules based on visit frequency and length of stay—not clinical risk scores. Readmission rates and department differences in the demo are artifacts of the generator. Real use would require governance, patient privacy protections, cohort and label definitions, temporal validation, and clinical review.
