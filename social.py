#!/usr/bin/env python

import BeautifulSoup as bs
import simplejson as json
import urllib2
import datetime
import shelve

class Node(object):
    query_url = "http://socialgraph.apis.google.com/lookup?q=%s&fme=1&edo=1&edi=1"
    node_cache = {}

    def __init__(self, url, python_obj=None):
        print "making %s" % url
        self.url = url

        if python_obj:
            self.python_obj = python_obj
            self.attributes = Attributes(python_obj.get('attributes', ''))
        else:
            self.python_obj = None
            self.attributes = None

        self.nodes_referenced = {}
        self.nodes_referenced_by = {}
        self.claimed_nodes = []
        self.unverified_claiming_nodes = []
        self.types = []

    def fetch_social_object(self):
        print "querying %s" % self.url
        resp = urllib2.urlopen(self.query_url % self.url)
        json_decoder = json.JSONDecoder()
        temp_python_obj = json_decoder.decode(resp.read())
        name = temp_python_obj['canonical_mapping'].values()[0]
        self.python_obj = temp_python_obj['nodes'][name]

    def populate_structure(self, recurse=False):
        if not self.python_obj:
            self.fetch_social_object()

        for claimed_node in self.python_obj.get('claimed_nodes', []):
            n = Node.get_or_create(claimed_node)
            if recurse:
                n.populate_structure(recurse=True)
            self.claimed_nodes.append(n)

        for unverified_node in self.python_obj.get('unverified_claiming_nodes', []):
            n = Node.get_or_create(unverified_node)
            self.unverified_claiming_nodes.append(n)

        for name,types in self.python_obj.get('nodes_referenced',{}).iteritems():
            n = Node.get_or_create(name)
            if recurse:
                n.populate_structure(recurse=True)
            n.types = types['types']
            self.nodes_referenced[name] = n

        for name,types in self.python_obj.get('nodes_referenced_by',{}).iteritems():
            n = Node.get_or_create(name)
            n.types = types['types']
            self.nodes_referenced_by[name] = n


    @classmethod
    def get_or_create(self, url, python_obj=None):
        db = shelve.open('test')
        if self.node_cache.has_key(url):
            #In local object cache
            print "NODE: pulling %s from cache" % url
            db.close()
            return self.node_cache[url]
        if db.has_key(url):
            #DB has key, put in local object cache
            print "DB: pulling %s from cache" % url
            n = Node(url, db[url])
            self.node_cache[url] = n
            db.close()
            return n
        elif python_obj:
            db[url] = python_obj
            db.close()
            return Node(url, python_obj)
        else:
            return Node(url, python_obj)
            print "FAIL FAIL FAIL FAIL"

    def __unicode__(self):
        return self.url

    def __str__(self):
        return self.url

    def __repr__(self):
        return "<Node object: %s>" % self.url

class Request(object):
    query_url = "http://socialgraph.apis.google.com/lookup?q=%s&fme=1&edo=1&edi=1"

    def __init__(self, url):
        self.url = url
        self.toplevel_nodes = []
        self.canonical_mapping = {}

    def fetch_social_object(self):
        resp = urllib2.urlopen(self.query_url % self.url)
        json_decoder = json.JSONDecoder()
        self.python_obj = json_decoder.decode(resp.read())

    def populate_structure(self, recurse=False):
        self.fetch_social_object()
        self.canonical_mapping = self.python_obj['canonical_mapping']
        for url,node in self.python_obj['nodes'].items():
            t = Node.get_or_create(url=url, python_obj=node)
            if recurse:
                t.populate_structure(recurse=True)
            else:
                t.populate_structure(recurse=False)
            self.toplevel_nodes.append(t)

    @property
    def urls_claimed(self):
        urls = set()
        for node in self.toplevel_nodes:
            urls.add(node)
            for claimed in node.claimed_nodes:
                urls.add(claimed)
        return list(urls)

    @property
    def urls_referenced(self):
        urls = set()
        for node in self.toplevel_nodes:
            for name,ref in node.nodes_referenced.items():
                #print "%s --%s--> %s" % (node, ref.types, name)
                urls.add(ref)
        return list(urls)


    def print_urls_referenced(self):
        urls = set()
        for node in self.toplevel_nodes:
            for name,ref in node.nodes_referenced.items():
                print "%s -> %s;" % (node, name)
        return list(urls)


    def loves(self, lover):
        my_nodes = self.urls_claimed
        lover_nodes = lover.urls_referenced
        for node in my_nodes:
            if node in lover_nodes:
                print "%s loves %s" % (lover, node)
                return True
        return False

    def __repr__(self):
        return "<Request object: %s>" % self.url


class Attributes(object):

    def __init__(self, kwargs={}):
        self.kwargs = kwargs
        self.populate_structure()

    def populate_structure(self):
        self.url = self.kwargs.get('url', '')
        self.profile = self.kwargs.get('profile', '')
        self.rss = self.kwargs.get('rss', '')
        self.atom = self.kwargs.get('atom', '')
        self.foaf = self.kwargs.get('foaf', '')
        self.photo = self.kwargs.get('photo', '')
        self.fn = self.kwargs.get('fn', '')
