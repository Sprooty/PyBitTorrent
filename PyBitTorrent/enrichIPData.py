import json
import requests
import time
import logging
from torwoldTrackerdb import get_null_country_ips  # Importing from the other file
from torwoldTrackerdb import insert_enriched_ip_data  # Importing from the other file
from torwoldTrackerdb import check_ip_enriched_status

import plotly.graph_objs as go

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def update_ips_with_country():
    logging.info("Fetching IPs that need country information.")
    ips = get_null_country_ips()  # Ensure this returns a list of IP strings or dicts
    logging.info(f"Total IPs fetched: {len(ips)}")

    # Chunk the IP list into batches of 100
    logging.info("Chunking IPs into batches of 100.")
    ip_chunks = list(chunk_list(ips, 100)) 

    # Specify the fields you want to return from the API
    fields = "country,countryCode,region,city,lat,lon,timezone,isp,as,org,query"

    # Use HTTP (as HTTPS is a paid option)
    endpoint = f'http://ip-api.com/batch?fields={fields}'
    headers = {'Content-Type': 'application/json'}  # Explicitly set the content type

    logging.info("Starting to update IPs with country information.")
    for chunk_index, chunk in enumerate(ip_chunks):
        logging.info(f"Processing chunk {chunk_index + 1}/{len(ip_chunks)} with {len(chunk)} IPs.")

        # Convert the chunk of IPs to a JSON-formatted string
        data = json.dumps(chunk)

        # Send the POST request
        response = requests.post(endpoint, data=data, headers=headers)

        # Check the response status code
        logging.info("Received response, checking status code.")
        if response.status_code == 200:
            # Parse and add the response data to all_ip_data
            logging.info(f"Processing successful response for chunk {chunk_index + 1}")
            ip_data = response.json()
            insert_api_response_into_db(ip_data)
        else:
            logging.error(f"Failed to retrieve data for chunk {chunk_index + 1}: HTTP {response.status_code}")
            logging.error(f"Response body: {response.text}")
        logging.info(f"Waiting for 5 seconds before next request to avoid rate limits.")
        time.sleep(5)  # Adjust sleep time if necessary

    logging.info("Completed updating IPs with country information.")

def insert_api_response_into_db(ip_data):
    if not ip_data:
        logging.error("No IP data to insert into the database. ip_data is None or empty.")
        return  # Exit the function early

    for item in ip_data:
        ip = item.get('query')  # Extract the IP address from the item
        if not ip:  # Ensure IP is present
            logging.warning(f"Skipping record with missing IP: {item}")
            continue

        # Extract all other necessary fields from the item
        country = item.get('country', None)  # Using .get() method with default fallback
        country_code = item.get('countryCode', None)
        region = item.get('region', None)
        city = item.get('city', None)
        latitude = item.get('lat', None)
        longitude = item.get('lon', None)
        timezone = item.get('timezone', None)
        isp = item.get('isp', None)
        as_description = item.get('as', None)
        org = item.get('org', None)

        try:
            insert_enriched_ip_data(ip, country, country_code, region, city, latitude, longitude, timezone, isp, as_description, org)
            logging.info(f"Inserted/Updated data for IP: {ip}")
        except Exception as e:
            logging.error(f"Error inserting/updating data for IP {ip}: {e}")




def main():
    ip_data = update_ips_with_country()  # Retrieve the IP data
    insert_api_response_into_db(ip_data)  # Pass the IP data as an argument to the function

    logging.info("Extracting latitude, longitude, and hover text from IP data.")
    lats = []
    lons = []
    text = []
    for data in ip_data:
        lat = data.get('lat')
        lon = data.get('lon')
        if lat is not None and lon is not None:
            lats.append(lat)
            lons.append(lon)
            text.append(f"{data['query']} - {data.get('city', 'Unknown')}")
        else:
            logging.debug(f"Missing lat/lon for IP: {data.get('query')}")

    logging.info(f"Extracted data for {len(lats)} locations.")
    if len(lats) < len(ip_data):
        logging.warning(f"Some IP data did not have latitude/longitude information.")

    logging.info(f"Extracted data for {len(lats)} locations.")
    if len(lats) < len(ip_data):
        logging.warning(f"Some IP data did not have latitude/longitude information.")

    # Create a scatter geo plot
    fig = go.Figure(data=go.Scattergeo(
        lon = lons,
        lat = lats,
        text = text,
        mode = 'markers',
        marker = dict(
            size = 8,
            opacity = 0.8,
            reversescale = True,
            autocolorscale = False,
            symbol = 'circle',
            line = dict(
                width=1,
                color='rgba(102, 102, 102)'
            ),
            colorscale = 'Viridis',
            cmin = 0,
            color = lats,
            colorbar_title="Some metric"
        )))

    # Update the layout to add map configurations
    fig.update_layout(
        title = 'IP Locations Worldwide',
        geo = dict(
            scope = 'world',
            showland = True,
            landcolor = "rgb(212, 212, 212)",
            subunitcolor = "rgb(255, 255, 255)",
            countrycolor = "rgb(255, 255, 255)",
            showlakes = True,
            lakecolor = "rgb(255, 255, 255)",
            showsubunits = True,
            showcountries = True,
            resolution = 50,
            projection = dict(
                type = 'mercator'
            ),
            lonaxis = dict(
                showgrid = True,
                gridwidth = 0.5,
                range= [ -180.0, 180.0 ],
                dtick = 5
            ),
            lataxis = dict (
                showgrid = True,
                gridwidth = 0.5,
                range= [ -90.0, 90.0 ],
                dtick = 5
            )
        )
    )

    # Show the figure
    fig.show()

if __name__ == "__main__":
    main()