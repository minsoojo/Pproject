실행을 위해서 아래 절차를 따라 하세요

1. faiss index와 pkl을 다운 받고 /v0.9src/aidata에 넣기
   https://drive.google.com/file/d/1IVg0biw8KlTRGACTssuFu5Tlt5BT9O-v/view?usp=drive_link
3. .sql 파일 순서대로 다운 후 실행하기 (workbench에 db 생성(db.py에 맞게 만들어야함), sql 스크립트 실행)
   https://drive.google.com/file/d/1lETRorKnqdZSNAgBqfE1JJZjpzfB3ImI/view?usp=drive_link
   https://drive.google.com/file/d/1AqJFFgmwGhcLQ_tHCxBJh0VgKrfj6hSq/view?usp=drive_link
4. /v0.9src/muhanchatbot-main 으로 이동 후 npm run build

모두 끝났다면 
cd ./v0.9src/
python -m uvicorn Server.api.app:app --host 0.0.0.0 --port 5000 --reload
