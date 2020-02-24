import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify, render_template

import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite",
                       connect_args={'check_same_thread': False}, echo=True)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Session
#################################################
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Calc Temps
#################################################

# This function called `calc_temps` will accept start date and end date in the format '%Y-%m-%d'
# and return the minimum, average, and maximum temperatures for that range of dates


def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.

    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d

    Returns:
        TMIN, TAVE, and TMAX
    """

    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/api/v1.0/precipitation")
def precipitation():

    print("Precipitation API request received.")

    # Design a query to retrieve the last 12 months of precipitation data and plot the results
    last_date = session.query(Measurement.date).order_by(
        Measurement.date.desc()).first()
    last_date = last_date[0]

    # Calculate the date 1 year ago from the last data point in the database
    year_ago = dt.datetime.strptime(
        last_date, "%Y-%m-%d") - dt.timedelta(days=366)

    # Perform a query to retrieve the data and precipitation scores
    retrieve_scores = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= year_ago).all()

    # Convert the query results to a Dictionary using `date` as the key and `prcp` as the value.
    results_dict = {}
    for result in retrieve_scores:
        results_dict[result[0]] = result[1]

    return jsonify(results_dict)


@app.route("/api/v1.0/stations")
def stations():

    print("Stations API request received.")

    # query stations list
    stations_data = session.query(Station).all()

    # create a list of dictionaries
    stations_list = []
    for station in stations_data:
        station_dict = {}
        station_dict["id"] = station.id
        station_dict["station"] = station.station
        station_dict["name"] = station.name
        station_dict["latitude"] = station.latitude
        station_dict["longitude"] = station.longitude
        station_dict["elevation"] = station.elevation
        stations_list.append(station_dict)

    return jsonify(stations_list)


@app.route("/api/v1.0/tobs")
def tobs():

    print("Tobs API request received.")

    # We find temperature data for the last year. First we find the last date in the database
    final_date_query = session.query(
        func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    last_date_string = final_date_query[0][0]
    last_date = dt.datetime.strptime(last_date_string, "%Y-%m-%d")

    # Set beginning
    begin_date = last_date - dt.timedelta(366)

    # get temperature measurements for last year
    results = session.query(Measurement).filter(
        func.strftime("%Y-%m-%d", Measurement.date) >= begin_date).all()

    # create list of dictionaries (one for each observation)
    tobs_list = []
    for result in results:
        tobs_dict = {}
        tobs_dict["date"] = result.date
        tobs_dict["station"] = result.station
        tobs_dict["tobs"] = result.tobs
        tobs_list.append(tobs_dict)

    return jsonify(tobs_list)

# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.


@app.route("/api/v1.0/<start>")
def temp_stats_start(start):

    print("<Start> API request received.")

    """Return a JSON list of the minimum, average, and maximum temperatures from the start date until
    the end of the database."""

    # Retrieve First and Last dates
    final_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    max_date = final_date_query[0][0]

    # Retrieve temps
    temps = calc_temps(start, max_date)

    # Create list
    start_data_list = []
    date_dict = {'start_date': start, 'end_date': max_date}
    start_data_list.append(date_dict)
    start_data_list.append({'tobs': 'TMIN', 'Temperature': temps[0][0]})
    start_data_list.append({'tobs': 'TAVG', 'Temperature': temps[0][1]})
    start_data_list.append({'tobs': 'TMAX', 'Temperature': temps[0][2]})

    return jsonify(start_data_list)


@app.route("/api/v1.0/<start>/<end>")
def start_end(start=None, end=None):

    print("<Start>/<End> API request received.")

    # Retrieve temps
    temps = calc_temps(start, end)

    # Create list
    between_dates_data = []
    date_dict = {'start_date': start, 'end_date': end}
    between_dates_data.append(date_dict)
    between_dates_data.append({'tobs': 'TMIN', 'Temperature': temps[0][0]})
    between_dates_data.append({'tobs': 'TAVG', 'Temperature': temps[0][1]})
    between_dates_data.append({'tobs': 'TMAX', 'Temperature': temps[0][2]})
    
    return jsonify(between_dates_data)


if __name__ == '__main__':
    app.run(debug=True)
