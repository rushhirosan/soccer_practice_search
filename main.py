from utilities.get_videos import get_youtube_video_data
from utilities.get_channel_id import get_channel_id, get_channel_details
from utilities.db_access import create_cid_table, get_db_connection, insert_cid_data, create_contents_table, insert_contents_data, create_category_table, search_content_table, insert_category_data, create_feedback_table
from utilities.update_category_db import update_category
from flask import Flask
import os
import sys
from dotenv import load_dotenv
import logging

app = Flask(__name__)

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    with app.app_context():

    #     get_youtube_video_data(cid, api_key, output_file)
    #     logger.info(cid + "is finished well.")
    #########################################################

    #########################################################
    ## cid table setup
    #########################################################
        load_dotenv("./utilities/.env")
        #output_file = '../misc/youtube_video_data.csv'
    
        get_db_connection()
        api_key = os.getenv('API_KEY')
    
        if not api_key:
            logger.error("API key is missing. Please set it in the .env file.")
            sys.exit(1)
    
        # if len(sys.argv) < 2:
        #     logger.error("Please provide a YouTube channel name as a command-line argument.")
        #     sys.exit(1)
        #
        # channel_name = sys.argv[1]  # コマンドライン引数からチャンネル名を取得
        # cid = get_channel_id(channel_name, api_key)
        # if cid:
        #     logger.info("Channel ID: %s", cid)
        # else:
        #     logger.error("Failed to retrieve channel ID.")
        #     sys.exit(1)
    
        channel_id = os.getenv('CHANNEL_ID')
        channel_link = os.getenv('CHANNEL_LINK')
        channels = channel_id.split(",")
        channel_links = channel_link.split(",")
        create_cid_table()
    
        for c_num, cid in enumerate(channels, start=1):
            channel_name = get_channel_details(cid, api_key)
            #print(c_num, cid, channel_name, channel_links[c_num-1])
            if channel_name == "N/A":
                logger.error("Failed to retrieve channel name.")
                sys.exit(1)
            ########################################################
            ## contents setup
            ########################################################
            insert_cid_data(cid, channel_name, channel_links[c_num-1])
            create_contents_table()
            video_data = get_youtube_video_data(cid, api_key)
            # for data in video_data:
            #     print(data)
            #     print(data['id'], data['title'], data['upload_date'], data['url'],
            #               data['view_count'], data['like_count'], data['duration'], c_num)
            insert_contents_data(video_data, c_num)
            #########################################################
            ## category setup
            #########################################################
            create_category_table()
            contents = search_content_table() # search table parameter not work
            contents_data = update_category(contents)
            insert_category_data(contents_data, c_num)

        create_feedback_table()
        logger.info("feedback table created. All processes finished successfully")

