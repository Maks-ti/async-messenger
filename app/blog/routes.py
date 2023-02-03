
from quart import render_template

from app.blog import bp


@bp.route('/')
@bp.route('/index')
async def index():
    posts = Post.get_followed_posts(current_user.id)
    if posts is None:
        posts = []
    return await render_template('index.html', title='Home', posts=posts)
