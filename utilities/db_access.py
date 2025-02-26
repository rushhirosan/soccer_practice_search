import sqlite3
import logging
from contextlib import closing
import pandas as pd
from collections import defaultdict

# データベースに接続し、コンテキストマネージャを使って自動で接続を閉じる
DATABASE_PATH = './soccer_content.db'
#file_path = "../misc/youtube_video_data.csv"

# TABLES
# contents, category, feedback, cid

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,  # ログレベルを INFO に設定
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 標準出力にログを表示
    ]
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """データベース接続を取得"""
    logger.info("Establishing database connection...")
    return sqlite3.connect(DATABASE_PATH)


def delete_table(tbl_name: str):
    """テーブルを削除して、データを削除"""
    logger.info(f"Deleting data and dropping {tbl_name} table if it exists...")
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        try:
            c.execute(f"DELETE FROM {tbl_name};")
            c.execute(f'DROP TABLE IF EXISTS {tbl_name}')
            conn.commit()
            logger.info(f"{tbl_name} table deleted successfully.")
        except sqlite3.Error as e:
            logger.error("Error while deleting table: %s", e)


def create_table(query: str):
    """テーブル作成の汎用関数"""
    logger.info("Creating table...")
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        try:
            c.execute(query)
            conn.commit()
            logger.info("Table created successfully.")
        except sqlite3.Error as e:
            logger.error("Error while creating table: %s", e)


def create_cid_table():
    """`cid`テーブルを作成"""
    logger.info("Creating 'cid' table...")
    query = '''
        CREATE TABLE IF NOT EXISTS cid (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cid TEXT UNIQUE,
            cname TEXT,
            clink TEXT
        )
    '''
    create_table(query)


def create_contents_table():
    """`contents`テーブルを作成"""
    logger.info("Creating 'contents' table...")
    query = '''
        CREATE TABLE IF NOT EXISTS contents (
            ID TEXT PRIMARY KEY,
            title TEXT,
            upload_date TEXT,
            video_url TEXT,
            view_count INTEGER,
            like_count INTEGER,
            duration TEXT,
            channel_category INTEGER
        )
    '''
    create_table(query)


def create_category_table():
    """`category`テーブルを作成"""
    logger.info("Creating 'category' table...")
    query = '''
        CREATE TABLE IF NOT EXISTS category (
            ID TEXT PRIMARY KEY,
            category_title TEXT,
            players TEXT,
            level TEXT,
            channel_brand_category INTEGER,
            FOREIGN KEY (channel_brand_category) REFERENCES cid(id) ON DELETE CASCADE            
        )
    '''
    create_table(query)


def create_feedback_table():
    """`feedback`テーブルを作成"""
    logger.info("Creating 'feedback' table...")
    query = '''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            category TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    create_table(query)


def insert_cid_data(cid: str, cname: str, clink: str):
    """`cid`テーブルにデータを挿入"""
    logger.info("Inserting data into 'cid' table...")
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        try:
            c.execute('''
                INSERT OR IGNORE INTO cid (cid, cname, clink)
                VALUES (?, ?, ?)
            ''', (cid, cname, clink))
            conn.commit()
            logger.info("Data inserted into 'cid' table successfully.")
        except sqlite3.Error as e:
            logger.error("Error while inserting data into 'cid' table: %s", e)


def insert_category_data(contents_data, channel_category):
    """`category`テーブルにデータを挿入"""
    logger.info("Inserting data into 'category' table...")
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        try:
            for data in contents_data:
                c.execute('''
                    INSERT OR IGNORE INTO category (ID, category_title, players, level, channel_brand_category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (data["id"], data["category"], data["nop"], data["level"], channel_category))
                conn.commit()
            logger.info("Data inserted into 'category' table successfully.")
        except sqlite3.Error as e:
            logger.error("Error while inserting data into 'category' table: %s", e)


def insert_contents_data(video_data, channel_category):
    """CSVファイルからデータをデータベースに挿入"""
    logger.info("Inserting data from CSV into 'contents' table...")
    #df = pd.read_csv(file_path)
    #duplicates = find_duplicates(df)

    # if duplicates:
    #     r = input(f"Duplicate IDs found: {duplicates}. Do you want to delete them? (y/n): ")
    #     if r.lower() == "y":
    #         df = df.drop_duplicates(subset="ID", keep="first")
    #         df.to_csv(file_path, index=False)
    #         logger.info("Duplicates removed and CSV file updated.")
    #     else:
    #         logger.info("Processing stopped due to duplicate IDs.")
    #         return
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        try:
            for data in video_data:
                c.execute('''
                    INSERT OR IGNORE INTO contents (id, title, upload_date, video_url, 
                    view_count, like_count, duration, channel_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data['id'], data['title'], data['upload_date'], data['url'],
                      data['view_count'], data['like_count'], data['duration'], channel_category))
                logger.info("Inserted data for video ID: %s", data['id'])
        except sqlite3.Error as e:
            logger.error("Error while inserting data for ID %s: %s", data['id'], e)
        conn.commit()
        logger.info("All data inserted successfully into 'contents' table.")
        # for _, row in df.iterrows():
        #     c.execute('SELECT 1 FROM contents WHERE ID = ?', (row['ID'],))
        #     if c.fetchone():
        #         logger.info("Skipping duplicate ID: %s", row['ID'])
        #         continue

        # try:
        #     c.execute('''
        #         INSERT OR IGNORE INTO contents (ID, title, upload_date, video_url, view_count, like_count, duration)
        #         VALUES (?, ?, ?, ?, ?, ?, ?)
        #     ''', (row['ID'], row['Title'], row['Upload Date'], row['Video URL'],
        #           row['View Count'], row['Like Count'], row['Duration']))
        #     logger.info("Inserted data for video ID: %s", row['ID'])


def search_content_table():
    """`contents`テーブルを検索"""
    logger.info("Searching data in 'contents' table...")
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        query = 'SELECT * FROM contents'
        c.execute(query)
        results = c.fetchall()
        logger.info("Search completed. Found %d records.", len(results))
        return [[result[0], result[1]] for result in results]

# def search_table(search_term: str = None):
#     """`contents`テーブルからデータを検索"""
#     logger.info("Searching data in 'contents' table...")
#     with closing(get_db_connection()) as conn:
#         c = conn.cursor()
#         query = 'SELECT * FROM contents'
#         if search_term:
#             query += ' WHERE title LIKE ?'
#             logger.info("Searching for records containing: %s", search_term)
#             c.execute(query, ('%' + search_term + '%',))
#         else:
#             c.execute(query)
#
#         results = c.fetchall()
#         logger.info("Search completed. Found %d records.", len(results))
#         return [[result[0], result[1]] for result in results]


def get_channel_name_from_id(id):
    """ 指定した ID のチャンネル名を取得 """
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        query = 'SELECT cname FROM cid WHERE id = ?'  # プレースホルダーを使用
        c.execute(query, (id,))  # タプルで値を渡す
        result = c.fetchone()  # 1行のみ取得
        return result[0] if result else None  # データがあれば返す、なければ None


def search_db():
    """データベースのテーブル一覧を表示"""
    logger.info("Fetching list of tables in the database...")
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        table_names = [table[0] for table in tables]
        logger.info("Tables found: %s", table_names)
        print("テーブル一覧:", table_names)


def search_term_in_table(table, term):
    """`table`テーブルの`term`を検索"""
    # logger.info("Searching data in 'contents' table...")
    # with closing(get_db_connection()) as conn:
    #     c = conn.cursor()
    #     query = 'SELECT * FROM contents'
    #     c.execute(query)
    #     results = c.fetchall()
    #     logger.info("Search completed. Found %d records.", len(results))
    #     return [[result[0], result[1]] for result in results]

# def find_duplicates(df: pd.DataFrame) -> list:
#     """重複したIDを検索"""
#     logger.info("Searching for duplicate IDs...")
#     id_count = defaultdict(int)
#     for _, row in df.iterrows():
#         id_count[row["ID"]] += 1
#     duplicates = [k for k, v in id_count.items() if v >= 2]
#     if duplicates:
#         logger.warning("Duplicate IDs found: %s", duplicates)
#     return duplicates


# if __name__ == '__main__':
#     # USAGE
#     #delete_table("feedback")
#     create_base_table()
#     create_feedback_table()
#     insert_contents_data()
#     #insert_category_data()
#     # search_term = 'ドリブル'
#     # contents = search_table(search_term)
#     # print(contents)
