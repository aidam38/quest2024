from flask import Flask, request, render_template, send_from_directory, session
from functools import wraps
import sqlite3
import re
import random

# Read config file
_KEY_VALUE_STRING_REGEX = re.compile(r"(?P<key>(\w|_)*)\s*=\s*\"(?P<value>.*)\"")
_KEY_VALUE_NUMBER_REGEX = re.compile(r"(?P<key>(\w|_)*)\s*=\s*(?P<value>.*)")
config = {}
with open("./quest.cfg", "r") as cfgfile:
    for line in cfgfile.readlines():
        for regex in [_KEY_VALUE_STRING_REGEX, _KEY_VALUE_NUMBER_REGEX]:
            match = regex.match(line)
            if match is not None and match.group("key") not in config:
                config[match.group("key")] = match.group("value").strip()

# Connect to database
db = sqlite3.connect("./db/quest.db", check_same_thread=False)
cur = db.cursor()


# Create Flask app
app = Flask("quest")
app.secret_key = "69"


################################################################################
# Helper functions
################################################################################
def get_mole_id(username):
    """Gets mole id from database"""
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    (mole_id,) = cur.fetchone()
    return mole_id


def get_locations(mole_id):
    """Returns a list of all locations in the database with a boolean indicating whether the mole has found them."""
    cur.execute(
        """
        SELECT locations.level, locations.id, locations.name, locations.clue, finds.mole_id, unlocked.mole_id
        FROM locations
        LEFT JOIN finds
        ON locations.id = finds.location_id AND finds.mole_id = ?
        LEFT JOIN unlocked
        ON locations.id = unlocked.location_id AND unlocked.mole_id = ?
        """,
        (mole_id, mole_id),
    )
    locations = {}
    for level, id, name, clue, finds_mole_id, unlocked_mole_id in cur.fetchall():
        if level not in locations:
            locations[level] = []
        locations[level].append(
            {
                "id": id,
                "name": name,
                "clue": clue,
                "found": finds_mole_id is not None,
                "unlocked": unlocked_mole_id is not None or level == 1,
            }
        )
    return locations


################################################################################
# Security wrappers
################################################################################
@app.before_request
def make_session_permanent():
    session.permanent = True

def passphrase(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        if "passphrase" not in session or session["passphrase"] != config["passphrase"]:
            return render_template("passphrase.html", base_url=config["base_url"])
        return route(*args, **kwargs)

    return wrapper


def authenticate(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        # Check if user signed in
        if "username" not in session or "password" not in session:
            return render_template("user.html", base_url=config["base_url"])

        username = session["username"]

        # Check if user exists in database
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        if cur.fetchone() is None:
            return render_template("user.html", base_url=config["base_url"])

        # If user exists, check if password is correct
        password = session["password"]
        cur.execute("SELECT password FROM users WHERE username=?", (username,))
        (correct_password,) = cur.fetchone()
        if password != correct_password:
            return render_template("user.html", base_url=config["base_url"])

        # If password is correct, return route
        return route(*args, **kwargs)

    return wrapper


################################################################################
# Define routes
################################################################################
@app.route("/")
@passphrase
@authenticate
def index():
    # Render all locations
    username = session["username"]
    locations = get_locations(get_mole_id(username))
    return render_template(
        "locations.html", base_url=config["base_url"], username=username, locations=locations
    )


@app.route("/check-passphrase", methods=["POST"])
def check_passphrase():
    # Check passphrase
    if request.form["passphrase"] != config["passphrase"]:
        return render_template(
            "passphrase.html", base_url=config["base_url"], incorrect=True
        )

    # Set passphrase cookie
    session["passphrase"] = config["passphrase"]
    return render_template("user.html", base_url=config["base_url"])


@app.route("/log-in", methods=["POST"])
@passphrase
def log_in():
    # Get username and password from form
    username = request.form["username"]
    password = request.form["password"]

    # Check username and password are not empty
    if username == "" or password == "":
        return render_template(
            "user.html", base_url=config["base_url"], empty=True
        )
        

    # Check user doesn't exist in database
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    result = cur.fetchone()
    if result is None:
        # Add user to database
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, password)
        )
        db.commit()
    else:
        (correct_password,) = result
        # Check if password is correct
        if password != correct_password:
            return render_template(
                "user.html", base_url=config["base_url"], incorrect=True
            )

    session["username"] = username
    session["password"] = password
    return index()


@app.route("/submit-code", methods=["POST"])
@passphrase
@authenticate
def submit_code():
    # Get location info from database
    location_id = request.form["id"]
    cur.execute(
        "SELECT level, name, clue, code FROM locations WHERE id = ?", (location_id,)
    )
    (level, name, clue, code) = cur.fetchone()

    # If submitted code is incorrect
    if request.form["code"] != code:
        # Render the same card with "incorrect" message
        return render_template(
            "location_card.html",
            base_url=config["base_url"],
            location={"id": location_id, "clue": clue},
            incorrect=True,
        )

    # If submitted code is correct
    # Store find in database
    username = session["username"]
    mole_id = get_mole_id(username)
    cur.execute(
        "INSERT INTO finds (location_id, mole_id) VALUES (?, ?)", (location_id, mole_id)
    )

    # Get number of locations found in this level
    locations = get_locations(mole_id)
    num_found = len([l for l in locations[level] if l["found"]])

    # If we've found enough, unlock location in next level (if there's one)
    to_unlock = None
    if (
        num_found % int(config["num_found_for_unlock"]) == 0
    ) and level + 1 in locations:
        # Choose which location to unlock
        locked_locations = [
            l for l in locations[level + 1] if not l["found"] and not l["unlocked"]
        ]
        to_unlock = locked_locations[0]

        # Store unlock in database
        cur.execute(
            "INSERT INTO unlocked (location_id, mole_id) VALUES (?, ?)",
            (to_unlock["id"], mole_id),
        )

    # Commit database before returning
    db.commit()

    # Return found and optinally unlocked card
    found_card = render_template(
        "location_card_found.html",
        base_url=config["base_url"],
        location={"id": location_id, "name": name, "clue": clue},
    )
    unlocked_card = render_template(
            "location_card.html", base_url=config["base_url"], location=to_unlock, oob=True
        ) if to_unlock else ""
    updated_count = "<span id='level-" + str(level) + "-count' hx-swap-oob='true'>" + str(num_found) + "</span>"
    return found_card + unlocked_card + updated_count

@app.route("/leaderboard")
@passphrase
@authenticate
def leaderboard():
    # Get leaderboard from database
    cur.execute(
        """
        SELECT username, COUNT(finds.location_id) AS num_finds
        FROM users
        LEFT JOIN finds
        ON users.id = finds.mole_id
        GROUP BY username
        ORDER BY num_finds DESC
        """
    )
    leaderboard = cur.fetchall()
    print(leaderboard)
    return render_template(
        "leaderboard.html", base_url=config["base_url"], leaderboard=leaderboard
    )


# Serve static files from /assets
@app.route("/assets/<path:path>")
def send_assets(path):
    return send_from_directory("assets", path)


# Start server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config["port"])
