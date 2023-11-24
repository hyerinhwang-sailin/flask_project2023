import json
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from database import DBhandler
import hashlib
import sys
import firebase_admin
from firebase_admin import credentials, db

application = Flask(__name__, template_folder="templates", static_folder="static")
application.config["SECRET_KEY"] = "helloosp"

DB = DBhandler()


# Firebase Admin SDK 초기화
cred = credentials.Certificate("authentication/market-ososo-firebase-adminsdk-j1xam-5e6e153b46.json")  # 자신의 서비스 계정 키 경로로 설정
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://market-ososo.firebaseio.com'  # Firebase 프로젝트의 데이터베이스 URL로 설정
})


@application.route("/")
def hello():
    # return render_template("index.html")
    return redirect(url_for('view_list'))


@application.route("/reg_items")
def reg_items():
    return render_template("reg_items.html")


@application.route("/list")
def view_list():
    page = request.args.get("page", 0, type=int)
    per_page = 6  # item count to display per page
    per_row = 3  # item count to display per row
    row_count = int(per_page / per_row)
    start_idx = per_page * page
    end_idx = per_page * (page + 1)
    data = DB.get_items()  # read the table
    item_counts = len(data)
    data = dict(list(data.items())[start_idx:end_idx])
    tot_count = len(data)
    for i in range(row_count):  # last row
        if (i == row_count - 1) and (tot_count % per_row != 0):
            locals()['data_{}'.format(i)] = dict(list(data.items())[i * per_row:])
        else:
            locals()['data_{}'.format(i)] = dict(list(data.items())[i * per_row:(i + 1) * per_row])
    return render_template("list.html", datas=data.items(), row1=locals()['data_0'].items(),
                           row2=locals()['data_1'].items(), limit=per_page,
                           page=page, page_count=int((item_counts / per_page) + 1), total=item_counts)


@application.route("/review")
def view_review():
    page = request.args.get("page", 0, type=int)
    per_page=6 # item count to display per page
    per_row=3# item count to display per row
    row_count=int(per_page/per_row)
    start_idx=per_page*page
    end_idx=per_page*(page+1)
    data = DB.get_reviews() #read the table
    item_counts = len(data)
    data = dict(list(data.items())[start_idx:end_idx])
    tot_count = len(data)
    for i in range(row_count):#last row
        if (i == row_count-1) and (tot_count%per_row != 0):
            locals()['data_{}'.format(i)] = dict(list(data.items())[i*per_row:])
        else:
            locals()['data_{}'.format(i)] = dict(list(data.items())[i*per_row:(i+1)*per_row])
    return render_template("review.html", datas=data.items(), row1=locals()['data_0'].items(), row2=locals()['data_1'].items(),
                           limit=per_page, page=page, page_count=int((item_counts/per_page)+1), total=item_counts)


@application.route("/view_review_detail/<name>/")
def view_review_detail(name):
    print("###review_name:", name)
    review_data = DB.get_review_byname(name)
    print("####review_data:", review_data)
    return render_template("review_detail.html", review_data=review_data)


@application.route("/reg_reviews")
def reg_reviews():
    return render_template("reg_reviews.html")


@application.route("/submit_item_post", methods=['POST'])
def reg_item_submit_post():
    image_file = request.files["file"]
    image_file.save("static/images/{}".format(image_file.filename))
    data = request.form
    DB.insert_item(data['name'], data, image_file.filename)
    return render_template("submit_item_result.html", data=data,
                           img_path="static/images/{}".format(image_file.filename))


@application.route("/login")
def login():
    return render_template("login.html")


@application.route("/login_confirm", methods=['POST'])
def login_user():
    id_ = request.form['id']
    pw = request.form['pw']
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    if DB.find_user(id_, pw_hash):
        session['id'] = id_
        return redirect(url_for('view_list'))
    else:
        flash("Wrong ID or PW!")
        return render_template("login.html")


@application.route("/signup")
def signup():
    return render_template("signup.html")


@application.route("/signup_post", methods=['POST'])
def register_user():
    data = request.form
    pw = request.form['pw']
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    if DB.insert_user(data, pw_hash):
        return render_template("login.html")
    else:
        flash("user id already exists!")
        return render_template("signup.html")


@application.route("/logout")
def logout_user():
    session.clear()
    return redirect(url_for('view_list'))


@application.route("/dynamicurl/<varible_name>/")
def DynamicUrl(varible_name):
    return str(varible_name)


@application.route("/view_detail/<name>/")
def view_item_detail(name):
    print("###name:", name)
    data = DB.get_item_byname(str(name))
    print("####data:", data)
    return render_template("detail.html", name=name, data=data)


@application.route("/search", methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        try:
            keyword = request.form['keyword']  # 폼 필드 이름을 'keyword'로 수정
            # DBhandler 클래스의 인스턴스를 생성
            db_handler = DB  # 괄호를 추가하지 않습니다.
            results = db_handler.search_items(keyword)  # 검색 결과를 가져옴

            # 검색 결과를 확인
            print("검색 결과:", results)

            # 검색 결과를 search_result.html로 렌더링
            return render_template("search_result.html", results=results)
        except KeyError:
            flash("Missing 'keyword' in the request.")
            return render_template("search.html")

    return render_template("search.html")


@application.route("/search_result", methods=['GET'])
def search_result():
    search_query = request.args.get("search")  # 검색어를 쿼리 파라미터로 받아옴

    # DB에서 검색 결과를 가져오는 로직 (DBhandler 클래스의 search_items 메서드 활용)
    results = DB.search_items(search_query)  # 검색 결과를 리스트로 받아옴

    # 검색 결과를 JSON 형식으로 반환
    return jsonify(results)


# Flask 애플리케이션 코드
@application.route("/view_item_details/<name>/")
def view_item_details(name):
    # DBhandler 클래스의 get_item_byname 메서드를 사용하여 해당 상품의 정보를 가져옵니다.
    data = DB.get_item_byname(name)

    if data:
        return render_template("detail.html", name=name, data=data)
    else:
        # 해당 상품이 존재하지 않을 경우 처리 (예: 에러 페이지 또는 다른 처리)
        return render_template("error.html", message="해당 상품을 찾을 수 없습니다.")


@application.route("/delete_item/<name>", methods=['POST'])
def delete_item(name):
    try:
        # DBhandler 클래스의 인스턴스를 생성
        db_handler = DB  # 괄호를 추가하지 않습니다.

        # 아이템 삭제를 시도하고 성공하면 상품 목록 페이지로 리디렉션
        if db_handler.delete_item(name):
            return redirect(url_for("view_list"))
        else:
            flash("Error deleting item.")
            return redirect(url_for("view_list"))
    except Exception as e:
        return str(e)


@application.route("/reg_review_init/<name>/")
def reg_review_init(name):
    return render_template("reg_reviews.html", name=name)


@application.route("/reg_review", methods=['POST'])
def reg_review():
    data = request.form
    DB.reg_review(data)
    return redirect(url_for('view_review'))


@application.route('/show_heart/<name>/', methods=['GET'])
def show_heart(name):
    if 'id' in session:
        my_heart = DB.get_heart_byname(session['id'], name)
        return jsonify({'my_heart': my_heart})
    else:
        # 사용자가 로그인되지 않은 경우에 대한 처리
        return jsonify({'error': '로그인이 필요합니다'})


@application.route('/like/<name>/', methods=['POST'])
def like(name):
    my_heart = DB.update_heart(session['id'],'Y',name)
    return jsonify({'msg': '좋아요 완료!'})


@application.route('/unlike/<name>/', methods=['POST'])
def unlike(name):
    my_heart = DB.update_heart(session['id'],'N',name)
    return jsonify({'msg': '안좋아요 완료!'})


if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
