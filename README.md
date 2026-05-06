# StableFlow Multi-Ingredient Feed MVP

This updated version supports proper multi-ingredient feeds.

## New feed structure

- Feed Ingredients
- Feed Meals
- Feed Meal Items
- Feed Logs

This allows:
- multiple ingredients per meal
- AM / Midday / PM / Night meals
- quantities and units
- supplement and medication flags
- prep notes
- daily feed sheet view

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then click **Load sample data**.
