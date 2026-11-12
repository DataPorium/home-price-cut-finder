# Home price cut finder: homes with the biggest price drops by ZIP code, city or county

Find US homes for sale whose sellers have cut the price, sorted by the biggest cut, and save them to CSV. Search one or more ZIP codes, a city, a county or a whole state, and keep only fresh cuts, large cuts, a price range or a home style. Useful for buyers looking for motivated sellers and for investors watching a market soften.

```bash
python price_cuts.py --city Austin --state TX --within-days 7 --price-max 600000
```

## Quick start

```bash
git clone https://github.com/DataPorium/home-price-cut-finder.git
cd home-price-cut-finder
pip install -r requirements.txt
export DATAPORIUM_API_KEY="YOUR_API_KEY"
python price_cuts.py --zip 92602,92618
```

It writes `price_cuts.csv` with one row per home (address, price, beds, baths, square feet, price per square foot, the latest and the total price cut, the real listed date, days on market, whether it was relisted, and every other field the API returns), prints the ten biggest cuts and gives a link to see the homes on a map at dataporium.tech.

## Options

| Option | Meaning |
|---|---|
| `--zip 92602,92618` | One or more ZIP codes (up to 25) |
| `--city Austin --state TX` | A city; add the state |
| `--county Maricopa --state AZ` | A county; add the state |
| `--state FL` | A whole state |
| `--within-days 7` | Only homes whose latest cut was in the last 7 days |
| `--cut-min 25000` / `--cut-pct-min 5` | Total cut since the home was first listed, in dollars or percent |
| `--price-min` / `--price-max` / `--beds-min` | Price range and bedrooms |
| `--style single_family` | `single_family`, `condos`, `townhomes`, `multi_family`, ... |
| `--sort biggest_cut` | `biggest_cut` (default), `recent_cut`, `best_value`, `price_asc` or `dom_desc` |
| `--max 500` | Most homes to save (default 500) |

Days on market use the real listed date, so a home that was taken off the market and relisted does not look new. The total cut counts every cut since the home was first listed in the current selling effort.

## How it works

One endpoint of the DataPorium API, through the [Python library](https://github.com/DataPorium/dataporium-python):

```python
from dataporium import DataPorium

dp = DataPorium()
answer = dp.properties(city="Austin", state="TX", price_cut=True, price_cut_within_days=7,
                       sort="biggest_cut", limit=100)
```

The answer has the homes, a summary of all matches and `next_offset` when there are more; the script follows it page by page. The same endpoint also finds pending, rented, sold and off-market homes (`status`).

## Get an API key

The script uses the [DataPorium](https://dataporium.tech) financial data API with your own API key. Sign up at [dataporium.tech](https://dataporium.tech/pricing) and subscribe to the Premium plan; the key is in your account settings. Then set it once in your terminal:

```bash
export DATAPORIUM_API_KEY="YOUR_API_KEY"     # macOS and Linux
setx DATAPORIUM_API_KEY "YOUR_API_KEY"       # Windows (open a new terminal afterwards)
```

Keep the key out of code you commit or share.

## More

- Python library used here: [dataporium-python](https://github.com/DataPorium/dataporium-python)
- JavaScript and TypeScript: [dataporium-js](https://github.com/DataPorium/dataporium-js)
- Examples in curl, R, Google Sheets and Excel: [financial-data-api](https://github.com/DataPorium/financial-data-api)
- Use the same data in Claude, ChatGPT or Cursor: [dataporium-mcp](https://github.com/DataPorium/dataporium-mcp)
- API documentation: <https://dataporium.tech/api-docs>

## License

MIT. Use of the API and its data is governed by the DataPorium [Terms of Use](https://dataporium.tech/terms-of-use). Data is for information only and is not investment advice.
