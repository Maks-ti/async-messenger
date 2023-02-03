from datetime import datetime

import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool

from quart_auth import AuthUser

from app import bcrypt as bc
from app import app


class _DataBase(object):
    _db_name = app.config['DB_NAME']
    _db_user = app.config['DB_USER']
    _user_password = app.config['USER_PASSWORD']
    _db_host = app.config['DB_HOST']
    _db_port = app.config['DB_PORT']
    _pool: Pool | None = None

    @classmethod
    async def _create_pool(cls):
        dsn: str = f"postgres://{cls._db_user}:{cls._user_password}@{cls._db_host}:{cls._db_port}/{cls._db_name}"
        try:
            cls._pool: Pool = await asyncpg.create_pool(dsn)
        except BaseException as ex:
            print(ex)

    @classmethod
    async def execute_query(cls, query: str, *args,
                            execute: bool = False,
                            fetch: bool = False,
                            fetchrow: bool = False,
                            fetchval: bool = False):
        if cls._pool is None:
            await cls._create_pool()
        async with cls._pool.acquire() as con:
            con: Connection
            async with con.transaction():
                if execute:
                    result = await con.execute(query, *args)
                elif fetch:
                    result = await con.fetch(query, *args)
                elif fetchrow:
                    result = await con.fetchrow(query, *args)
                elif fetchval:
                    result = await con.fetchval(query, *args)
        return result


class User(AuthUser):
    def __init__(self, id: int = 0, login: str = '',
                 password_hash: str = '', name: str = ''):
        super().__init__(id)
        self.id = id
        self.login = login
        self.password_hash = password_hash
        self.name = name

    def __repr__(self):
        return f'<User {self.login}>'

    def __str__(self):
        string = f'{self.name}:' + '\r\n' + f'{self.login}'
        return string

    def set_password(self, password: str):
        self.password_hash = bc.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str):
        return bc.check_password_hash(self.password_hash, password)

    def tup(self) -> tuple:
        return (self.login,
                self.password_hash,
                self.name,)

    @classmethod
    async def add(cls, user):
        query = '''
        INSERT INTO users (login, password_hash, name)
        VALUES ($1, $2, $3)'''
        return await _DataBase.execute_query(query, *user.tup(), execute=True)

    @classmethod
    async def get_by_login(cls, login: str):
        query = '''
        SELECT * FROM users
        WHERE login = $1'''
        res = await _DataBase.execute_query(query, login, fetchrow=True)
        if res is None:
            return None
        return User(*res)

    @classmethod
    async def get_by_id(cls, user_id: int):
        query = '''
        SELECT  * FROM users
        WHERE id = $1'''
        res = await _DataBase.execute_query(query, user_id, fetchrow=True)
        if res is None:
            return None
        return User(*res)

    @classmethod
    async def search_by_word(cls, key_word: str) -> list | None:
        query = '''
        SELECT * FROM users
        WHERE name LIKE %$1% OR
        login LIKE %$2%'''
        res = await _DataBase.execute_query(query, key_word, key_word, fetch=True)
        if res is None or len(res) == 0:
            return None
        res = list(map(lambda x: User(*x), res))
        return res


class Profile(object):
    '''
    класс описывающий профиль пользователя
    '''

    def __init__(self,
                 id: int,
                 profile_img: str | None = None,
                 biography: str = '',
                 about: str = ''):
        self.id = id
        self.profile_img = profile_img
        self.biography = biography
        self.about = about

    def tup(self) -> tuple:
        return (self.id,
                self.profile_img,
                self.biography,
                self.about,)

    def avatar(self) -> str:
        if self.profile_img == '' or self.profile_img is None:
            return None
        return self.profile_img

    @classmethod
    async def add(cls, profile):
        query = '''
        INSERT INTO profile_info (id, profile_img, biography, about)
        VALUES ($1, $2, $3, $4)'''
        return await _DataBase.execute_query(query, *profile.tup(), execute=True)

    @classmethod
    async def get_by_id(cls, user_id: int):
        query = '''
        SELECT * FROM profile_info
        WHERE id = $1'''
        res = await _DataBase.execute_query(query, user_id, fetchrow=True)
        if res is None:
            return None
        return Profile(*res)

    @classmethod
    async def update(cls, new_profile):
        profile = cls.get_by_id(new_profile.id)
        if profile is None:
            return await cls.add(new_profile)
        query = ''' UPDATE profile_info 
        SET profile_img = $1,
        biography = $2,
        about = $3,
        WHERE id = $4'''
        return await _DataBase.execute_query(query, new_profile.profile_img, new_profile.biography,
                                             new_profile.about, new_profile.id, execute=True)


class Follows(object):
    @classmethod
    async def add(cls, follower_id: int, followed_id: int):
        query = ''' INSERT INTO follows (follower_id, followed_id)
        VALUES ($1, $2)'''
        return await _DataBase.execute_query(query, follower_id, followed_id, execute=True)

    @classmethod
    async def delete(cls, follower_id: int, followed_id: int) -> bool:
        query = ''' DELETE FROM follows
            WHERE follower_id = $1
            AND followed_id = $2 '''
        return await _DataBase.execute_query(query, follower_id, followed_id, execute=True)

    @classmethod
    async def is_following(cls, follower_id, followed_id) -> bool:
        query = ''' SELECT COUNT(*) FROM follows
            WHERE follower_id = $1
            AND followed_id = $2 '''
        res = await _DataBase.execute_query(query, follower_id, followed_id, fetchval=True)
        if res is None or res == 0:
            return False
        return True

    @classmethod
    async def get_followers(cls, user_id: int) -> list[User] | None:
        ''' получаем подписчиков user(user_id) '''
        query = ''' SELECT * FROM follows
            WHERE followed_id = $1 '''
        res = await _DataBase.execute_query(query, user_id, fetch=True)
        if res is None or len(res) == 0:
            return None
        res = list(map(lambda x: await User.get_by_id(x[0]), res))
        return res

    @classmethod
    async def get_followings(cls, user_id: int) -> list[User] | None:
        ''' получаем подписки user(user_id) '''
        query = ''' SELECT * FROM follows
                    WHERE follower_id = $1 '''
        res = await _DataBase.execute_query(query, user_id, fetch=True)
        if res is None or len(res) == 0:
            return None
        res = list(map(lambda x: await User.get_by_id(x[1]), res))
        return res


class Chat(object):
    '''
    класс описывающий сущность чата
    '''

    def __init__(self,
                 id: int = 0,
                 name: str = '',
                 counter: int = 0,
                 image: str | None = None):
        self.id = id
        self.name = name
        self.counter = counter
        self.image = image

    def tup(self) -> tuple:
        return (self.name,
                self.counter,
                self.image,)

    @classmethod
    async def add(cls, chat):
        query = ''' INSERT INTO chat (name, counter, image)
        VALUES  ($1, $2, $3)
        RETURNING id '''
        return await _DataBase.execute_query(query, chat.name, chat.counter, chat.image, fetchval=True)

    @classmethod
    async def get_by_id(cls, chat_id: int):
        query = ''' SELECT * FROM chat
        WHERE id = $1'''
        res = await _DataBase.execute_query(query, chat_id, fetchrow=True)
        if res is None:
            return None
        return Chat(*res)


class User_in_chat(object):
    @classmethod
    async def add(cls, user_id: int, chat_id: int):
        query = ''' INSERT INTO user_in_chat (user_id, chat_id)
        VALUES ($1, $2)'''
        return await _DataBase.execute_query(query, user_id, chat_id, execute=True)

    @classmethod
    async def delete(cls, user_id: int, chat_id: int):
        pass
        pass
        pass


class Message(object):
    '''
    класс описывающий сообщение
    '''

    def __init__(self,
                 id: int = 0,
                 chat_id: int = 0,
                 user_id: int = 0,
                 parent_id: Union[int, None] = None,
                 mes_text: str = '',
                 sends_time: datetime = datetime.now()):
        self.id = id
        self.chat_id = chat_id
        self.user_id = user_id
        self.parent_id = parent_id
        self.mes_text = mes_text
        self.sends_time = sends_time
        # поле не относящееся к бд
        # необходимо для формирования дерева сообщений (если оно формируется)
        self.child_list = []
        # глубина сообщения в дереве
        self.depth = 0
        # автор сообщения
        self.author: User = User.get_by_id(self.user_id)

    def tup(self) -> tuple:
        return (self.chat_id,
                self.user_id,
                self.parent_id,
                self.mes_text,
                self.sends_time,)

    def __repr__(self):
        return f'<Message {self.id}>'


class Post(object):
    '''
    класс описывает пост
    '''

    def __init__(self,
                 id: int = 0,
                 user_id: int = 0,
                 title: str = '',
                 publication_date: datetime = datetime.now(),
                 last_edit_date: Union[datetime, None] = None,
                 post_text: str = '',
                 image: str = ''):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.publication_date = publication_date
        self.last_edit_date = last_edit_date
        self.post_text = post_text
        self.image = image
        # автор поста User (данные о нём непосредственно в запросе не получаются)
        self.author: User = User.get_by_id(user_id)
        # коменты опять же получаем отдельно
        self.comments = None

    def tup(self) -> tuple:
        last_edit_date: Union[str, None]
        if self.last_edit_date is None:
            last_edit_date = None
        else:
            last_edit_date = str(self.last_edit_date)
        return (self.user_id,
                self.title,
                str(self.publication_date),
                last_edit_date,
                self.post_text,
                self.image,)

    def __repr__(self):
        return f'<Post {self.title}>'


class Comment(object):
    '''
    класс описывающий коментарий к посту
    '''

    def __init__(self,
                 id: int = 0,
                 post_id: int = 0,
                 commentator_id: int = 0,
                 comment_text: str = '',
                 sends_time: datetime = datetime.now()):
        self.id = id
        self.post_id = post_id
        self.commentator_id = commentator_id
        self.comment_text = comment_text
        self.sends_time = sends_time
        # автор коммента
        self.author: User = User.get_by_id(self.commentator_id)

    def tup(self) -> tuple:
        return (self.post_id,
                self.commentator_id,
                self.comment_text,
                str(self.sends_time),)
