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

    def mysql_run_qry_fetchall(self, qry):
        connection = self.mysql_connect()
        cursor = connection.cursor()
        cursor.execute(qry)
        rows = cursor.fetchall()
        self.mysql_connection_shutdown()
        return rows

    def get_cpu_features(self):
        #returns features as list of lists.
        qry = 'select vm_id_map, timestamp, cpu_usage_percent, admin_historic_decision_cpu from sda_usage_data'
        rows = self.mysql_run_qry_fetchall(qry)
        rows=[list(row) for row in rows]
        return rows

    def get_vm_current_state(self, vm_id_map):
        qry='select vm_name, num_cpu, memory_gb, disk_gb, operating_system, SECURE_DATA from sda_vm_state where vm_id=%d' %(vm_id_map)
        rows = self.mysql_run_qry_fetchall(qry)
        vm_state = {'vm_name': rows[0][0], 'num_cpu': rows[0][1], 'memory_gb': rows[0][2],
                    'disk_gb': rows[0][3], 'operating_system': rows[0][4], 'SECURE_DATA': rows[0][5]}
        return vm_state

    def get_distinct_resource(self, resource_name, cloud_name, operating_system, resource_limit=''):
        qry = 'select distinct %s from sda_cloud_cost where cloud_name=\'%s\' and operating_system=\'%s\'' %(resource_name, cloud_name, operating_system)
        if resource_limit:
            qry+='and %s' %(resource_limit)
        #if resource_name=='disk_size_gb':
            #print 'qry_disk', qry
        rows = self.mysql_run_qry_fetchall(qry)
        distinct_resource = [list(row)[0] for row in rows]
        return distinct_resource

    def get_instance_amortized_cost_and_cloud_label(self, rec):
        cloud=rec[0]
        cpu=rec[1]
        memory=rec[2]
        disk=rec[3]
        operating_system=rec[4]
        qry='select cost_dollar_hour, label from sda_cloud_cost where cloud_name=\'%s\' and operating_system=\'%s\' and cpu=%f and memory_gb=%f' %(cloud, operating_system, cpu, memory)
        if cloud!='Amazon':
            qry+=' and disk_size_gb=%f' %(disk)
        #print qry
        rows = self.mysql_run_qry_fetchall(qry)
        instance_costs = [list(row) for row in rows]
        #print 'instance_costs', instance_costs
        min_cost=0
        if len(instance_costs)>1:
            i=0
            for cost in instance_costs:
                if instance_costs[min_cost][0]>cost[0]:
                    min_cost=i
                i=i+1
        if instance_costs:
            return instance_costs[min_cost]

    def get_vm_name(self, vim_id):
        qry='select vm_name from sda_vm_state where vm_id=%s' %(vim_id)
        rows = self.mysql_run_qry_fetchall(qry)
        rows=[list(row)[0] for row in rows]
        return rows[0]

    def get_instance_specs(self, instance):
        instance = instance.split(' ', 1)
        qry = 'select cpu, memory_gb, disk_size_gb from sda_cloud_cost where cloud_name=\'%s\' and label=\'%s\'' %(instance[0], instance[1])
        rows = self.mysql_run_qry_fetchall(qry)
        return rows[0][0], rows[0][1], rows[0][2] 



if __name__ == '__main__':
    db_connector = DBConnector()
