from flask import Flask, request
from flask_restx import Api, Resource
from sqlalchemy.exc import NoResultFound
from marshmallow.exceptions import ValidationError
from models import Movie, MovieSchema, Director, DirectorSchema, Genre, GenreSchema, db

# Настраиваем приложение и инициализируем в sqlalchemy
app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

# создаем объекты Schema для дальнейшей работы с сериализацией
movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)

genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)

# инициализируем приложение в restx
api = Api(app)
# создаем namespace
movie_ns = api.namespace('movies')
director_ns = api.namespace('directors')
genre_ns = api.namespace('genres')


def query_format_movie():
    """
    Формат для вывода информации из таблицы movie
    """
    query = db.session.query(Movie.id,
                             Movie.title,
                             Movie.description,
                             Movie.trailer,
                             Movie.year,
                             Movie.rating,
                             Genre.name.label('genre'),
                             Director.name.label('director')) \
        .join(Movie.director).join(Movie.genre)
    return query


@movie_ns.route('/')
class MoviesView(Resource):
    def get(self):
        try:
            # получаем director_id и genre_id
            page = request.args.get('page', type=int, default=1)
            director_id = request.args.get('director_id', type=int)
            genre_id = request.args.get('genre_id', type=int)
            # если получаем director_id и genre_id, то выполняем поиск по ним
            if director_id and genre_id:
                # получаем фильмы
                all_movies = query_format_movie().filter(Movie.director_id == director_id, Movie.genre_id == genre_id)\
                    .limit(10).offset((page - 1) * 10).all()
                # если фильмы не найдены, то выбрасываем ошибку
                if not all_movies:
                    raise ValueError("Нет фильмов с таким id режиссера и id жанра")
            # если получаем только director_id
            elif director_id:
                all_movies = query_format_movie().filter(Movie.director_id == director_id)\
                    .limit(10).offset((page - 1) * 10).all()

                if not all_movies:
                    raise ValueError("Нет фильмов с таким id режиссера")
            # если получаем только genre_id
            elif genre_id:
                all_movies = query_format_movie().filter(Movie.genre_id == genre_id).limit(10)\
                    .offset((page - 1) * 10).all()

                if not all_movies:
                    raise ValueError("Нет фильмов с таким id жанра")
            else:
                all_movies = query_format_movie().limit(10).offset((page - 1) * 10).all()
            # вывод всех фильм на сайт
            return movies_schema.dump(all_movies), 200
        except ValueError as e:
            return str(e), 404

    def post(self):
        json_data = request.json

        try:
            new_movie = Movie(**json_data)
        except TypeError:
            return "Введены неправильные данные для добавления фильма", 404

        with db.session.begin():
            db.session.add(new_movie)

        return "Новый фильм добавлен", 201


@movie_ns.route('/<int:movie_id>')
class MovieView(Resource):
    def get(self, movie_id):
        """
        Получаем фильм по его id
        """
        # получаем объект movie, если его нет обрабатываем ошибку
        try:
            movie = query_format_movie().filter(Movie.id == movie_id).one()
            return movie_schema.dump(movie)
        except NoResultFound:
            return "Фильм с таким id не найден", 404

    def put(self, movie_id):
        """
        Изменяем данные фильма с полученным id
        """
        try:
            # получаем данные из запроса и прогоняем их через схему, для проверки
            json_data = movie_schema.load(request.json)
            # проверяем есть ли объект который мы хотим изменить
            db.session.query(Movie).filter(Movie.id == movie_id).one()
        except ValidationError:
            return 'Введены неправильные данные для изменения', 404
        except NoResultFound:
            return "Фильм не найден", 404
        # обновляем данные
        db.session.query(Movie).filter(Movie.id == movie_id).update(json_data)
        db.session.commit()
        return f"Данные у фильма с id-{movie_id} изменены", 200

    def delete(self, movie_id):
        try:
            # проверяем есть ли объект который мы хотим изменить
            movie_del = db.session.query(Movie).filter(Movie.id == movie_id).one()
        except NoResultFound:
            return "Фильм не найден", 404
        # удаляем данные
        db.session.delete(movie_del)
        db.session.commit()
        return "", 200


@director_ns.route('/')
class DirectorsView(Resource):
    def post(self):
        json_data = request.json

        try:
            new_director = Director(**json_data)
        except TypeError:
            return "Введены неправильные данные для добавления нового директора", 404

        with db.session.begin():
            db.session.add(new_director)

        return "Новый директор добавлен", 201


@director_ns.route('/<int:director_id>')
class DirectorView(Resource):
    def put(self, director_id):
        try:
            json_data = director_schema.load(request.json)
            db.session.query(Director).filter(Director.id == director_id).one()
        except ValidationError:
            return 'Введены неправильные данные для изменения', 404
        except NoResultFound:
            return "Такого директора нет", 404

        db.session.query(Director).filter(Director.id == director_id).update(json_data)
        db.session.commit()
        return f"Данные у директора с id-{director_id} изменены", 200

    def delete(self, director_id):
        try:
            director_del = db.session.query(Director).filter(Director.id == director_id).one()
        except NoResultFound:
            return "Такого директора нет", 404

        db.session.delete(director_del)
        db.session.commit()
        return "", 200


@genre_ns.route('/')
class GenresView(Resource):
    def post(self):
        json_data = request.json

        try:
            new_genre = Genre(**json_data)
        except TypeError:
            return "Введены неправильные данные для добавления жанра", 404

        with db.session.begin():
            db.session.add(new_genre)

        return "Новый жанр добавлен", 201


@genre_ns.route('/<int:genre_id>')
class GenreView(Resource):
    def put(self, genre_id):
        try:
            json_data = genre_schema.load(request.json)
            db.session.query(Genre).filter(Genre.id == genre_id).one()
        except ValidationError:
            return 'Введены неправильные данные для изменения', 404
        except NoResultFound:
            return "Такого жанра нет", 404

        db.session.query(Genre).filter(Genre.id == genre_id).update(json_data)
        db.session.commit()
        return f"Данные у жанра с id-{genre_id} изменены", 200

    def delete(self, genre_id):
        try:
            genre_del = db.session.query(Genre).filter(Genre.id == genre_id).one()
        except NoResultFound:
            return "Такого жанра нет", 404

        db.session.delete(genre_del)
        db.session.commit()
        return "", 200


if __name__ == '__main__':
    app.run(debug=True)
