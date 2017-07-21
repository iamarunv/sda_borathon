import bisect
import decisionTrees
import dbConnect
import slackOps

class CloudOptimizer():

    def __init__(self, vm_id_map):
        self._vm_id_map = vm_id_map
        self._prediction_table_vm = decisionTrees.get_switch_table(self._vm_id_map)
        #print self._prediction_table_vm
        #self._prediction_table_vm = [5, 1, 1, 1, 1]
        self._db_connect = dbConnect.DBConnector()
        self._current_state = self._db_connect.get_vm_current_state(self._vm_id_map)

    def generate_recommendations(self):
        pred_time=[]
        for pred in self._prediction_table_vm:
            if pred[1] in pred_time:
                continue
            else:
                pred_time.append(pred[1])
                self._change_orders = {'cpu_change': pred[2],
                                 'memory_change': pred[3],
                                 'disk_change': pred[4]}
                if self._current_state["SECURE_DATA"] == 0:
                    print "\nAnalyzing a possible move..."
                    amazon_rec = self.generate_possible_options('Amazon')
                    azure_rec = self.generate_possible_options('Azure')
                    amazon_rec[3]=azure_rec[3]
                    avail_recs=[amazon_rec, azure_rec]
                    rec_instance = self.get_cost_optimized_rec(avail_recs)
                    if rec_instance:
                        print "\nPushing Recommendation to Slack for Admin approval...\n"
                        self.send_rec_over_slack(pred[1], rec_instance)
                        return 'vm_id', self._vm_id_map, 'time', pred[1], rec_instance
                    else:
                        print "\nRejected move to Public Cloud because of SECURITY constraint...\n"
        #self.generate_possible_option_onprem('OnPrem')

    def send_rec_over_slack(self, time, rec_instance):
        vm_name=self._db_connect.get_vm_name(self._vm_id_map)
        cpu, memory, disk = self._db_connect.get_instance_specs(rec_instance)
        if not disk:
            disk = 'EBS'
        message = 'We recommend you move %s to %s with vCPU: %s, Memory: %s (GiB), Disk: %s (GB) at %s:00 hours.' %(vm_name, rec_instance, cpu, memory, disk, int(time))
        slackOps.promptRec(0, message)

    def get_cost_optimized_rec(self, avail_recs):
        instance_amortized_cost = {}
        instance_amortized_cost_30day={}
        for rec in avail_recs:
            instance_amortized_cost[rec[0]] = self._db_connect.get_instance_amortized_cost_and_cloud_label(rec)
        for cloud, instance in instance_amortized_cost.iteritems():
            if instance:
                cloud_instance=cloud+' '+instance[1]
                instance_amortized_cost_30day[cloud_instance] = instance[0]*30*24
                if cloud == 'Amazon':
                    instance_amortized_cost_30day[cloud_instance]+=rec[3]*0.0045
                return min(instance_amortized_cost_30day, key=instance_amortized_cost_30day.get)

    def generate_possible_options(self, cloud):
        recommended_cpu = self._current_state['num_cpu']
        recommended_memory = self._current_state['memory_gb']
        recommended_disk = self._current_state['disk_gb']
        #CPU Options
        if self._change_orders['cpu_change']!=0:
            distinct_cpu = self._db_connect.get_distinct_resource('cpu', cloud, self._current_state['operating_system'])
            distinct_cpu.sort()
            if self._change_orders['cpu_change']>0:
                if len(distinct_cpu)==1:
                    recommended_cpu=distinct_cpu[0]
                else:
                    recommended_cpu = self.bump_genie(distinct_cpu, 'cpu_change', recommended_cpu)
            else:
                if len(distinct_cpu)==1:
                    recommended_cpu=distinct_cpu[0]
                else:
                    recommended_cpu = self.drop_genie(distinct_cpu, 'cpu_change', recommended_cpu)
        #Memory Options
        distinct_memory = self._db_connect.get_distinct_resource('memory_gb', cloud, self._current_state['operating_system'], 'cpu=%s' %(recommended_cpu))
        if self._change_orders['memory_change']>0:
            if len(distinct_memory)==1:
                recommended_memory=distinct_memory[0]
            else:
                recommended_memory = self.bump_genie(distinct_memory, 'memory_change', recommended_memory)
        else:
            if len(distinct_memory)==1:
                recommended_memory=distinct_memory[0]
            else:
                recommended_memory = self.drop_genie(distinct_memory, 'memory_change', recommended_memory)
        #Storage Options
        if cloud!='Amazon':
            distinct_disk = self._db_connect.get_distinct_resource('disk_size_gb', cloud, self._current_state['operating_system'], 'cpu=%s and memory_gb=%s' %(recommended_cpu, recommended_memory))
            #print 'distinct_disk', distinct_disk
            if self._change_orders['disk_change']>0:
                if len(distinct_disk)==1:
                    recommended_disk=distinct_disk[0]
                else:
                    recommended_disk = self.bump_genie(distinct_disk, 'disk_change', recommended_disk)
            else:
                if len(distinct_disk)==1:
                    recommended_disk=distinct_disk[0]
                else:
                    recommended_disk = self.drop_genie(distinct_disk, 'disk_change', recommended_disk)
        else:
            recommended_disk = 0
        return [cloud, recommended_cpu, recommended_memory, recommended_disk, self._current_state['operating_system']]



    def bump_genie(self, distict_list, resource, recommended_rec):
        distinct_sublist=distict_list
        for i in range(1, int(self._change_orders[resource])+1):
            distinct_sublist = [j for j in distinct_sublist if j>recommended_rec]
            if distinct_sublist:
                recommended_rec = distinct_sublist[0]
            else:
                break
        return recommended_rec

    def drop_genie(self, distict_list, resource, recommended_rec):
        distinct_sublist=distict_list
        for i in range(-1, int(self._change_orders[resource])-1, -1):
            distinct_sublist = [j for j in distinct_sublist if j<recommended_rec]
            if distinct_sublist:
                recommended_rec = distinct_sublist[-1]
            else:
                break
        return recommended_rec


if __name__=='__main__':
    copt=CloudOptimizer(5)
    copt.generate_recommendations()
