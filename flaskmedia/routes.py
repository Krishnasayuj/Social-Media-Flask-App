from flask import render_template, url_for, flash, abort, redirect, request
from flaskmedia import app, db, bcrypt
from flaskmedia.forms import RegistrationForm, LoginForm, Updateaccountform, PostForm
from flaskmedia.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
import secrets, os
from PIL import Image




@app.route("/")
@app.route("/home")
def home_page():

    posts=Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('welcome.html', posts=posts)


#@app.route("/about")
#def about():
#    return render_template('about.html', title='About')


@app.route("/signup", methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        #if db.session.query(User).filter_by().count()<1:
        db.session.commit()
        #else:
            #flash(f'User {form.username.data} already exist!', category='danger')
            #return redirect(url_for('register_page'))
        flash(f'Account created successfully {form.username.data}!', category='success')
        return redirect(url_for('login_page'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            flash('You have been logged in!', 'success')
            login_user(user, remember=form.remember.data)
            next_page=request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home_page'))

        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout_page():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home_page'))

def save_picture(form_picture):
    random_hex=secrets.token_hex(8)
    _ , f_ext= os.path.splitext(form_picture.filename)
    picture_fn=random_hex + f_ext
    picture_path=os.path.join(app.root_path, 'static/dp', picture_fn)
    output_size=(125,125)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


"""def save_postpic(form_postpic):
    random_hex=secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_postpic.filename)
    postpic_fn=random_hex+f_ext
    postpic_path=os.path.join(app.root_path, 'static/post_pics', postpic_fn)
    form_postpic.save(postpic_path)
    return postpic_fn"""



@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form=Updateaccountform()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('account'))
    elif request.method=='GET':

        form.username.data = current_user.username
        form.email.data = current_user.email



    image_file=url_for('static', filename='dp/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)



@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form=PostForm()
    if form.validate_on_submit():
        post=Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post uploaded', 'info')
        return redirect(url_for('home_page'))
    return render_template('post.html', title='New Post', form=form, legend='New post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('in_post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Post edited!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('post.html', title='Edit Post', form=form, legend='Edit post')



@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home_page'))


@app.route("/user/<string:username>")
def user_post(username):
    user=User.query.filter_by(username=username).first_or_404()
    posts=Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).all()
    return render_template('user_post.html', posts=posts, user=user)


