"""로컬 실행 진입점 — python app.py 또는 flask run"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.index import app

if __name__ == '__main__':
    print("\n  네이버 블로그 자동 발행기")
    print("  http://localhost:5000\n")
    app.run(debug=True, port=5000)
