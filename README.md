# Google Fonts Regression Tester

Compare local font families against the last release, hosted on fonts.google.com.

## Installation
-Clone repository
-Create a new virtualenv
-Pip install -r requirements.txt
-python test_fonts.py
-visit http://127.0.0.1:5000/ in a browser

## Testing fonts setup
-Drop desired fonts into static folder
-Refresh web browser

Note: Adding a font which does not exist in fonts.google.com will return Fira Mono as a fallback.

## Todo:
- Add OT feature test
