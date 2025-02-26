import re
import unicodedata
import logging
from typing import List, Tuple


# ロガーの設定
logging.basicConfig(
    level=logging.INFO,  # ログレベルを INFO に設定
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 標準出力にログを表示
    ]
)
logger = logging.getLogger(__name__)


def assign_category(title: str) -> str:
    """タイトルに基づいてカテゴリを割り当てる"""
    logger.info("Starting category assignment for title: %s", title)

    patterns: List[Tuple[str, str]] = [
        (r"\d対\d", "対人"),
        (r"パス", "パス"),
        (r"ドリブル", "ドリブル"),
        (r"シュート", "シュート"),
        (r"キック", "キック"),
        (r"ビルドアップ", "ビルドアップ"),
        (r"(GK|キーパー)", "キーパー"),
        (r"(守備|ディフェンス)", "ディフェンス"),
        (r"(フィジカル|アジリティ|ストレッチ|ラダー)", "フィジカル"),
        (r"(考え方|コンセプト|指導)", "コンセプト/考え方"),
    ]
    for pattern, category in patterns:
        if re.search(pattern, title):
            logger.info("Category '%s' matched for pattern '%s'", category, pattern)
            return category

    logger.info("No category matched, returning 'その他'")
    return "その他"


def to_half_width(text: str) -> str:
    """全角→半角変換（数字・アルファベット・記号）"""
    text = unicodedata.normalize("NFKC", text)  # Unicode正規化
    text = re.sub(r"[０-９]", lambda x: chr(ord(x.group(0)) - 0xFEE0), text)  # 全角数字を半角に
    return text.strip()  # 余分な空白削除


def assign_number(title: str) -> str:
    """タイトルに基づいて必要人数を割り当てる"""
    title = to_half_width(title)  # 全角→半角変換
    logger.info("Starting number assignment for title: %s", title)

    if match := re.search(r"(\d+)人", title):
        logger.info("Number of people found: %s人", match.group(1))
        return f"{match.group(1)}人"

    if match := re.search(r"(\d+)対(\d+)", title):
        num1, num2 = int(match.group(1)), int(match.group(2))  # 数値化
        bigger, smaller = max(num1, num2), min(num1, num2)  # 大小比較
        logger.info("Number of people found: %s対%s (normalized to %s対%s)",
                    num1, num2, bigger, smaller)
        return f"{bigger}対{smaller}"  # 大きい数を前にする

    logger.info("No number found, returning empty string.")
    return "人数指定なし"


def assign_level(title: str) -> str:
    """タイトルに基づいてレベルを割り当てる"""
    logger.info("Starting level assignment for title: %s", title)

    levels: List[Tuple[str, str]] = [
        (r"(高校|高等)", "高校生"),
        (r"(中学|中等)", "中学生"),
        (r"ユース", "ユース"),
    ]
    for pattern, level in levels:
        if re.search(pattern, title):
            logger.info("Level '%s' matched for pattern '%s'", level, pattern)
            return level

    logger.info("No level matched, returning '小学生以上'")
    return "小学生以上"


def update_category(contents):
    """
    メイン処理: テーブルを作成し、カテゴリデータを更新
    """
    try:
        logger.info("Fetching contents from the database...")
        contents_data = []

        for content_id, title in contents:

            # カテゴリの予測
            category = assign_category(title)
            if category == "その他":
                category = "その他"  # 冗長なコードを削除

            # プレイヤー数の予測
            number_of_players = assign_number(title) or ""  # 空文字列をデフォルトに設定

            # レベルの予測
            level = assign_level(title)

            # カテゴリデータをデータベースに挿入
            #logger.info(f"Inserting data for content ID: {content_id}, Category: {category}, Players: {number_of_players}, Level: {level}")
            contents_data.append({
                "id": content_id,
                "category": category,
                "nop": number_of_players,
                "level": level
            })
            #db_access.insert_category_data(content_id, category, number_of_players, level)

        logger.info("Category assignment completed successfully.")
    #
    except Exception as e:
        logger.error("An error occurred during the main process: %s", e)
        raise
    #
    return contents_data


# if __name__ == "__main__":
#     try:
#         main()
#         print("カテゴリーの割り当てが完了しました。")
#     except Exception as e:
#         print(f"エラーが発生しました: {e}")
