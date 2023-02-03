
from quart import redirect, url_for
from quart_auth import Unauthorized

from app.errors import bp


@bp.errorhandler(Unauthorized)
async def redirect_to_login(*_: Exception):
    return redirect(url_for('auth.login'))

