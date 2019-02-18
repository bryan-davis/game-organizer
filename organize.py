# Project:      Game Organization
# Description:  This script reads through the games listed in the input
#               directory, and moves them into the output directory.
#               The initial directory is the country/region of origin. The 
#               secondary directory is the first character of the games
#               title if it starts with an alpha character, # if it
#               starts with a number.
# Author:       Bryan Davis
# Created:      10/25/2018
# Notes:        This script requires Python 3.6+ to run
#

import argparse
import logging
import os
import re
import shutil
import sys


ALPHA_NUMERIC = re.compile(r'([A-Za-z0-9])')
REGION = re.compile(r'\(([A-Za-z0-9 ,]+)\)')
NUMERIC = re.compile(r'\d+')

def abort(message):
    '''Logs the message as an error, along with a stacktrace,
    and exits with return code 1'''
    log.exception(message)
    log.error('Aborted')
    sys.exit(1)

def parse_args():
    '''Sets up script arguments'''
    parser = argparse.ArgumentParser(
        description='Organize games by country and first character of the title')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
        help='enable debug logging')
    parser.add_argument('-i', '--input-dir', dest='input_dir', required=True,
        help='directory that contains the games')
    parser.add_argument('-o', '--output-dir', dest='output_dir', required=True,
        help='destination of the organized games')
    return parser.parse_args()

def configure_logging(debug):
    '''Configures and returns a logger object'''
    level = logging.DEBUG if debug else logging.INFO
    # Directory this script is running in
    directory = os.path.dirname(os.path.realpath(__file__))
    # Script name without the .py extension
    script = os.path.splitext(os.path.basename(__file__))[0]
    # Script name with .log appended
    log_file = os.path.join(directory, f'{script}.log')
    logging.basicConfig(format='%(asctime)s [%(levelname)-5s] %(name)s | %(message)s',
        level=level, filename=log_file)
    return logging.getLogger()

def log_args():
    '''Log the arguments passed to the script'''
    log.info('*** Script Arguments Begin ***')
    for key, value in vars(args).items():
        log.info(f'{key}: {value}')
    log.info('*** Script Arguments End ***')

def create_dir(dir):
    try:
        os.makedirs(dir)
    except OSError as e:
        log.error(e)
        abort(f"Failed to create {dir}")

def get_destination_dir(region, first_char):
    if region in ('Europe', 'Japan', 'USA'):
        return os.path.join(args.output_dir, region, first_char)
    else:
        return os.path.join(args.output_dir, 'Other', region)

def move_game(game):
    match = REGION.search(game)
    if match:
        region = match.groups()[0]
        # There can be multiple regions in the matching group e.g. - (Japan, USA)
        # If USA is in there, we'll go with that. Otherwise, if there's a comma
        # then we'll go with the first region. Otherwise, we'll take the region
        # as it is -- this seems to only happen with Hong Kong
        if ',' in region:
            if 'USA' in region:
                region = 'USA'
            else:
                region = region.split(',')[0].strip()
    else:
        log.warning(f"Unable to find region in '{game}'; defaulting to USA")
        region = 'USA'
    
    match = ALPHA_NUMERIC.search(game)
    if not match:
        log.warning(f"Unable to determine the first alpha numeric character in '{game}'; skipping")
        return
    first_char = match.group()
    
    if NUMERIC.match(first_char):
        # Drop all numeric titles into #
        first_char = '#'

    destination_dir = get_destination_dir(region, first_char)
    if not os.path.exists(destination_dir):
        log.info(f"{destination_dir} not found; attempting to create")
        create_dir(destination_dir)

    source = os.path.join(args.input_dir, game)
    destination = os.path.join(destination_dir, game)
    log.info(f'Copy from {source} to {destination}')
    # Uncomment the line below to move files instead of copy (faster if on the same file system)
    #shutil.move(source, destination)
    shutil.copyfile(source, destination)

def organize():
    if not os.path.exists(args.input_dir):
        abort(f"Input directory: '{args.input_dir}' doesn't exist!")
    
    if not os.path.exists(args.output_dir):
        log.info(f"{args.output_dir} not found; attempting to create")
        create_dir(args.output_dir)

    game_count = 0
    for _, _, games in os.walk(args.input_dir):
        for game in games:
            if 'BIOS' in game:
                log.info(f'Skipping BIOS file: {game}')
                continue
            move_game(game)
            game_count += 1
    
    return game_count

if __name__ == '__main__':
    args = parse_args()
    log = configure_logging(args.debug)
    log.info('Start')
    log_args()
    game_count = organize()
    log.info(f'Processed {game_count} games')
    log.info('Finish')
