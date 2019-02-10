import asyncio
import re
import threading
import aiohttp
import aiopg
from flask import Flask, jsonify, request

app = Flask(__name__)

db_params = """
    dbname = 'ipport'
    user = 'user'
    password = 'password'
    host = 'localhost'
"""


@app.route('/')
def home_page():
    """
    this function handles requests to the home page
    :return: json response
    """
    message = {
        'status': 200,
        'message': 'Welcome to IpPortAPI!',
        'sample request 1': 'http://127.0.0.1:5000/get_by/127.0.0.1',
        'sample request 2': 'http://127.0.0.1:5000/get_by/172.217.21.142/80',
        'sample request 3': 'http://127.0.0.1:5000/add_entity/127.0.0.4/123/true',
    }
    resp = jsonify(message)

    return resp


@app.errorhandler(404)
def page_not_found(error):
    """
    this function handles non-existing addresses
    :param error: code of error
    :return: json response
    """
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)

    return resp


@app.errorhandler(400)
def bad_request(error):
    """
    this function handles invalid requests.
    :param error: code of error
    :return: json response
    """
    message = {
        'status': 400,
        'message': 'Bad Request: ' + request.url,
    }
    resp = jsonify(message)

    return resp


@app.route('/get_by/<string:ip>', methods=['GET'])
@app.route('/get_by/<string:ip>/<string:port>', methods=['GET'])
def get_by_ip_or_port(ip: str, port=None):
    """
    this function handles requests for ip or for ip and port
    :param ip: ip user specified
    :param port: port user specified
    :return: json response
    """

    async def select(port) -> list:
        """
        this function collects all data from a database into a list
        :return: list with all records
        """
        async with aiopg.create_pool(db_params) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    colnames = ['available', 'ip', 'port']
                    records = []
                    # case if user specified port
                    if port:
                        await cur.execute("SELECT available, ip, port \
                                           FROM services \
                                           WHERE ip='{}' AND port={}"
                                          .format(ip, port))

                        async for row in cur:
                            records.append(dict(zip(colnames, row)))
                    # case if not
                    else:
                        await cur.execute("SELECT available, ip, port \
                                           FROM services \
                                           WHERE ip='{}'"
                                          .format(ip))
                        async for row in cur:
                            records.append(dict(zip(colnames, row)))

        return records

    check_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)

    if not check_ip:
        return bad_request(400)

    if port:
        try:
            port = int(port)
            if port < 0:
                return bad_request(400)
        except ValueError:
            return bad_request(400)

    loop = asyncio.new_event_loop()
    records = loop.run_until_complete(select(port))

    if records:
        message = {
            'status': 200,
            'message': records
        }
        resp = jsonify(message)

        return resp
    else:
        return page_not_found(404)


@app.route('/add_entity/<string:ip>/<int:port>/<string:available>', methods=['GET'])
def add_entity(ip: str, port: int, available: str):
    async def insert_to_db(new_entity: tuple):
        """
        this function inserts new entity into the database
        :param updated_records: new entity from user
        """
        async with aiopg.create_pool(db_params) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    insert_query = 'INSERT INTO services (ip, port, available) VALUES (%s,%s,%s)'
                    await cur.execute(insert_query, new_entity)

    check_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)

    if not check_ip:
        return bad_request(400)

    if available.lower() == 'true':
        available = True
    else:
        available = False

    loop = asyncio.new_event_loop()
    loop.run_until_complete(insert_to_db(tuple((ip, port, available))))

    message = {
        'status': 200,
        'message': 'new entity added!'
    }
    resp = jsonify(message)

    return resp


def update_state_of_service():
    """
    this is an ensemble function that is responsible for updating the database
    """

    async def select_from_db() -> list:
        """
        this function pulls all the data from the database
        :return: list with all records from db
        """
        async with aiopg.create_pool(db_params) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT id, ip, port, available FROM services")
                    records = []
                    async for row in cur:
                        records.append(row)
        return records

    async def check_status_url(records: list) -> list:
        """
        this function checks the ip and port of each entry for existence
        :param records: list with all records from db
        :return: updated list of records
        """
        updated_records = []
        for record in records:
            url = 'http://' + record[1] + ':' + str(record[2])  # ip:port
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url):
                        updated_records.append(tuple((record[0], record[1], record[2], True)))
            except aiohttp.ClientConnectionError:
                updated_records.append(tuple((record[0], record[1], record[2], False)))
        return updated_records

    async def insert_to_db(updated_records: list) -> None:
        """
        this function inserts updated data into the database
        :param updated_records: records that have been tested
        """
        async with aiopg.create_pool(db_params) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute('DELETE FROM services')
                    records_list_template = ','.join(['%s'] * len(updated_records))
                    insert_query = 'INSERT INTO services VALUES {}'.format(records_list_template)
                    await cur.execute(insert_query, updated_records)

    threading.Timer(30, update_state_of_service).start()  # runs every 30 seconds

    loop = asyncio.new_event_loop()
    records = loop.run_until_complete(select_from_db())
    updated_records = loop.run_until_complete(check_status_url(records))
    loop.run_until_complete(insert_to_db(updated_records))


if __name__ == '__main__':
    update_state_of_service()

    app.run(debug=True, use_reloader=False)
