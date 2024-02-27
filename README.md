# GDBG Quest 2024 Website 

Changes:

* Darb-friendly (separate auth from Titanic)
* levels

## Setup

To completely set up the Quest website on Titanic (steps to start a development server are similar), you need to:

0. Set up a Python virtual environment (recommended)
1. Set up the database
2. Specify base url and port in `config.cfg`
3. Set up authentication/authorization on Titanic
4. Start the server

### Python venv

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Database

0. Install `sqlite3` on the host machine. 

1. Create a csv file of your locations in `db/locations.csv` with fields `name,clue,code`. Example:

```
name,clue,code
Siberia,Vatikremlin,1234
Pub,Senior alley,1234
Cannes,Fake shawn,1234
```
*Tip: You can use Google Spreadsheet to collaborate on the locations and then just export to csv.*

2. `cd` into `db/` and run `python setup.py`

### `quest.cfg`

Config file follows simple `key = "value"` format (always with quotes). Required fields:

* `base_url`: route at which the app is deployed, e.g. `https://blacker.caltech.edu/quest/2024`
* `port`: port the app should listen at

*Tip: If you're developing both locally (where your `base_url` probably just needs to be `""` or `"localhost"`) and on Titanic, simply have different `quest.cfg` files. They are also ignored by git.*

### Titanic auth

The Quest server expects moles to be logged in on the Blacker website, all requests to be authorized by the web server, and the username to be present in the `X-Username` request header.

As of 2024, the server we use is Apache and the full configuration snippet is:

```
TODO
```

### Start the server

Simply run

```
python quest.py
```
*Note: Flask will show a warning that the development server shouldn't be used in a production deployment. But for this amount of traffic, it's totally fine.*

It might be a good idea to set up a systemd service on the host machine or use some sort of container.

## Maintenance

If something goes wrong and you need to edit the database, simply run `sqlite3 db/quest.db` and edit it directly with SQL commands.