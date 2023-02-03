
from quart import Quart

# создание экземпляра приложения
app = Quart(__name__)

# загрузка конфигурации
from config import Config
app.config.from_object(Config)

# password hashing
from quart_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

# auth
from app import models
from quart_auth import AuthManager
auth_manager = AuthManager()
auth_manager.user_class = models.User

auth_manager.init_app(app)

''' # bootstrap
from flask_bootstrap import Bootstrap
bootstrap = Bootstrap()
bootstrap.init_app(app) '''

# register blueprints
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from app.auth import bp as auth_bp
app.register_blueprint(auth_bp)

from app.blog import bp as blog_bp
app.register_blueprint(blog_bp)


'''
cd PycharmProjects/quart_chat
venv\Scripts\activate
set QUART_DEBUG=1
quart run
'''

'''
chcp 1251
PATH C:\Program Files\PostgreSQL\14\bin;%PATH%
psql -h localhost -p 5432 -d messenger -U maxti
'''

if __name__ == '__main__':
    app.run(debug=True)
