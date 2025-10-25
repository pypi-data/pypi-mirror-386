import mrnet4gmns as mr

net = mr.loadNetFromCSV(node_file='net_full/node.csv', link_file='net_full/link.csv')
mr.buildMultiResolutionNets(net, width_of_lane=3.50, length_of_cell=7.0, num_nodes_for_ramp_alignment=10)
mr.outputNetToCSV(net, output_folder='mrn_full')
