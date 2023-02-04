
from quart import render_template
from quart_auth import current_user

from app.blog import bp
from app.models import Post


@bp.route('/')
@bp.route('/index')
async def index():
    posts = Post.get_followed_posts(current_user.id)
    if posts is None:
        posts = []
    return await render_template('index.html', title='Home', posts=posts)
