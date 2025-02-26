import requests
import logging
from typing import Optional

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,  # ログレベルを INFO に設定
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 標準出力にログを表示
    ]
)
logger = logging.getLogger(__name__)


def get_channel_details(channel_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=brandingSettings&id={channel_id}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if 'items' in data and len(data['items']) > 0:
        return data['items'][0]['brandingSettings']['channel'].get('title', 'N/A')
    return 'N/A'


def get_channel_id(handle: str, api_key: str) -> Optional[str]:
    """チャンネルハンドルからチャンネルIDを取得する"""
    logger.info("Fetching channel ID for handle: %s", handle)
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={handle}&type=channel&key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # ステータスコードがエラーの場合例外を発生

        data = response.json()
        for item in data.get('items', []):
            channel_id = item['id']['channelId']
            logger.info("Channel ID found: %s", channel_id)
            return channel_id

        logger.warning("No channel ID found for handle: %s", handle)
        return None

    except requests.exceptions.RequestException as e:
        logger.error("Error fetching channel ID: %s", e)
        return None


# # RUN THIS AS python get_channel_id.py @REGATE
# if __name__ == '__main__':
#     load_dotenv()
#     api_key = os.getenv('API_KEY')
#
#     if not api_key:
#         logger.error("API key is missing. Please set it in the .env file.")
#     else:
#         if len(sys.argv) < 2:
#             logger.error("Please provide a YouTube channel name as a command-line argument.")
#         else:
#             channel_name = sys.argv[1]  # コマンドライン引数からチャンネル名を取得
#             cid = get_channel_id(channel_name, api_key)
#             if cid:
#                 logger.info("Channel ID: %s", cid)
#             else:
#                 logger.error("Failed to retrieve channel ID.")
