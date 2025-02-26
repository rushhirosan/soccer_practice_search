import os


def restart():
    files_to_delete = ["./soccer_content.db"]

    for file in files_to_delete:
        if os.path.exists(file):  # ファイルが存在するか確認
            os.remove(file)       # ファイルを削除
            print(f"Deleted: {file}")
        else:
            print(f"File not found: {file}")


if __name__ == '__main__':
    restart()
