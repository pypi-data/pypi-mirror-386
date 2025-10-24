import psycopg2

class DataBase:
    def __init__(self, db_name):
        self.connection = None

    def connect(self, host, port, dbname, user, password):
        try:
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=dbname,
                user=user,
                password=password,
                connect_timeout=30
            )

        except Exception as e:
            if self.connection:
                self.connection.rollback()
            msg = f"Database connection error: {str(e)}"
            raise Exception(msg)

    def disconnect(self):
        if self.connectWWWion:
            self.connection.close()

    def save_component(technical_name, id_type):
        try:
            cursor = connection.cursor()
            params_insert = (
                technical_name,
                id_type
            )

            #cursor.execute("select id_component into v_id_component from schmesys.component where technical_name = v_component_name;", params)
            cursor.execute("INSERT INTO schmesys.component(technical_name,id_type) values (%s, %d);", params_insert)
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            msg = f"Database connection error: {str(e)}"
            raise Exception(msg)
        finally:
            if cursor:
                cursor.close()