from flask import Flask, render_template, request, jsonify, g
from datetime import datetime
from utilities.db_access import get_db_connection, pool, get_channel_name_from_id
from contextlib import closing
import os
import sqlite3
import unicodedata
import logging
import psycopg2


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
    #logger.info(f"Converting video URL: {video_url}")
    if "watch?v=" in video_url:
        video_id = video_url.split("watch?v=")[-1]
        return f"https://www.youtube.com/embed/{video_id}"
    return video_url  # 他のリンク形式の場合そのまま返す


def convert_activities(activities):
    """アクティビティリストのデータを変換する"""
    logger.info("Converting activities")
    result = []

    column_names = [
        "id", "title", "upload_date", "video_url", "view_count", 
        "like_count", "duration", "channel_category"
    ]  # カラム名を明示的に定義

    for activity in activities:
        # zip() を使ってタプルを辞書に変換
        activity_dict = dict(zip(column_names, activity))

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


def build_query_with_filters(base_query, filters, params):
    """フィルタに基づいてクエリを構築する補助関数"""
    if filters.get('type_filter'):
        base_query += " AND category_title = %s"
        params.append(filters['type_filter'])

    if filters.get('players_filter'):
        base_query += " AND players = %s"
        params.append(filters['players_filter'])

    if filters.get('level_filter'):
        base_query += " AND level = %s"
        params.append(filters['level_filter'])

    if filters.get('channel_filter'):
        base_query += " AND channel_brand_category = %s"
        params.append(filters['channel_filter'])

    return base_query, params


def execute_query(conn, query, params):
    """クエリを実行し、結果を返す"""
    logger.info(f"Executing query: {query} with params: {params}")    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        #print("results", results)
        return results
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return []


# def safe_query(conn, query, params):
#     """安全にクエリを実行する関数"""
#     logger.info(f"Executing safe query: {query} with params: {params}")
#     query = f"SELECT ID FROM contents WHERE ID IN ('ewMGrhiWc1E', 'vY8B71_TVLw', '6sFICjN9bPQ', 'hUBAMSuydJI', 'y_ZXOJJFyuA', 'EnZ95vi9RU8', 'TIu4PNw_PTQ', 'XPPl5NDFdMc', 'sYVfBvdc6Xo', 'HKcB-ZrL52Q');"
#     try:
#         #result = conn.execute(query, params)
#         result = conn.execute(query)
#         t = conn.fetchall()
#         print("RES", result, len(t))
#         if result is None:
#             logger.warning("Query returned no results.")
#             return None
# 
#         row = result.fetchone()
#         print("row", row)
#         if row is None:
#             logger.warning("No row found.")
#             return None
# 
#         return row[0]
# 
#     except Exception as e:
#         logger.error(f"Error executing query: {e}")
#         return None

def get_total_data_by_id(conn, q, ids):
    """IDリストに基づいて総データ数を取得"""

    conn = get_db_connection()

    if not ids:
        return 0

    # プレースホルダを作成
    placeholders = ', '.join(['%s'] * len(ids))

    # qが指定されている場合、titleのLIKE句のパラメータを作成
    q_like = f"%{q}%" if q else None

    # クエリの作成
    query = f'''
        SELECT count(*) FROM contents
        WHERE ID IN ({placeholders})
    '''

    # パラメータをidsとして設定
    params = ids

    # qが指定されている場合、LIKE句を追加
    if q:
        query += " AND title LIKE %s"
        params.append(q_like)

    print("THISIS", query, params)

    cursor = conn.cursor()  # カーソルを取得

    # クエリを実行
    cursor.execute(query, params)

    # 結果を取得
    result = cursor.fetchone()  # 1行を取得

    if result:
        count = result[0]  # count(*)の値
    else:
        count = 0

    cursor.close()  # カーソルを閉じる

    return count


# def get_total_data_by_id(conn, q, ids):
#     """IDリストに基づいて総データ数を取得"""
#     #print("HOIHIOHIOHOIHI", q, ids)
#
#     if not ids:
#         return 0
#
#     placeholders = ', '.join(['%s'] * len(ids))
#     q_like = f"%{q}%" if q else None
#
#     query = f'''
#         SELECT count(*) FROM contents
#         WHERE ID IN ({placeholders})
#     '''
#     params = ids
#     if q:
#         query += " AND title LIKE %s"
#         params.append(q_like)
#
#     print("THISIS", query, params)
#
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     res = cursor.execute(query, params)
#     print("WWWW", res)
#
#     return res

    #result = conn.execute(query, params).fetchone()
    # if result is not None:
    #     return result[0]
    # else:
    #     return 0  # 該当するレコードがない場合、0を返す

    #return conn.execute(query, params).fetchone()[0]
    # count = safe_query(conn, query, params)
    # #print(count)
    # if count is None:
    #     logger.info("No data found, count set to 0")
    #     count = 0


def get_data_by_id(conn, q, ids, sort, offset, limit=None):
    """IDリストに基づいてデータを取得"""
    if not ids:
        return []

    # PostgreSQL では %s を使う
    placeholders = ', '.join(['%s'] * len(ids))
    q_like = f"%{q}%" if q else None

    # クエリ構築
    query = f'''
        SELECT * FROM contents
        WHERE ID IN ({placeholders})
    '''
    params = ids

    if q:
        query += " AND title LIKE %s"
        params.append(q_like)

    query += f" ORDER BY {sort} DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    # クエリ実行
    return execute_query(conn, query, params)



def multi_search_total(conn, q, filters):
    """複数のフィルタ条件に基づいて総データ数を取得"""
    base_query = "SELECT * FROM category WHERE 1=1"
    params = []
    base_query, params = build_query_with_filters(base_query, filters, params)

    rows = execute_query(conn, base_query, params)
    #ids = [row["ID"] for row in rows]
    #print("rows", rows)
    ids = [row[0] for row in rows]
    print(ids)
    return get_total_data_by_id(conn, q, ids)


def multi_search(conn, q, filters, sort, offset, limit):
    """複数のフィルタ条件に基づいてデータを取得"""
    base_query = "SELECT * FROM category WHERE 1=1"
    params = []
    base_query, params = build_query_with_filters(base_query, filters, params)
    #print("HIHI", base_query, params)

    rows = execute_query(conn, base_query, params)
    #ids = [row["ID"] for row in rows]
    ids = [row[0] for row in rows]
    return get_data_by_id(conn, q, ids, sort, offset, limit)


@app.route('/search')
def search_activities():
    
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

    conn = get_db_connection()
    with closing(conn.cursor()) as c:  # ✅ カーソルのみ `closing` を使用
        try:
            if query:
                if not any([type_filter, players_filter, level_filter, channel_filter]):
                    query = unicodedata.normalize('NFKC', query.strip())

                    c.execute('''
                        SELECT count(*) FROM contents
                        WHERE title ILIKE %s
                    ''', ('%' + query + '%',))  # ✅ `?` → `%s` に修正 (PostgreSQL 用)

                    total = c.fetchone()[0]

                    c.execute(f'''
                        SELECT * FROM contents
                        WHERE title ILIKE %s
                        ORDER BY {sort} DESC
                        LIMIT %s OFFSET %s
                    ''', ('%' + query + '%', limit, offset))

                    activities = c.fetchall()
                else:
                    total = multi_search_total(c, query, filters)
                    activities = multi_search(c, query, filters, sort, offset, limit)
            else:
                total = multi_search_total(c, query, filters)
                activities = multi_search(c, query, filters, sort, offset, limit)

        except psycopg2.Error as e:
            logger.error("Error while executing search query: %s", e)
            return jsonify({"error": "Database error"}), 500  # HTTP 500 を返す

    current_display_count = len(activities) + offset

    #conn.close()

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
        with conn.cursor() as c:
            c.execute(
                'INSERT INTO feedback (name, email, category, message) VALUES (%s, %s, %s, %s)',
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


@app.teardown_appcontext
def close_db(error):
    """リクエストが終わったら接続を閉じる"""
    db = g.pop('db', None)
    if db is not None:
        #db.close()
        pool.putconn(db)
        logger.info("Closing database connection...")


@app.route('/')
def index():
    logger.info("Starting Flask application")
    return render_template('home.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # PORT環境変数を使用、無ければ5000
    app.run(host="0.0.0.0", port=port, debug=True)  # 0.0.0.0で外部アクセスを許可