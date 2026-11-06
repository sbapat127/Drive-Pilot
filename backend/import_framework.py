set FLASK_APP=app.py

import click
from flask import Flask

app = Flask(__name__)


@app.cli.command("init-db")
def init_db_command():
  """Clear the existing data and create new tables."""
  # Put your database initialization logic here
  print("Initialized the database.")


if __name__ == "__main__":
  app.run()