from flask import *
from sqlalchemy import *
from sqlalchemy.orm import *
import requests


app = Flask(__name__)
app.secret_key = "dont tell anyone"
engine = create_engine("postgres://wrsiodovoscfsd:5d828aea4d469e6a58aa746ee24055a40e161ebe02625608837041a970fcd59f@ec2-3-222-30-53.compute-1.amazonaws.com:5432/d137aupaptr5g")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["Get", "POST"])
def index():
    if request.method == "GET":
        return render_template("login.html")

    else:
        name = request.form.get('username')
        password = request.form.get('password')
        session['username'] = name

        userExist = db.execute("Select * from users where username = :username", {"username":name}).fetchone()
        if userExist is None:
            flash(Markup("Not a member? <a href='/register'> Click here to Register! </a>"))
            return redirect(url_for('index'))
        if userExist.password == password:
            return render_template("search.html")
        else:
            flash("The password is incorrect!")
            flash("Please try Again!")
            flash(Markup("Forgot Password? <a href='/reset'> Click here Reset Password! </a>"))
            return redirect(url_for('index'))


@app.route("/reset", methods=["GET","POST"])
def reset():
    if request.method == "GET":
        return render_template("reset.html")
    else:
        user = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if user == '':
            flash("Please Enter your User-name.")
            return redirect(url_for('reset'))
        elif password == '':
            flash("Please Set a New Password.")
            return redirect(url_for('reset'))
        elif confirm == '':
            flash("Please Re-Enter your Password.")
            return redirect(url_for('reset'))
        elif password != confirm:
            flash("The two Passwords do not match!")
            return redirect(url_for('reset'))
        elif len(password) < 5:
            flash("The length of the password should atleast be 5 characters!")
            return redirect(url_for('reset'))
        else:
            db.execute("UPDATE users set password = :password where username = :username", {"password":password, "username":user})
            db.commit()
            return render_template("success.html", message="Password Reset Successfully!")



@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        uname = request.form.get("uname")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if fname == '':
            flash("Enter your First Name")
            return redirect(url_for('register'))
        elif lname == '':
            flash("Enter your Last Name")
            return redirect(url_for('register'))
        elif uname == '':
            flash("Enter your User Name")
            return redirect(url_for('register'))
        elif password == '':
            flash("Please set a password!")
            return redirect(url_for('register'))
        elif confirm == '':
            flash("Enter your First Name")
            return redirect(url_for('register'))
        elif password != confirm:
            flash("The passwords do not match!")
            return redirect(url_for('register'))
        elif len(password) < 5:
            flash("The length of the password should atleast be 5 characters!")
            return redirect(url_for('register'))
        else:
            db.execute("INSERT into users values (:first, :last, :username, :password)",
                       {"first": fname, "last": lname, "username": uname, "password": password})
            db.commit()
        return render_template(url_for('success'), message="Registration Successful")


@app.route("/success", methods=["GET", "POST"])
def success():
    return render_template("success.html")


@app.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "POST":
        selection = request.form.get("search")
        search = request.form.get("entity")
        if search == "":
            return render_template("error.html", message="Please enter a Valid Search Entity", way='search')
        elif selection == "Title":
            result = db.execute(f"SELECT * from books where lower(title) like '%{search.lower()}%'").fetchall()
            #print(result)
            if len(result) == 0:
                return render_template("error.html", message="No books matching with your query found!", way='search')
            else:
                for i in range(len(result)):
                    return render_template("result.html", result=result)

        elif selection == "ISBN":
            if search.isnumeric() is False:
                return render_template("error.html", message="Invalid Search Query. Please use Digits Only!",
                                       way='search')
            result = db.execute(f"SELECT * from books where isbn = :isbn", {'isbn':search}).fetchall()
            #print(result)
            if len(result) == 0:
                return render_template("error.html", message="No books matching with your query found!", way='search')
            else:
                for i in range(len(result)):
                    return render_template("result.html", result=result)

        elif selection == "Author":
            result = db.execute(f"SELECT * from books where lower(author) like '%{search.lower()}%'").fetchall()
            if len(result) == 0:
                return render_template("error.html", message="No books matching with your query found!", way='search')
            else:
                return render_template("result.html", result=result)

        elif selection == "Year":
            if search.isnumeric() is False:
                return render_template("error.html", message='Invalid Search Query. Please Use Digits Only',
                                       way='search')
            result = db.execute(f"SELECT * from books where year=:year",{"year":search}).fetchall()
            if len(search) != 4:
                return render_template("error.html", message="Please Enter a Valid Year!", way='search')
            if len(result) == 0:
                return render_template("error.html", message="No books matching with your query Found!", way='search')
            else:
                return render_template("result.html", result=result)
    else:
        return render_template("search.html")


@app.route("/search/<string:title>", methods=["POST","GET"])
def book(title):
    bookOne = db.execute("SELECT * from books where title=:title", {"title":title}).fetchone()
    print(bookOne.isbn)
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": 'PTFEUxIqbb8YwBZAfiqIkQ', "isbns": str(bookOne.isbn)})
    print(res.status_code)
    if res.status_code == 404:
        raise Exception("ERROR: API request unsuccesful!")
    data = res.json()
    average = data['books'][0]['average_rating']
    count = data['books'][0]['work_ratings_count']
    if bookOne is None:
        return render_template("error.html", message="No Information about the book found!", way='search')
    else:
        if request.method == "GET":
            review = db.execute("SELECT * from reviews where book = :book", {"book":title}).fetchall()
            #print(review)
            return render_template("book.html", bookOne=bookOne, review=review, average=average, count=count)

        else:
            user = session.get('username')
            rate = request.form.get("rating")
            rev = request.form.get("review")
            review = db.execute("SELECT * from reviews where username = :username and book = :book", {"username":user,"book":title}).fetchone()
            if review is None:
                if rate == '':
                    flash("Please Rate the Book!")
                    return redirect(url_for('book'))
                else:
                    db.execute("INSERT into reviews (book,username,rating,review) VALUES (:book, :username,:rating, :review)",
                                {"book":title, "username":user, "rating":rate,"review":rev})
                    db.commit()
                    flash("Review Submitted Successfully!")
                    all = db.execute("SELECT * from reviews where book = :book", {"book":title}).fetchall()
                    return render_template("book.html", review=all, bookOne=bookOne)
            else:
                flash("You Cannot Submit More than One review for a book!")
                all = db.execute("SELECT * from reviews where book = :book", {"book":title}).fetchall()
                return render_template("book.html", bookOne=bookOne, review=all)



@app.route("/logged")
def logged():
    session.clear()
    return render_template("login.html")


if __name__ == "__main__":
    app.run()
