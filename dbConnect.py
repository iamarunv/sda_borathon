import mysql.connector

class DBConnector():

    def __init__(self):
        self._DB_HOST='pt-neo.eng.vmware.com'
        self._DB_DATABASE='borathon'
        self._DB_USER='sqladmin'
        self._DB_PASS='lampsql'

    def mysql_connect(self):
        try:
            self._connection = mysql.connector.connect(user=self._DB_USER,
             password=self._DB_PASS, host=self._DB_HOST, database=self._DB_DATABASE)
            return self._connection
        except Error as e:
            print(e)

    def mysql_connection_shutdown(self):
        self._connection.close()

    def get_cpu_features(self):
        #returns features as list of lists.
        qry = 'select vm_id_map, timestamp, cpu_usage_percent, admin_historic_decision_cpu from sda_usage_data'
        connection = self.mysql_connect()
        cursor = connection.cursor()
        cursor.execute(qry)
        rows = cursor.fetchall()
        rows=[list(row) for row in rows]
        self.mysql_connection_shutdown()
        return rows

if __name__ == '__main__':
    db_connector = DBConnector()
    db_connector.get_cpu_features()
