# Google Fonts Regression Tester

Compare local font families against the last release, hosted on fonts.google.com.

# ![Font Bakery](screenshot.png)

## Installation
- Clone repository
    `$ git clone https://github.com/m4rc1e/gfregression.git`
- Create a new virtualenv
    `$ virtualenv env`
- Activate virtualenv
    `$ source env/bin/activate`
- Install dependencies 
    `$ pip install -r requirements.txt`
- Run the test server
    `$ python main.py`
- visit http://127.0.0.1:5000/ in a browser

## Testing fonts setup
- Drop desired fonts into static folder
- Refresh web browser

Note: Adding a font which does not exist in fonts.google.com will return Inconsolata as a fallback.

## Todo:
- Add OT feature test
