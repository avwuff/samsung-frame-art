import argparse
import json
import logging
import os
import random
import sys

sys.path.append('../')

from samsungtvws import SamsungTVWS

# Add command line argument parsing
parser = argparse.ArgumentParser(description='Upload images to Samsung TV.')
parser.add_argument('--upload-all', action='store_true', help='Upload all images at once')
parser.add_argument('--debug', action='store_true', help='Enable debug mode to check if TV is reachable')
# parser.add_argument('--matte', action)
args = parser.parse_args()

# Set the path to the folder containing the images
folder_path = '/images/'

# Set the path to the file that will store the list of uploaded filenames
upload_list_path = '/container/uploaded_files.json'

# Load the list of uploaded filenames from the file
if os.path.isfile(upload_list_path):
    with open(upload_list_path, 'r') as f:
        uploaded_files = json.load(f)
else:
    uploaded_files = []

# Increase debug level
logging.basicConfig(level=logging.INFO)

# Autosave token to file
token_file = '/tokens/tv-token.txt'
# Set your TVs local IP address. Highly recommend using a static IP address for your TV.
tv = SamsungTVWS(host='192.168.2.64', port=8002, token_file=token_file)

# Check if TV is reachable in debug mode
if args.debug:
    try:
        logging.info('Checking if the TV can be reached.')
        info = tv.rest_device_info()
        logging.info("Device info: ")
        logging.info(info)
        logging.info('If you do not see an error, your TV could be reached.')

        print("")
        print("CURRENT ARTWORK")
        logging.info(tv.art().get_current())

        print("")
        print("MATTE LIST")
        print(tv.art().get_matte_list())

        print("")
        print("PHOTO FILTER LIST")
        print(tv.art().get_photo_filter_list())

        print("")
        print("ART MODE ACTIVE?")
        print(tv.art().get_artmode())

        sys.exit()
    except Exception as e:
        logging.error('Could not reach the TV: ' + str(e))
        sys.exit()

# Checks if the TV supports art mode
art_mode = tv.art().supported()

default_matte = "shadowbox_black"

if art_mode:
    # Retrieve information about the currently selected art
    # current_art = tv.art().get_current()

    # Determine if Art Mode is enabled right now
    art_mode_on = tv.art().get_artmode() == "on"

    # If not, just exit, otherwise we'd be changing the picture while the TV is in use
    if not art_mode_on and not args.upload_all:
        logging.info("Art mode is not currently enabled, exiting")
        exit(0)

    # Get a list of JPG/PNG files in the folder, and searches recursively if you want to use subdirectories
    files = [os.path.join(root, f) for root, dirs, files in os.walk(folder_path) for f in files if
             f.endswith('.jpg') or f.endswith('.png')]

    files_to_upload = []
    if args.upload_all:
        logging.info('Bulk uploading all photos. This may take a while...')

        # Remove the filenames of images that have already been uploaded
        files = list(set(files) - set([f['file'] for f in uploaded_files]))
        files_to_upload = files
    else:
        if len(files) == 0:
            logging.info('No new images to upload.')
            exit(0)
        else:

            # Make a lookup list of files we HAVE uploaded
            print("previously uploaded files: ", len(uploaded_files))
            lookup_list = {}
            for uploaded_file in uploaded_files:
                lookup_list[uploaded_file['file']] = True

            # Make a list of all the files that we haven't yet uploaded
            limited_list = []
            for file in files:
                if not (file in lookup_list):
                    limited_list.append(file)

            print("files not yet uploaded: ", len(limited_list))
            if len(limited_list) == 0:
                logging.info("All files have already been uploaded, picking a random image now.")
                files_to_upload = [random.choice(files)]

            else:
                logging.info('Choosing random image')
                files_to_upload = [random.choice(limited_list)]

    for file in files_to_upload:
        # Read the contents of the file
        with open(file, 'rb') as f:
            data = f.read()

        # Upload the file to the TV and select it as the current art, or select it using the remote filename if it has already been uploaded
        remote_filename = None
        for uploaded_file in uploaded_files:
            if uploaded_file['file'] == file:
                remote_filename = uploaded_file['remote_filename']
                logging.info('Image already uploaded.')
                break
        # See if the image was found on the remote end
        if remote_filename is None:
            logging.info('Uploading new image: ' + str(file))

            try:
                if file.endswith('.jpg'):
                    remote_filename = tv.art().upload(data, file_type='JPEG', matte=default_matte)
                elif file.endswith('.png'):
                    remote_filename = tv.art().upload(data, file_type='PNG', matte=default_matte)
            except Exception as e:
                logging.error('There was an error: ' + str(e))
                sys.exit()

            # Add the filename to the list of uploaded filenames
            uploaded_files.append({'file': file, 'remote_filename': remote_filename})

            if not args.upload_all:
                # Select the uploaded image using the remote file name
                tv.art().select_image(remote_filename, show=True)

        else:
            if not args.upload_all:
                # Select the image using the remote file name only if not in 'upload-all' mode
                logging.info('Setting existing image, skipping upload')
                tv.art().select_image(remote_filename, show=True)

        # Save the list of uploaded filenames to the file
        with open(upload_list_path, 'w') as f:
            json.dump(uploaded_files, f)
else:
    logging.warning('Your TV does not support art mode.')
