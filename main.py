from igraph import *
import csv
import operator

from labelprop import LabelProp

assembly_graph_file = "/media/vijinim/data/Experiments/Data/1_Data_For_Paper/3G_Output/assembly_graph_with_scaffolds.gfa"
contig_file = "/media/vijinim/data/Experiments/Data/1_Data_For_Paper/3G_Output/contigs.fasta"
contig_paths = "/media/vijinim/data/Experiments/Data/1_Data_For_Paper/3G_Output/contigs.paths"
contig_bins_file = "/media/vijinim/data/Experiments/Data/1_Data_For_Paper/3G_Output/MaxBin_Result/contig_bins.csv"
n_bins = 3


paths = []
links = []


# Get contig paths from contigs.paths
with open(contig_paths) as file:
    name = file.readline()
    path = file.readline()
    
    while name != "" and path != "":
            
        while ";" in path:
            path = path[:-2]+","+file.readline()
            
        paths.append(path.split("\n")[0])
        
        name = file.readline()
        path = file.readline()

node_count = int(len(paths)/2)

print("Total number of contigs available:", node_count)



## ---Construct assembly graph---

# Get links from assembly_graph_with_scaffolds.gfa
with open(assembly_graph_file) as file:
    line = file.readline()
    
    while line != "":
        
        # Identify lines with link information
        if "L" in line:
            strings = line.split("\t")
            links.append(strings[1]+strings[2]+" "+strings[3]+strings[4])
        line = file.readline()

# Create graph
g = Graph()

# Add vertices
g.add_vertices(node_count)


for i in range(len(g.vs)):
    g.vs[i]["id"]= i
    g.vs[i]["label"]= str(i)

# Iterate paths
for i in range(len(paths)):
    segments = paths[i].split(",")
    start = segments[0]
    end = segments[len(segments)-1]
    
    new_links = []
    connections = []
    
    # Iterate links
    for link in links:
        link_list = link.split()
        
        if start in link_list[0]:
            new_links.append(link_list[1])
        elif start in link_list[1]:
            new_links.append(link_list[0])
        if end in link_list[0]:
            new_links.append(link_list[1])
        elif end in link_list[1]:
            new_links.append(link_list[0])
    
    # Determine connections
    for new_link in new_links:
        for j in range(len(paths)):
            if new_link in paths[j] and int(j/2) not in connections and int(j/2)!=int(i/2):
                ind = int(j/2)
                connections.append(ind)
    
    # Add connections in graph
    for connection in connections:
        g.add_edge(int(i/2),connection)

g.simplify(multiple=True, loops=False, combine_edges=None)


# ---Get initial binning result---

bins = [[] for x in range(n_bins)]

with open(contig_bins_file) as contig_bins:
    readCSV = csv.reader(contig_bins, delimiter=',')
    for row in readCSV:
        bin_num = int(row[1])-1
        contig_num = int(row[0])
        # print(contig_num,bin_num)
        bins[bin_num].append(contig_num)

print("\nMaxBin result\n----------------")

for i in range(n_bins):
    bins[i].sort()
    print("Bin", i+1, ":\n", bins[i])


# ---Remove labels of ambiguous vertices---

remove_labels = []

for b in range(n_bins):

    for i in bins[b]:

        my_bin = b


        # dist = {}

        # for j in range(node_count):
        #     dis = g.shortest_paths_dijkstra(source=i, target=j, weights=None, mode=OUT)[0][0]
        #     if dis != 0:
        #         print(i, j, dis)
        #         dist[i] = dis

        # sorted_dist = sorted(dist.items(), key=operator.itemgetter(1))

        # print(i, dist)

        # distances = [1000000 for x in range(n_bins)]

        # for element in sorted_dist:

        #     count_is_million = True

        #     for k in range(n_bins):
        #         if distances[k] == 1000000:
        #             count_is_million = False

        #     if not count_is_million:

        #         for h in range(n_bins):
        #             if element[0] in bins[h] and distances[h] == 1000000:
        #                 distances[h] = element[1]

        # min_dist = 100000
        # min_index = 1000

        # for k in range(n_bins):

        #     if distances[k] < min_dist:
        #         min_dist = distances[k]
        #         min_index = k

        # if min_index != my_bin:
        #     remove_labels.append(i)



        neighbours = g.neighbors(i, mode=ALL)
        
        counts = [0 for x in range(n_bins)]

        for neighbour in neighbours:

            for j in range(n_bins):
                
                if neighbour in bins[j]:
                    counts[j] += 1
                    
        other_counts_zero = True

        for k in range(n_bins):

            if counts[k]!=0 and k!=my_bin:
                other_counts_zero = False

        if not other_counts_zero:
             remove_labels.append(i)


remove_labels.sort()
print("\nRemove labels of:", remove_labels)

for i in remove_labels:

    for n in range(n_bins):
        if i in bins[n]:
            bins[n].remove(i)

print("\nRefined MaxBin result\n---------------------")

for i in range(n_bins):
    print("Bin", i+1, ":\n", bins[i])



# ---Run label propagation---

data = []

for contig in range(node_count):
    
    neighbours = g.neighbors(contig, mode=ALL)
    
    if len(neighbours) > 0:
        line = []
        line.append(contig)

        assigned = False

        for i in range(n_bins):
            if contig in bins[i]:
                line.append(i+1)
                assigned = True
        
        if not assigned:
            line.append(0)

        neighbours = g.neighbors(contig, mode=ALL)

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

print("\nStarting label propagation\n---------------------")

ans = lp.run(0.00001, 100, show_log=True, clean_result=False) 

ans.sort()


for l in ans:
    for i in range(n_bins):
        if l[1]==i+1 and l[0] not in bins[i]:
            bins[i].append(l[0])


print("\nLabel Propagation result\n---------------------")

for i in range(n_bins):
    print("Bin", i+1, ":\n", bins[i])