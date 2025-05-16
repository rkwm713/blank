# Conflict Resolution Strategy

- Introduce dropdown options in the UI for users to select conflict resolution preferences:
  - For existing attachment height conflicts:
    - Prefer Katapult (default)
    - Prefer SPIDA Measured
    - Highlight Differences
  - For pole attribute conflicts (e.g., Class/Height):
    - Prefer Katapult (default)
    - Prefer SPIDA
    - Highlight Differences
- On form submission, capture the selected strategies and include them in the processing configuration.
- During data extraction and consolidation:
  - Apply the chosen strategy to resolve discrepancies between Katapult and SPIDAcalc data.
  - If "Highlight Differences" is selected, mark conflicting fields for special formatting in the Excel report (e.g., yellow background) or add notes indicating the discrepancies.
- Define available strategies as enums or constants in `constants.py` to prevent string typos.
