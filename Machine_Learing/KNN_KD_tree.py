# -*- coding:utf-8 -*-

T = [[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]]

class node:
    def __init__(self,point):
        self.left = None
        self.right = None
        self.point = point
        pass

def median(lst):
    m = len(lst)/2
    return lst[m],m


def build_kdtree(data,d):
    #according the value of x[d] to sort data
    data = sorted(data,key=lambda x: x[d])
    print data
    p,m = median(data)
    print p,m
    tree = node(p)

    del data[m]
    #print data,p

    if m > 0: tree.left = build_kdtree(data[:m],not d)
    if len(data) > 1: tree.right = build_kdtree(data[m:],not d)
    return tree

if __name__ == "__main__":
    kd_tree = build_kdtree(T,0)
    #print kd_tree
    
