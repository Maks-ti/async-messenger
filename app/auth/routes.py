
from quart import render_template, flash, redirect, url_for, request
from quart_auth import login_user, current_user, logout_user

from werkzeug.urls import url_parse

from app.models import User

from .forms import LoginForm, RegistrationForm

# import auth blueprint
from app.auth import bp


@bp.route('/login', methods=['GET', 'POST'])
async def login():
    if await current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = await LoginForm.create_form()
    if await form.validate_on_submit():
        print('form VALIDATE')
        user = await User.get_by_login(form.login.data)
        if user is None or not user.check_password(form.password.data):
            await flash('Invalid login or password')
            return redirect(url_for('auth.login'))
        # логиним пользоватаеля в системе самого quart
        login_user(user, remember=form.remember_me.data)
        # page for redirect
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('blog.index')
        return redirect(next_page)
    return await render_template('login.html', title='login', form=form)


@bp.route('/logout')
async def logout():
    logout_user()
    return redirect(url_for('blog.index'))


@bp.route('/register', methods=['GET', 'POST'])
async def register():
    if await current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = await RegistrationForm.create_form()
    if await form.validate_on_submit():
        user = User(login=form.login.data, name=form.name.data)
        user.set_password(form.password.data)
        # add new user in database
        await User.add(user)
        await flash('you are registered!')
        return redirect(url_for('auth.login'))
    return await render_template('register.html', title='register', form=form)

