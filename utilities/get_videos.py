import requests
import time
import isodate
import logging
from typing import Optional, List, Dict
import csv
import os

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,  # ログレベルを INFO に設定
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 標準出力にログを表示
    ]
)
logger = logging.getLogger(__name__)


def convert_duration(duration: str) -> str:
    """ISO 8601形式の動画長さを人間が読める形式に変換"""
    try:
        duration_obj = isodate.parse_duration(duration)
        return str(duration_obj)
    except Exception as e:
        logger.error("Failed to parse duration: %s. Error: %s", duration, e)
        return "N/A"


def fetch_video_details(video_ids: List[str], api_key: str) -> List[Dict]:
    """動画IDリストから詳細情報を取得"""
    video_details_url = f"https://www.googleapis.com/youtube/v3/videos?key={api_key}&id={','.join(video_ids)}&part=statistics,contentDetails"
    try:
        response = requests.get(video_details_url)
        response.raise_for_status()
        logger.info("Fetched video details for %d videos", len(video_ids))
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch video details: %s", e)
        return []


def fetch_videos_from_channel(channel_id: str, api_key: str, next_page_token: Optional[str] = None) -> Dict:
    """チャンネルから動画一覧を取得"""
    base_url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet&type=video&maxResults=50"
    url = f"{base_url}&pageToken={next_page_token}" if next_page_token else base_url
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info("Fetched video list for channel: %s", channel_id)
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch videos from channel: %s. Error: %s", channel_id, e)
        return {}


# def save_video_data_to_csv(output_file: str, video_data: List[Dict]):
#     """動画データをCSVファイルに保存"""
#
#     output_dir = os.path.dirname(output_file)
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#
#     try:
#         file_exists = os.path.isfile(output_file)  # ファイルが既に存在するか確認
#
#         with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
#             csvwriter = csv.writer(csvfile)
#
#             # ファイルが存在しない場合のみヘッダーを書き込む
#             if not file_exists:
#                 csvwriter.writerow(['ID', 'Title', 'Upload Date', 'Video URL', 'View Count',
#                                     'Like Count', 'Duration', 'Brand Title'])
#             for data in video_data:
#                 csvwriter.writerow([
#                     data.get('id', 'N/A'),
#                     data.get('title', 'N/A'),
#                     data.get('upload_date', 'N/A'),
#                     data.get('url', 'N/A'),
#                     data.get('view_count', 'N/A'),
#                     data.get('like_count', 'N/A'),
#                     data.get('duration', 'N/A'),
#                     data.get('channel_brand_category', 'N/A')
#                 ])
#
#         logger.info("Video data successfully saved to %s", output_file)
#
#     except Exception as e:
#         logger.error("Failed to save video data to CSV: %s", e)


def get_youtube_video_data(channel_id: str, api_key: str) -> List:
    """指定したチャンネルIDから動画データを取得しCSVに保存"""
    video_data = []
    next_page_token = None

    while True:
        channel_data = fetch_videos_from_channel(channel_id, api_key, next_page_token)
        if not channel_data:
            logger.warning("No data returned for channel ID: %s", channel_id)
            break

        video_ids = [item['id']['videoId'] for item in channel_data.get('items', [])]
        details = fetch_video_details(video_ids, api_key)

        for item in channel_data.get('items', []):
            video_id = item['id']['videoId']
            video_title = item['snippet']['title']
            ch_id = item['snippet']['channelId']
            #ch_title = item['snippet']['channelTitle']
            #ch_desc = item['snippet']['description']
            upload_date = item['snippet']['publishedAt']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # 詳細情報を検索
            detail = next((d for d in details if d['id'] == video_id), {})
            view_count = detail.get('statistics', {}).get('viewCount', 'N/A')
            like_count = detail.get('statistics', {}).get('likeCount', 'N/A')
            duration = convert_duration(detail.get('contentDetails', {}).get('duration', ''))

            video_data.append({
                'id': video_id,
                'title': video_title,
                'upload_date': upload_date,
                'url': video_url,
                'view_count': view_count,
                'like_count': like_count,
                'duration': duration
            })

        next_page_token = channel_data.get('nextPageToken')
        if not next_page_token:
            break

        time.sleep(1)  # API制限によりウェイトを追加

    #save_video_data_to_csv(output_file, video_data)
    logger.info("Video data collection completed for channel: %s", channel_id)
    return video_data
