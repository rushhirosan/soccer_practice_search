from flask import Flask, render_template, request, jsonify
from datetime import datetime
from utilities.db_access import get_channel_name_from_id
import os
import sqlite3
import unicodedata
import logging


# ロガーの設定
logging.basicConfig(
    level=logging.INFO,  # ログレベルを INFO に設定
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 標準出力にログを表示
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATABASE = 'soccer_content.db'


def convert_to_embed_url(video_url):
    """YouTubeの通常リンクからVIDEO_IDを抽出し、埋め込みリンクを生成する"""
    logger.info(f"Converting video URL: {video_url}")
    if "watch?v=" in video_url:
        video_id = video_url.split("watch?v=")[-1]
        return f"https://www.youtube.com/embed/{video_id}"
    return video_url  # 他のリンク形式の場合そのまま返す


def convert_activities(activities):
    """アクティビティリストのデータを変換する"""
    logger.info("Converting activities")
    result = []
    for activity in activities:
        activity_dict = dict(activity)
        dt = activity_dict["upload_date"].rstrip("Z")
        try:
            # 日本語形式（例: "2023年11月22日11時00分"）の場合
            date_obj = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            try:
                date_obj = datetime.strptime(dt, "%Y年%m月%d日%H時%M分")
            except ValueError:
                logger.error(f"Unsupported date format: {dt}")
                continue
        # 必要に応じてフォーマットを変換して保存
        activity_dict["upload_date"] = date_obj.strftime("%Y年%m月%d日%H時%M分")
        activity_dict["video_url"] = convert_to_embed_url(activity_dict["video_url"])
        activity_dict["channel_category"] = get_channel_name_from_id(activity_dict["channel_category"])
        result.append(activity_dict)
    return result


def get_db_connection():
    """データベース接続を取得する"""
    logger.info("Connecting to database: %s", DATABASE)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def build_query_with_filters(base_query, filters, params):
    """フィルタに基づいてクエリを構築する補助関数"""
    if filters.get('type_filter'):
        base_query += " AND category_title = ?"
        params.append(filters['type_filter'])

    if filters.get('players_filter'):
        base_query += " AND players = ?"
        params.append(filters['players_filter'])

    if filters.get('level_filter'):
        base_query += " AND level = ?"
        params.append(filters['level_filter'])

    if filters.get('channel_filter'):
        base_query += " AND channel_brand_category = ?"
        params.append(filters['channel_filter'])

    return base_query, params


def execute_query(conn, query, params):
    """クエリを実行し、結果を返す"""
    logger.info(f"Executing query: {query} with params: {params}")
    try:
        return conn.execute(query, params).fetchall()
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return []


def get_total_data_by_id(conn, q, ids):
    """IDリストに基づいて総データ数を取得"""
    if not ids:
        return 0

    placeholders = ', '.join(['?'] * len(ids))
    q_like = f"%{q}%" if q else None

    query = f'''
        SELECT count(*) FROM contents
        WHERE ID IN ({placeholders})
    '''
    params = ids
    if q:
        query += " AND title LIKE ?"
        params.append(q_like)

    return conn.execute(query, params).fetchone()[0]


def get_data_by_id(conn, q, ids, sort, offset, limit=None):
    """IDリストに基づいてデータを取得"""
    if not ids:
        return []

    placeholders = ', '.join(['?'] * len(ids))
    q_like = f"%{q}%" if q else None

    query = f'''
        SELECT * FROM contents
        WHERE ID IN ({placeholders})
    '''
    params = ids
    if q:
        query += " AND title LIKE ?"
        params.append(q_like)

    query += f" ORDER BY {sort} DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return execute_query(conn, query, params)


def multi_search_total(conn, q, filters):
    """複数のフィルタ条件に基づいて総データ数を取得"""
    base_query = "SELECT * FROM category WHERE 1=1"
    params = []
    base_query, params = build_query_with_filters(base_query, filters, params)
    print(base_query, params)

    rows = execute_query(conn, base_query, params)
    ids = [row["ID"] for row in rows]
    return get_total_data_by_id(conn, q, ids)


def multi_search(conn, q, filters, sort, offset, limit):
    """複数のフィルタ条件に基づいてデータを取得"""
    base_query = "SELECT * FROM category WHERE 1=1"
    params = []
    base_query, params = build_query_with_filters(base_query, filters, params)
    print("HIHI", base_query, params)

    rows = execute_query(conn, base_query, params)
    ids = [row["ID"] for row in rows]
    return get_data_by_id(conn, q, ids, sort, offset, limit)


@app.route('/search')
def search_activities():
    conn = get_db_connection()

    query = request.args.get('q', '')
    type_filter = request.args.get('type', '')
    players_filter = request.args.get('players', '')
    level_filter = request.args.get('level', '')
    channel_filter = request.args.get('channel', '')
    sort = request.args.get('sort', 'upload_date')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    filters = {
        'type_filter': type_filter,
        'players_filter': players_filter,
        'level_filter': level_filter,
        'channel_filter': channel_filter
    }

    if query:
        if not any([type_filter, players_filter, level_filter, channel_filter]):
            query = unicodedata.normalize('NFKC', query.strip())
            total = conn.execute('''
                SELECT count(*) FROM contents
                WHERE title LIKE ?
                COLLATE NOCASE
            ''', ['%' + query + '%']).fetchone()[0]

            activities = conn.execute(f'''
                SELECT * FROM contents
                WHERE title LIKE ?
                ORDER BY {sort} DESC
                LIMIT ? OFFSET ?
            ''', ['%' + query + '%', limit, offset]).fetchall()
        else:
            total = multi_search_total(conn, query, filters)
            activities = multi_search(conn, query, filters, sort, offset, limit)
    else:
        total = multi_search_total(conn, query, filters)
        activities = multi_search(conn, query, filters, sort, offset, limit)

    conn.close()

    current_display_count = len(activities) + offset

    return jsonify({
        "activities": convert_activities(activities),
        "total": total,
        "current_display_count": current_display_count
    })


def save_feedback_to_db(feedback):
    """フィードバックデータをデータベースに保存する"""
    logger.info(f"Saving feedback: {feedback}")
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO feedback (name, email, category, message) VALUES (?, ?, ?, ?)',
            (feedback['name'], feedback['email'], feedback['category'], feedback['message'])
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
    finally:
        conn.close()


# DBからユニークな値を取得する関数
def get_unique_values(column_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"""
        SELECT DISTINCT {column_name} 
        FROM category 
        WHERE {column_name} IS NOT NULL AND {column_name} != ''
        ORDER BY {column_name} ASC
    """
    cursor.execute(query)
    values = [row[0] for row in cursor.fetchall()]
    conn.close()
    return values


# APIエンドポイント
@app.route("/get_unique_values/<column>")
def get_unique_values_api(column):
    if column in ["category_title", "players"]:  # 安全のため制限
        return jsonify(get_unique_values(column))
    return jsonify({"error": "Invalid column"}), 400


def get_levels():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT level FROM category")
        levels = [{"level": row[0]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error loading level option: {e}")
    finally:
        conn.close()
    return levels


# APIエンドポイント（JSONでチャネル一覧を返す）
@app.route("/get_levels")
def get_levels_api():
    return jsonify(get_levels())


def get_channels():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, cname, clink FROM cid")
        channels = [{"id": row[0], "channel_name": row[1], "channel_link": row[2]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error loading channel option: {e}")
        channels = []
    finally:
        conn.close()
    return channels


# APIエンドポイント（JSONでチャネル一覧を返す）
@app.route("/get_channels")
def get_channels_api():
    return jsonify(get_channels())


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    data = request.json

    logger.info(f"Received feedback submission: {data}")

    # フィードバックの詳細を抽出
    feedback_details = {
        'name': data.get('name'),
        'email': data.get('email'),
        'category': data.get('category'),
        'message': data.get('message')
    }

    # フィードバックをデータベースに保存
    save_feedback_to_db(feedback_details)

    return jsonify({'message': 'Feedback submitted successfully'}), 200


@app.route('/')
def index():
    logger.info("Starting Flask application")
    return render_template('home.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # PORT環境変数を使用、無ければ5000
    app.run(host="0.0.0.0", port=port, debug=False)  # 0.0.0.0で外部アクセスを許可