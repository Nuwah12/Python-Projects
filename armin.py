from collections import defaultdict
from pandas import Series, DataFrame
import itertools as it
import pandas as pd
import math
import csv
import sys
import argparse
import collections
import glob
import os
import re
import requests
import string
import sys

class Armin():
    
    def apriori(self, input_filename, output_filename, min_support_percentage, min_confidence):
        """
        Implement the Apriori algorithm, and write the result to an output file

        PARAMS
        ------
        input_filename: String, the name of the input file
        output_filename: String, the name of the output file
        min_support_percentage: float, minimum support percentage for an itemset
        min_confidence: float, minimum confidence for an association rule to be significant

        """
        print("""===================================================================
            \nSupport Threshold: {}""".format(min_support_percentage))

        code = 0

        item_counts = defaultdict(int)
        paircount = defaultdict(int)
        tripcount = defaultdict(int)
        total_transactions = 0

        singles_support_per = []
        doubles_support_per = []
        triples_support_per = []

        master_frequents = defaultdict(float)
        all_transactions = []

        delim = ","

        lines = []

        outf = open(output_filename, "w")

        #Read in itemset
        with open(input_filename, "r") as inf:
            for line in inf:
                print(line)
                lines.append(line.strip())
                all_transactions.append(line.strip().replace(",", " "))

        # formatting check sigh
        for l in lines:
            try:
                if l.index(" ") == 2:
                    delim = ", "
                    break
            except:
                continue

        #SINGLES
        for line in lines:
            for item in line.split(delim)[1:]:
                #print(item)
                item_counts[item]+=1
            total_transactions += 1
        #print(item_counts)
        #print("TOTAL transactions: ", total_transactions)
        #get frequent items SINGLES
        frequents = set()
        for key in item_counts:
            if (item_counts[key] / total_transactions) >= min_support_percentage:
                print("Found frequent SINGLE! {}, sup = {:.4f}".format(key, item_counts[key] / total_transactions))
                outf.write("S,{:.4f},{item1}\n".format(item_counts[key] / total_transactions, item1 = key))
                singles_support_per.append(item_counts[key] / total_transactions)
                frequents.add(key)

        #DOUBLES
        for line in lines:
            items = line.split(delim)[1:]
            for idx1 in range(len(items)-1):
                if items[idx1] not in frequents:
                    continue
                for idx2 in range(idx1 + 1, len(items)):
                    if items[idx2] not in frequents:
                        continue
                    pair = self.stringify(items[idx1], items[idx2])
                    paircount[pair] += 1 

        # get frequent DOUBLES
        freq_pairs = set()
        for key in paircount:
            if paircount[key] / total_transactions >= min_support_percentage:
                print("Found frequent DOUBLE! {} {}, sup = {:.4f}".format(key.split()[0], key.split()[1], paircount[key] / total_transactions))
                outf.write("S,{:.4f},{item1},{item2}\n".format(paircount[key] / total_transactions, item1 = key.split()[0], item2 = key.split()[1]))
                master_frequents[key] = paircount[key] / total_transactions
                freq_pairs.add(key)
                doubles_support_per.append(paircount[key] / total_transactions)

        #TRIPLES
        for line in lines:
            items = line.split(delim)[1:]
            for idx1 in range(len(items)-2):
                if items[idx1] not in frequents:
                    continue
                for idx2 in range(idx1 + 1, len(items) - 1):
                    if items[idx2] not in frequents:
                        continue
                    for idx3 in range(idx2 + 1, len(items)):
                        if items[idx3] not in frequents:
                            continue

                        pairs = self.gen_pairs(items[idx1], items[idx2], items[idx3])
                        #print(pairs)
                        #print(frequents)
                        for pair in pairs:
                            if pair[0] not in list(frequents) and pair[1] not in list(frequents):
                                code = 1
                                break
                        if code == 1:
                            continue
                        triple = self.stringify(items[idx1], items[idx2], items[idx3])
                        tripcount[triple]+=1
    
        # get freq TRIPLES
        freqtrips = set()
        for key in tripcount:
            #print("Trying triple {}, sup = {:.4f}".format(key, tripcount[key] / total_transactions))
            if tripcount[key] / total_transactions >= min_support_percentage:
                print("Found frequent TRIPLE! {}, sup. % = {:.4f}".format(key, tripcount[key] / total_transactions))
                outf.write("S,{:.4f},{item1},{item2},{item3}\n".format(tripcount[key] / total_transactions, 
                            item1 = key.split()[0], item2 = key.split()[1], 
                            item3 = key.split()[2]))
                master_frequents[key] = tripcount[key] / total_transactions
                freqtrips.add(key)
                triples_support_per.append(tripcount[key] / total_transactions)


        # generate association rules
        rules = []
        print(master_frequents)
        for key in master_frequents:
            r1 = 0
            l1 = 0
            singleside = ""
            if len(key.split()) == 2:
                r1 = self.get_confidence(key.split()[0], key.split()[1], all_transactions)
                l1 = self.get_confidence(key.split()[1], key.split()[0], all_transactions)
                if r1 >= min_confidence:
                    rules.append("R,{:.4f},{:.4f},{lh},'=>',{rh}".format(master_frequents[key], r1, lh = key.split()[0], rh = key.split()[1]))
                if l1 >= min_confidence:
                    rules.append("R,{:.4f},{:.4f},{lh},'=>',{rh}".format(master_frequents[key], l1, lh = key.split()[1], rh = key.split()[0]))
            elif len(key.split()) == 3:
                twoside = list(it.combinations(key.split(), 2))
                print("========================== All pairs from triple ::: ",twoside)
                for pair_og in twoside:
                    pair_og = sorted(list(pair_og))
                    pair = "{} {}".format(pair_og[0], pair_og[1])
                    singleside_og =  set(key.split()) - set(pair)
                    singleside = list(singleside_og)[0]

                    r1 = self.get_confidence(singleside, pair, all_transactions)
                    l1 = self.get_confidence(pair, singleside, all_transactions)

                    if r1 >= min_confidence:
                        rules.append("R,{:.4f},{:.4f},{lh},'=>',{rh1},{rh2}".format(master_frequents[key], r1, lh = singleside, rh1 = pair[0], rh2 = pair[2]))
                    if l1 >= min_confidence:
                        rules.append("R,{:.4f},{:.4f},{lh1},{lh2},'=>',{rh}".format(master_frequents[key], l1, lh1 = pair[0], lh2 = pair[2], rh = singleside))

        for r in rules:
            print("{}\n".format(r))
            outf.write("{}\n".format(r))

        outf.close()

        print(master_frequents)

    def get_confidence(self, lhr, rhr, alltrans):
        total = "{} {}".format(lhr, rhr)
        lhr_supp = self.get_supp_percent(alltrans, lhr)
        total_supp = self.get_supp_percent(alltrans, total)
        print("COMBINED {} sup = {}, lhr sup = {}".format(total, total_supp, lhr_supp))
        return total_supp / lhr_supp

    def stringify(self, *args):
        if len(args) == 1:
            return ""+args
        if len(args) == 2:
            args = sorted(args)
            return "{} {}".format(args[0], args[1])
        if len(args) == 3:
            args = sorted(args)
            return "{} {} {}".format(args[0], args[1], args[2])

    def gen_pairs(self, i1, i2, i3):
        m = [i1, i2, i3]

        comb = list(it.combinations(m, 2))

        return comb

    def gen_rule(self, n, r):
        return list(it.combinations(n, r))

    def get_supp_percent(self, trans, item):
        count = 0
        if len(item.split()) == 1:
            for i in trans:
                if item in i:
                    count+=1
            return count / len(trans)

        elif len(item.split()) == 2:
            for i in trans:
                if item.split()[0] in i and item.split()[1] in i:
                    count+=1
            return count / len(trans)

        elif len(item.split()) == 3:
            for i in trans:
                if item.split()[0] in i and item.split()[1] in i and item.split()[2] in i:
                    count+=1
            return count / len(trans)

if __name__ == "__main__":
    armin = Armin()
    armin.apriori('input.csv', 'output.sup=0.5,conf=0.7.csv', 0.5, 0.7)
    armin.apriori('input.csv', 'output.sup=0.5,conf=0.8.csv', 0.5, 0.8)
    armin.apriori('input.csv', 'output.sup=0.6,conf=0.8.csv', 0.6, 0.8)