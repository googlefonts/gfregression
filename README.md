# Google Fonts Regression Tester

Compare local font families against the lastest release hosted on fonts.google.com.

Visit [GF Regression](http://45.55.138.144)

# ![Font Bakery](screenshot.png)

**Warning: Error handling and better tests are needed. This webapp should not be treated as a God. It should be used in conjunction with good judgement.**

*"Measure twice, cut once" - English Proverb*

*"Measure seven times, cut once" - Russian Proverb*

## Installation

To run GF Regression locally, you'll need a [Google Fonts api key](https://developers.google.com/fonts/). This must be stored in a .json file located at /app/secrets.json. It must have the following structure.

```
{
    "GF_API_KEY": "YOUR-GF-API-KEY"
}

```