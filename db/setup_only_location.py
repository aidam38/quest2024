import sqlite3
import csv

# Create the database file
db = sqlite3.connect('./quest.db')
cur = db.cursor()

# Clear location table
cur.execute('DELETE FROM locations')

# Create location records from locations.csv
with open('./locations.csv', 'r') as f:
	reader = csv.reader(f, delimiter="\t")
	next(reader)
	for row in reader:
		cur.execute('INSERT INTO locations (level, name, clue, code) VALUES (?,?,?,?)', row)

# Commit changes and close the database
db.commit()
db.close()

# Print success message
print("Locations were set up successfully!")