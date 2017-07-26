import cloudOptimizer
import dbConnect
import decisionTrees

if __name__=='__main__':
    print "\n===============Running Self-Driving Admin for Hybrid Cloud=============\n"
    for i in range(1,5):
        copt=cloudOptimizer.CloudOptimizer(i)
        print copt.generate_recommendations()
