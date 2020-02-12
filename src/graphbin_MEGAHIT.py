#!/usr/bin/python3

"""graphbin_MEGAHIT.py: Improved binning of metagenomic contigs using MEGAHIT assembly graphs.

GraphBin is a metagenomic contig binning tool that makes use of the contig 
connectivity information from the assembly graph to bin contigs. It utilizes 
the binning result of an existing binning tool and a label propagation algorithm 
to correct mis-binned contigs and predict the labels of contigs which are 
discarded due to short length.

graphbin_MEGAHIT.py makes use of the assembly graphs produced by MEGAHIT assembler.
"""

import sys
import os
import subprocess
import csv
import operator
import time
import argparse
import re

from igraph import *
from labelpropagation.labelprop import LabelProp
from bidirectionalmap.bidirectionalmap import BidirectionalMap

# Sample command
# -------------------------------------------------------------------
# python graphbin_MEGAHIT.py    --graph /path/to/graph_file.gfa
#                               --binned /path/to/binning_result.csv
#                               --output /path/to/output_folder
# -------------------------------------------------------------------

start_time = time.time()

# Setup argument parser
#-----------------------

ap = argparse.ArgumentParser()

ap.add_argument("--graph", required=True, help="path to the assembly graph file")
ap.add_argument("--binned", required=True, help="path to the .csv file with the initial binning output from an existing tool")
ap.add_argument("--output", required=False, help="path to the output folder")
ap.add_argument("--prefix", required=False, help="prefix for the output file")
ap.add_argument("--max_iteration", required=False, type=int, help="maximum number of iterations for label propagation algorithm. [default: 100]")
ap.add_argument("--diff_threshold", required=False, type=float, help="difference threshold for label propagation algorithm. [default: 0.1]")

args = vars(ap.parse_args())

assembly_graph_file = args["graph"]
contig_bins_file = args["binned"]
output_path = args["output"]
prefix = args["prefix"]
max_iteration = args["max_iteration"]
diff_threshold = args["diff_threshold"]

print("This version of GraphBin makes use of the assembly graph produced by MEGAHIT which is based on the de Bruijn graph approach.\n")

print("Assembly graph file:", assembly_graph_file)
print("Existing binning output file:", contig_bins_file)
print("Final binning output file:", output_path)
print("Maximum number of iterations:", max_iteration)
print("Difference threshold:", diff_threshold)

print("\nGraphBin started\n-----------------")


# Get the number of bins from the initial binning result
#--------------------------------------------------------

n_bins = 0

try:
    all_bins_list = []

    with open(contig_bins_file) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            all_bins_list.append(row[1])
            
    bins_list = list(set(all_bins_list))
    bins_list.sort()

    n_bins = len(bins_list)
    print("Number of bins available in initial binning result:", n_bins)
except:
    print("\nPlease make sure that the correct path to the initial binning result file is provided and it is having the correct format.")
    print("Exiting GraphBin...\nBye...!\n")
    sys.exit(2)


print("\nConstructing the assembly graph...")


## Construct the assembly graph
#-------------------------------

node_count = 0

links = []

my_map = BidirectionalMap()

try:

    # Get links from .gfa file
    with open(assembly_graph_file) as file:

        line = file.readline()

        while line != "":

            # Identify lines with link information
            if line.startswith("L"):
                link = []

                strings = line.split("\t")

                start_1 = 'NODE_'
                end_1 = '_length'

                link1 = int(re.search('%s(.*)%s' % (start_1, end_1), strings[1]).group(1))

                start_2 = 'NODE_'
                end_2 = '_length'

                link2 = int(re.search('%s(.*)%s' % (start_2, end_2), strings[3]).group(1))

                link.append(link1)
                link.append(link2)
                links.append(link)

            elif line.startswith("S"):
                strings = line.split()

                start = 'NODE_'
                end = '_length'

                contig_num = int(re.search('%s(.*)%s' % (start, end), strings[1]).group(1))

                my_map[node_count] = int(contig_num)

                node_count += 1
            
            line = file.readline()


    print("\nTotal number of contigs available:", node_count)

    contigs_map = my_map
    contigs_map_rev = my_map.inverse

    # Create graph
    assembly_graph = Graph()

    # Add vertices
    assembly_graph.add_vertices(node_count)

    # Create list of edges
    edge_list = []

    for i in range(node_count):
        assembly_graph.vs[i]["id"]= i
        assembly_graph.vs[i]["label"]= str(i)
        
    # Iterate links
    for link in links:
        # Remove self loops
        if link[0] != link[1]:
            # Add edge to list of edges
            edge_list.append((contigs_map_rev[link[0]], contigs_map_rev[link[1]]))

    # Add edges to the graph 
    assembly_graph.add_edges(edge_list)
    assembly_graph.simplify(multiple=True, loops=False, combine_edges=None)

except:
    print("\nPlease make sure that the correct path to the assembly graph file is provided.")
    print("Exiting GraphBin...\nBye...!\n")
    sys.exit(2)

print("Total number of edges in the assembly graph:", len(edge_list))


# Get initial binning result
#----------------------------

print("\nObtaining the initial binning result...")

bins = [[] for x in range(n_bins)]

try:
    with open(contig_bins_file) as contig_bins:
        readCSV = csv.reader(contig_bins, delimiter=',')
        for row in readCSV:
            start = 'NODE_'
            end = ''
            contig_num = contigs_map_rev[int(re.search('%s(.*)%s' % (start, end), row[0]).group(1))]
            
            bin_num = int(row[1])-1
            bins[bin_num].append(contig_num)

    for i in range(n_bins):
        bins[i].sort()

except:
    print("\nPlease make sure that the correct path to the binning result file is provided and it is having the correct format.")
    print("Moreover, please check whether you have provided the correct assembler type as well.")
    print("Exiting GraphBin...\nBye...!\n")
    sys.exit(2)


# Remove labels of ambiguous vertices
#-------------------------------------

def getClosestLabelledVertices(graph, node, binned_contigs):
    queu_l = [graph.neighbors(node, mode='ALL')]
    visited_l = [node]
    labelled = []

    while len(queu_l) > 0:
        active_level = queu_l.pop(0)
        is_finish = False
        visited_l += active_level

        for n in active_level:
            if n in binned_contigs:
                is_finish = True
                labelled.append(n)
        if is_finish:
            return labelled
        else:
            temp = []
            for n in active_level:
                temp += graph.neighbors(n, mode='ALL')
            temp = list(set(temp))
            temp2 = []

            for n in temp:
                if n not in visited_l:
                    temp2.append(n)
            if len(temp2) > 0:
                queu_l.append(temp2)
    return labelled


print("\nDetermining ambiguous vertices...")

remove_labels = []

neighbours_have_same_label_list = []

for b in range(n_bins):

    for i in bins[b]:

        my_bin = b

        dist = {}

        # Get set of closest labelled vertices with distance = 1
        closest_neighbours = assembly_graph.neighbors(i, mode=ALL)

        # Determine whether all the closest labelled vertices have the same label as its own
        neighbours_have_same_label = True
        
        neighbours_binned = False
        
        for neighbour in closest_neighbours:
            for k in range(n_bins):
                if neighbour in bins[k]:
                    neighbours_binned = True
                    if k != my_bin:
                        neighbours_have_same_label = False
                        break
                        
        if not neighbours_have_same_label:
            remove_labels.append(i)
        elif neighbours_binned:
            neighbours_have_same_label_list.append(i)

for i in remove_labels:
    for n in range(n_bins):
        if i in bins[n]:
            bins[n].remove(i)

# Further remove labels of ambiguous vertices
binned_contigs = []

for n in range(n_bins):
    binned_contigs = sorted(binned_contigs+bins[n])
            
for b in range(n_bins):

    for i in bins[b]:
        
        if i not in neighbours_have_same_label_list:

            my_bin = b

            # Get set of closest labelled vertices
            closest_neighbours = getClosestLabelledVertices(assembly_graph, i, binned_contigs)

            if len(closest_neighbours) > 0:

                # Determine whether all the closest labelled vertices have the same label as its own
                neighbours_have_same_label = True

                for neighbour in closest_neighbours:
                    for k in range(n_bins):
                        if neighbour in bins[k]:
                            if k != my_bin:
                                neighbours_have_same_label = False
                                break

                if not neighbours_have_same_label and i not in remove_labels:
                    remove_labels.append(i)

remove_labels.sort()

print("Removing labels of ambiguous vertices...")

# Remove labels of ambiguous vertices
for i in remove_labels:
    for n in range(n_bins):
        if i in bins[n]:
            bins[n].remove(i)

print("\nObtaining Refined Binning result...")
        

# Get vertices which are not isolated and not in components without any labels
#-----------------------------------------------------------------------------

print("\nDeteremining vertices which are not isolated and not in components without any labels...")

non_isolated = []

for i in range(node_count):
    
    if i not in non_isolated and i in binned_contigs:

        component = []
        component.append(i)
        length = len(component)
        neighbours = assembly_graph.neighbors(i, mode=ALL)

        for neighbor in neighbours:
            if neighbor not in component:
                component.append(neighbor)

        component = list(set(component))

        while length!= len(component):

            length = len(component)

            for j in component:

                neighbours = assembly_graph.neighbors(j, mode=ALL)

                for neighbor in neighbours:
                    if neighbor not in component:
                        component.append(neighbor)

        labelled = False
        for j in component:
            if j in binned_contigs:
                labelled = True
                break

        if labelled:
            for j in component:
                if j not in non_isolated:
                    non_isolated.append(j)

print("Number of non-isolated contigs:", len(non_isolated))


# Run label propagation
#-----------------------

data = []

for contig in range(node_count):
    
    # Consider vertices that are not isolated

    if contig in non_isolated:
        line = []
        line.append(contig)

        assigned = False

        for i in range(n_bins):
            if contig in bins[i]:
                line.append(i+1)
                assigned = True
        
        if not assigned:
            line.append(0)

        neighbours = assembly_graph.neighbors(contig, mode=ALL)

        neighs = []

        for neighbour in neighbours:
            n = []
            n.append(neighbour)
            n.append(1.0)
            neighs.append(n)

        line.append(neighs)

        data.append(line)

lp = LabelProp()

lp.load_data_from_mem(data)

print("\nStarting label propagation with eps="+str(diff_threshold)+" and max_iteration="+str(max_iteration))

ans = lp.run(diff_threshold, max_iteration, show_log=True, clean_result=False) 
ans.sort()

print("\nObtaining Label Propagation result...")

for l in ans:
    for i in range(n_bins):
        if l[1]==i+1 and l[0] not in bins[i]:
            bins[i].append(l[0])


# Remove labels of ambiguous vertices
#-------------------------------------

print("\nDetermining ambiguous vertices...")

remove_labels = []

for b in range(n_bins):

    for i in bins[b]:

        my_bin = b

        closest_neighbours = assembly_graph.neighbors(i, mode=ALL)

        # Determine whether all the closest labelled vertices have the same label as its own
        neighbours_have_same_label = True
        
        for neighbour in closest_neighbours:
            for k in range(n_bins):
                if neighbour in bins[k]:
                    if k != my_bin:
                        neighbours_have_same_label = False
                        break
                        
        if not neighbours_have_same_label:
            remove_labels.append(i)

remove_labels.sort()

print("Removing labels of ambiguous vertices...")

# Remove labels of ambiguous vertices
for i in remove_labels:
    for n in range(n_bins):
        if i in bins[n]:
            bins[n].remove(i)

elapsed_time = time.time() - start_time

print("\nObtaining the Final Refined Binning result...")

for i in range(n_bins):
    bins[i].sort()

# Print elapsed time for the process
print("\nElapsed time: ", elapsed_time, " seconds")


# Write result to output file
#-----------------------------

print("\nWriting the Final Binning result to file...")

output_bins = []

for i in range(node_count):
    for k in range(n_bins):
        if i in bins[k]:
            line = []
            line.append("NODE_"+str(contigs_map[i]))
            line.append(k+1)
            output_bins.append(line)

output_file = output_path + prefix + 'graphbin_output.csv'

with open(output_file, mode='w') as out_file:
    output_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    for row in output_bins:
        output_writer.writerow(row)

print("\nFinal binning results can be found at", output_file)


unbinned_contigs = []

for i in range(node_count):
    if i in remove_labels or i not in non_isolated:
        line = []
        line.append("NODE_"+str(contigs_map[i]))
        unbinned_contigs.append(line)

if len(unbinned_contigs)!=0:
    unbinned_file = output_path + prefix + 'graphbin_unbinned.csv'

    with open(unbinned_file, mode='w') as out_file:
        output_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        for row in unbinned_contigs:
            output_writer.writerow(row)

    print("Unbinned contigs can be found at", unbinned_file)


# Exit program
#--------------

print("\nThank you for using GraphBin!\n")