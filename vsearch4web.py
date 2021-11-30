"""Веб-приложение ждет от пользователя ввода букв и слова, в котором будет выполняться поиск введенных букв.
Далее на другой странице выдает результаты. Также записывает историю введенных данных в MySQL. Имеется проверка 
состояния сессии и страница для вывода истории из базы данных."""
from flask import Flask, render_template, request, session 
# Импорт собственной простейшей функции по поиску букв в слове
from vsearch import search4letters as s4l  
# То же самое только с русскими буквами 
from vsearch import search4letters_rus as s4l_rus 
from DBcm import UseDatabase, ConnectionError, CredentialsError, SQLError
from checker import check_logged_in
from time import sleep
from threading import Thread
from flask import copy_current_request_context

app = Flask(__name__) 

# Задаю пароль для возможности проверки состояния сессии 
app.secret_key = 'nopass' 

# Данные для доступа в MySQL 
app.config['dbconfig'] = {'host': '127.0.0.1',
                          'user': '',
                          'password': '',
                          'database': 'vsearchlogDB',} 

# Переходим сюда по нажатию кнопки Do it
@app.route('/search4', methods = ['POST']) 
def do_search() -> 'html':
    # Декоратор для сохранения переменных функции во время выполнения потока
    @copy_current_request_context  
    def log_request(req: 'flask_request', res: str) -> None:
        '''Журналирует веб-запрос и возвращаемые результаты'''
        # Ждем для выполнения потока на фоне 
        sleep(15)
        # Собственный диспетчер контекста 
        # Записываю данные в базу 
        with UseDatabase(app.config['dbconfig']) as cursor: 
            _SQL = '''insert into log
                    (phrase, letters, ip, browser_string, results)
                    values
                    (%s, %s, %s, %s, %s)''' 
            cursor.execute(_SQL, (req.form['phrase'],
                                req.form['letters'],
                                req.remote_addr,
                                req.user_agent.browser,
                                res,))
    # Принимаю введенные данные
    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results'
    results = str(s4l(phrase, letters))
    # Запускаю поток
    try:
        t = Thread(target=log_request, args=(request, results))
        t.start()
    except Exception as err:
        print('***** Logging failed with this error: ', str(err))
    if results == 'set()':
        results = 'There are no this letters'
    return render_template('results.html', 
                            the_phrase = phrase, 
                            the_letters = letters, 
                            the_title = title, 
                            the_results = results)

# Русская версия
@app.route('/search4_rus', methods = ['POST'])
def do_search_rus() -> 'html':
    @copy_current_request_context  
    def log_request(req: 'flask_request', res: str) -> None:
        '''Журналирует веб-запрос и возвращаемые результаты'''
        sleep(15)
        with UseDatabase(app.config['dbconfig']) as cursor: 
            _SQL = '''insert into log
                    (phrase, letters, ip, browser_string, results)
                    values
                    (%s, %s, %s, %s, %s)''' 
            cursor.execute(_SQL, (req.form['phrase'],
                                req.form['letters'],
                                req.remote_addr,
                                req.user_agent.browser,
                                res,))
    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Вот ваши результаты:'
    results = str(s4l_rus(phrase, letters))
    try:
        t = Thread(target=log_request, args=(request, results))
        t.start
    except Exception as err:
        print('***** Logging failed with this error: ', str(err))
    if results == 'set()':
        results = 'Таких букв не найдено'
    return render_template('results_rus.html', 
                            the_phrase = phrase, 
                            the_letters = letters, 
                            the_title = title, 
                            the_results = results)

@app.route('/')
@app.route('/entry', methods = ['GET'])
def entry_page() -> 'html':
    """Отображает начальную страницу"""
    return render_template('entry.html', 
                            the_title = 'Welcome to search4letters on the web!')

@app.route('/entry_rus', methods = ['GET'])
def entry_page_rus() -> 'html':
    return render_template('entry_rus.html', 
                            the_title = 'Добро пожаловать в search4letters в сети!')

@app.route('/view_log')
# Декоратор для проверки входа 
@check_logged_in 
def view_the_log() -> 'html':
    """Возвращает страницу с историей поиска из базы данных"""
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = '''select phrase, letters, ip, browser_string, results from log'''
            cursor.execute(_SQL)
            contents = cursor.fetchall()
        titles = ('Phrase', 'Letters', 'Remote_addr', 'User_agent', 'Results')
        return render_template('viewlog.html', 
                                the_title = 'View Log', 
                                the_row_titles = titles, 
                                the_data = contents)
    except ConnectionError as err:
        print('Is your database switched on? Error: ', str(err))
    except CredentialsError as err:
        print('User-id/Password issues. Error: ', str(err))
    except SQLError as err:
        print('Is your query correct? Error: ', str(err))
    except Exception as err:
        print('Something went wrong: ', str(err))
    return 'Error'

@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in'

@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'You are now logged out'

if __name__ == '__main__':
    app.run(debug=True)

