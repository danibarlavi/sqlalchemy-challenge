# Import the dependencies.
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc
from flask import Flask, jsonify
from datetime import datetime
from dateutil.relativedelta import relativedelta

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
Base.prepare(autoload_with=engine)

# Print out the table names to verify them
print(Base.classes.keys())

# Save references to each table
Measurements = Base.classes.measurement
Stations = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List of all available api routes:"""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    try:
        # Find the most recent date in the dataset
        most_recent_entry = session.query(Measurements).order_by(desc(Measurements.date)).first()
        if most_recent_entry:
            most_recent_date = most_recent_entry.date

            # Convert 'most_recent_date' to date if it's a string
            if isinstance(most_recent_date, str):
                most_recent_date = datetime.strptime(most_recent_date, "%Y-%m-%d").date()

            # Calculate the date one year ago from the most recent date
            one_year_ago = most_recent_date - relativedelta(months=12)

            # Perform a query to retrieve the data and precipitation scores
            measurements_last_12m = session.query(Measurements.date, Measurements.prcp).filter(
                Measurements.date.between(one_year_ago, most_recent_date)
            ).all()

            # Convert the query results to a dictionary
            precipitation_dict = {
                datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d") if isinstance(date, str) else date.strftime("%Y-%m-%d"): prcp
                for date, prcp in measurements_last_12m
            }

            return jsonify(precipitation_dict)
    finally:
        session.close()

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    try:
        results = session.query(Stations.station).all()
        stations_list = [station[0] for station in results]
        return jsonify(stations_list)
    finally:
        session.close()

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    most_active_station = 'USC00519281'
    try:
        most_active_query = session.query(
            func.min(Measurements.tobs), 
            func.max(Measurements.tobs), 
            func.avg(Measurements.tobs)
        ).filter(Measurements.station == most_active_station).first()

        if most_active_query:
            lowest_temperature = most_active_query[0]
            highest_temperature = most_active_query[1]
            average_temperature = most_active_query[2]

            temperature_stats = {
                "Lowest Temperature": lowest_temperature,
                "Highest Temperature": highest_temperature,
                "Average Temperature": average_temperature
            }

            return jsonify(temperature_stats)
        else:
            return jsonify({"error": "No temperature data for given station"}), 404
    finally:
        session.close()

@app.route("/api/v1.0/<start>")
def temperature_start(start):
    session = Session(engine)
    try:
        # Convert start date from string to date
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        # Query for min, max, avg temperatures from the start date
        temps = session.query(
            func.min(Measurements.tobs),
            func.avg(Measurements.tobs),
            func.max(Measurements.tobs)
        ).filter(Measurements.date >= start_date).all()

        temps_dict = {
            "Start Date": start,
            "TMIN": temps[0][0],
            "TAVG": temps[0][1],
            "TMAX": temps[0][2]
        }
        return jsonify(temps_dict)
    finally:
        session.close()

@app.route("/api/v1.0/<start>/<end>")
def temperature_start_end(start, end):
    session = Session(engine)
    try:
        # Convert start and end dates from string to date
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()

        # Query for min, max, avg temperatures between the start and end date
        temps = session.query(
            func.min(Measurements.tobs),
            func.avg(Measurements.tobs),
            func.max(Measurements.tobs)
        ).filter(Measurements.date.between(start_date, end_date)).all()

        temps_dict = {
            "Start Date": start,
            "End Date": end,
            "TMIN": temps[0][0],
            "TAVG": temps[0][1],
            "TMAX": temps[0][2]
        }
        return jsonify(temps_dict)
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)



