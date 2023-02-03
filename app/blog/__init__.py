
from quart import Blueprint

bp = Blueprint('blog', __name__, template_folder='templates')

from app.blog import routes
