from geopy.geocoders import Nominatim, options
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from PIL import Image
import os
import shutil
import argparse
import exifread
from fractions import Fraction
import ssl
import certifi
from tqdm import tqdm
import datetime

def get_location(image):
    """Return the location of the image as a (latitude, longitude) tuple."""
    with open(image, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        latitude_ref = tags.get('GPS GPSLatitudeRef').printable
        latitude_str = tags.get('GPS GPSLatitude').printable
        longitude_ref = tags.get('GPS GPSLongitudeRef').printable
        longitude_str = tags.get('GPS GPSLongitude').printable

    # Split latitude and longitude strings by comma
    latitude_parts = [part.strip() for part in latitude_str.replace('[','').replace(']','').split(',')]
    longitude_parts = [part.strip() for part in longitude_str.replace('[','').replace(']','').split(',')]

    # Convert degrees, minutes, and seconds to decimal degrees
    latitude = (float(latitude_parts[0]) + float(latitude_parts[1])/60 + float(Fraction(latitude_parts[2])/Fraction(60*60)))
    longitude = (float(longitude_parts[0]) + float(longitude_parts[1])/60 + float(Fraction(longitude_parts[2])/Fraction(60*60)))

    if latitude_ref == 'S':
        latitude = -latitude
    if longitude_ref == 'W':
        longitude = -longitude

    return latitude, longitude



def get_location_name(latitude, longitude):
    """Return the location name (city) for the given (latitude, longitude) pair."""
    geolocator = Nominatim(user_agent="photo-sorter")
    location = None
    while location is None:
        try:
            location = geolocator.reverse(f"{latitude}, {longitude}")
        except GeocoderTimedOut:
            print(f"Geocoding timed out, retrying...")
    address = location.raw['address']
    keys = ['city', 'town', 'village', 'hamlet', 'county', 'municipality']
    city = next((address.get(key, '') for key in keys if address.get(key)), '')
    return city


def sort_images(source_dir, dest_dir):
    """Sort images in source_dir by location data and copy them to dest_dir."""
    for dir_path in [dest_dir, os.path.join(dest_dir, 'no_location')]:
        os.makedirs(dir_path, exist_ok=True)
    for root, _, files in os.walk(source_dir):
        for file in tqdm(files):
            if not file.lower().endswith(('.jpg', '.jpeg', '.png', '.mov', '.mp4')):
                continue
            try:
                image = os.path.join(root, file)
                lat, lon = get_location(image)
                location_name = get_location_name(lat, lon).split(",")[0]
                folder_path = os.path.join(dest_dir, location_name)
            except (KeyError, TypeError, ValueError, AttributeError, GeocoderServiceError):
                timestamp = os.path.getmtime(image)
                date = datetime.datetime.fromtimestamp(timestamp)
                year = date.year
                quarter = (date.month - 1) // 3 + 1
                quarter_dir = os.path.join(dest_dir, 'no_location', f"{year}Q{quarter}")
                folder_path = quarter_dir
            os.makedirs(folder_path, exist_ok=True)
            shutil.copy(image, folder_path)


if __name__ == "__main__":
    ctx = ssl.create_default_context(cafile=certifi.where())
    options.default_ssl_context = ctx
    parser = argparse.ArgumentParser(description="Sort images by location data")
    parser.add_argument("source_dir", help="the source directory to scan for images")
    parser.add_argument("dest_dir", help="the destination directory to copy sorted images to")
    args = parser.parse_args()

    sort_images(args.source_dir, args.dest_dir)
