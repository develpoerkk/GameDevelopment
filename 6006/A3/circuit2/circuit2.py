#!/usr/bin/env python

import json   # Used when TRACE=jsonp
import os     # Used to get the TRACE environment variable
import re     # Used when TRACE=jsonp
import sys    # Used to smooth over the range / xrange issue.

# Python 3 doesn't have xrange, and range behaves like xrange.
if sys.version_info >= (3,):
    xrange = range

# Circuit verification library.

class Wire(object):
  """A wire in an on-chip circuit.
  
  Wires are immutable, and are either horizontal or vertical.
  """
  
  def __init__(self, name, x1, y1, x2, y2):
    """Creates a wire.
    
    Raises an ValueError if the coordinates don't make up a horizontal wire
    or a vertical wire.
    
    Args:
      name: the wire's user-visible name
      x1: the X coordinate of the wire's first endpoint
      y1: the Y coordinate of the wire's first endpoint
      x2: the X coordinate of the wire's last endpoint
      y2: the Y coordinate of the wire's last endpoint
    """
    # Normalize the coordinates.
    if x1 > x2:
      x1, x2 = x2, x1
    if y1 > y2:
      y1, y2 = y2, y1
    
    self.name = name
    self.x1, self.y1 = x1, y1
    self.x2, self.y2 = x2, y2
    self.object_id = Wire.next_object_id()
    
    if not (self.is_horizontal() or self.is_vertical()):
      raise ValueError(str(self) + ' is neither horizontal nor vertical')
  
  def is_horizontal(self):
    """True if the wire's endpoints have the same Y coordinates."""
    return self.y1 == self.y2
  
  def is_vertical(self):
    """True if the wire's endpoints have the same X coordinates."""
    return self.x1 == self.x2
  
  def intersects(self, other_wire):
    """True if this wire intersects another wire."""
    # NOTE: we assume that wires can only cross, but not overlap.
    if self.is_horizontal() == other_wire.is_horizontal():
      return False 
    
    if self.is_horizontal():
      h = self
      v = other_wire
    else:
      h = other_wire
      v = self
    return v.y1 <= h.y1 and h.y1 <= v.y2 and h.x1 <= v.x1 and v.x1 <= h.x2
  
  def __repr__(self):
    # :nodoc: nicer formatting to help with debugging
    return('<wire ' + self.name + ' (' + str(self.x1) + ',' + str(self.y1) + 
           ')-(' + str(self.x2) + ',' + str(self.y2) + ')>')
  
  def as_json(self):
    """Dict that obeys the JSON format restrictions, representing the wire."""
    return {'id': self.name, 'x': [self.x1, self.x2], 'y': [self.y1, self.y2]}

  # Next number handed out by Wire.next_object_id()
  _next_id = 0
  
  @staticmethod
  def next_object_id():
    """Returns a unique numerical ID to be used as a Wire's object_id."""
    id = Wire._next_id
    Wire._next_id += 1
    return id

class WireLayer(object):
  """The layout of one layer of wires in a chip."""
  
  def __init__(self):
    """Creates a layer layout with no wires."""
    self.wires = {}
  
  def wires(self):
    """The wires in the layout."""
    self.wires.values()
  
  def add_wire(self, name, x1, y1, x2, y2):
    """Adds a wire to a layer layout.
    
    Args:
      name: the wire's unique name
      x1: the X coordinate of the wire's first endpoint
      y1: the Y coordinate of the wire's first endpoint
      x2: the X coordinate of the wire's last endpoint
      y2: the Y coordinate of the wire's last endpoint
    
    Raises an exception if the wire isn't perfectly horizontal (y1 = y2) or
    perfectly vertical (x1 = x2)."""
    if name in self.wires:
        raise ValueError('Wire name ' + name + ' not unique')
    self.wires[name] = Wire(name, x1, y1, x2, y2)
  
  def as_json(self):
    """Dict that obeys the JSON format restrictions, representing the layout."""
    return { 'wires': [wire.as_json() for wire in self.wires.values()] }
  
  @staticmethod
  def from_file(file):
    """Builds a wire layer layout by reading a textual description from a file.
    
    Args:
      file: a File object supplying the input
    
    Returns a new Simulation instance."""

    layer = WireLayer()
    
    while True:
      command = file.readline().split()
      if command[0] == 'wire':
        coordinates = [float(token) for token in command[2:6]]
        layer.add_wire(command[1], *coordinates)
      elif command[0] == 'done':
        break
      
    return layer

def nodeNum(node):
  if(node is None):
    return 0
  return node.nodeNum

def height(node):
    if(node is None):
        return -1
    else:
        return node.height

class Node(object):
    def __init__(self,key,patient):
        self.left=None
        self.right=None
        self.key=key
        self.height=0
        self.patient=patient
        self.nodeNum=1
    def updateHeight(self):
        self.height=1+max(height(self.right),height(self.left))
    def updateNodeNum(self):
        self.nodeNum=nodeNum(self.right)+nodeNum(self.left)+1

    def rRotate(self):
        lNode=self.left
        patient=self.patient
        self.left=lNode.right
        if(self.left!=None):
            self.left.patient=self
        lNode.right=self
        self.patient=lNode
        if(self == patient.right):
            patient.right=lNode
        else:            
            patient.left=lNode
        lNode.patient=patient
        self.updateHeight()
        self.updateNodeNum()
        lNode.updateHeight()
        lNode.updateNodeNum()
        
    def lRotate(self):
        rNode=self.right
        patient=self.patient
        self.right=rNode.left
        if(self.right != None):
            self.right.patient=self
        rNode.left=self
        self.patient=rNode
        if(self==patient.right):
            patient.right=rNode
        else:
            patient.left=rNode
        rNode.patient=patient            
        self.updateHeight()
        self.updateNodeNum()
        rNode.updateHeight()
        rNode.updateNodeNum()

    def rlRotate(self):
        self.right.rRotate()
        self.lRotate()
    def lrRotate(self):
        self.left.lRotate()
        self.rRotate()
    def checkAndFixRightInsert(self):
        if(height(self.right)-height(self.left)<=1):
            self.updateHeight()
            self.updateNodeNum()
            return
        if(height(self.right.left)-height(self.right.right)>=1):
            self.rlRotate()
        else:
            self.lRotate()

    def checkAndFixLeftInsert(self):
        if(height(self.left)-height(self.right)<=1):
            self.updateHeight()
            self.updateNodeNum()
            return
        if(height(self.left.right)-height(self.left.left)>=1):
            self.lrRotate()
        else:
            self.rRotate()
    def checkAndFixRightDelete(self):
        self.checkAndFixLeftInsert()
    def checkAndFixLeftDelete(self):
        self.checkAndFixRightInsert()
    
    
#klevel=1

class RangeIndex(object):
  """
  Post: Array-based range index implementation.
  Now: AVL-tree-based range index implementation
  """
  
  def __init__(self):
    """Initially empty range index."""
    self.head=Node(0,None)
    
  def add(self, key):
    """Inserts a key in the range index."""
    
    if key is None:
        raise ValueError('Cannot insert nil in the index')
    if(self.head.right is None):
        self.head.right=Node(key,self.head)
    else:
        self.__add__(self.head.right,key)
    
  def __add__(self,toBeInserted,key):
      if(toBeInserted is None):
          if(self.head.right is None):
            raise Exception("Fucking! We algothrim won't happened that we add to a None!")
          else:
            raise Exception("We algothrim won't happened that we add to a None!")
      if(key>toBeInserted.key):
          if(toBeInserted.right is None):
              toBeInserted.right=Node(key,toBeInserted)
              toBeInserted.updateHeight()
              toBeInserted.updateNodeNum()
          else:
              self.__add__(toBeInserted.right,key)
              toBeInserted.checkAndFixRightInsert()
              
      elif(key<toBeInserted.key):
          if(toBeInserted.left is None):
              toBeInserted.left=Node(key,toBeInserted)
              toBeInserted.updateHeight()
              toBeInserted.updateNodeNum()
          else:
              self.__add__(toBeInserted.left,key)
              toBeInserted.updateHeight()
              toBeInserted.updateNodeNum()
              toBeInserted.checkAndFixLeftInsert()

      else:
          raise Exception("Key duplitate found!")
      
  def remove(self, key):
    """Removes a key from the range index."""
    self.__remove__(self.head.right,key)
  
  def __remove__(self,currentNode,key):
      if(key>currentNode.key):
          self.__remove__(currentNode.right,key)
          currentNode.updateHeight()
          currentNode.updateNodeNum()
          currentNode.checkAndFixRightDelete()
      elif(key<currentNode.key):
          self.__remove__(currentNode.left,key)
          currentNode.updateHeight()
          currentNode.updateNodeNum()
          currentNode.checkAndFixLeftDelete()
      else:
          if(currentNode.right is None or currentNode.left is None):
            patient=currentNode.patient  
            if(currentNode == patient.right):
                  patient.right=currentNode.right or currentNode.left
                  if(patient.right is not None):
                      patient.right.patient=currentNode.patient
                  patient.updateNodeNum()
                  patient.updateHeight()
                  patient.checkAndFixRightDelete()
            else:
                  patient.left=currentNode.right or currentNode.left
                  if(patient.left is not None):
                      patient.left.patient=patient
                  patient.updateNodeNum()
                  patient.updateHeight()
                  patient.checkAndFixLeftDelete()
          else:
              # find the next larger element,
              next_larger=currentNode.right
              while(next_larger.left is not None):
                  next_larger=next_larger.left
              next_larger.key,currentNode.key=currentNode.key,next_larger.key
              self.__remove__(next_larger,key)
              
        
  def list(self, first_key, last_key):
    """List of values for the keys that fall within [first_key, last_key]."""
    lca=self.__lca__(self.head.right,first_key,last_key)
    resultList=[]
    self.__nodeList__(lca,first_key,last_key,resultList)
    return resultList
  
    
  def count(self, first_key, last_key):
    """Number of keys that fall within [first_key, last_key]."""
    
    hit1,rank1=self.rank(first_key)
    hit2,rank2=self.rank(last_key)
    return rank2-rank1+hit1
  
  def __lca__(self,tree,l,h):
    while(True):
      if(tree is None or (l<=tree.key and h>=tree.key)):
        break
      if(l<tree.key):
        tree=tree.left
      else:
        tree=tree.right
    return tree
  def __nodeList__(self,node,l,h,result):
    if(node is None): return
    global klevel
    if(l<=node.key <=h):
      result.append(node.key)
#      print(str(klevel)+'    '+str(node.key))
    if(node.key>=l):
#      klevel+=1
      self.__nodeList__(node.left,l,h,result)
#      klevel-=1
    if(node.key<=h):
#      klevel+=1
      self.__nodeList__(node.right,l,h,result)
#      klevel-=1
  def __rank__(self,currentNode,key):
    if(currentNode is None):
      return False,0
    if(key>currentNode.key):
      hit,count=self.__rank__(currentNode.right,key)
      return hit,count+1+nodeNum(currentNode.left)
    if(key<currentNode.key):
      return self.__rank__(currentNode.left,key)
    return True,1+nodeNum(currentNode.left)
    
  def rank(self,key):
    return self.__rank__(self.head.right,key)


index=RangeIndex()
index.add(4)
index.add(2)
index.add(1)
index.add(3)
index.add(6)
index.add(5)
index.add(7)
index.list(0,7)
print(index.head.right.nodeNum)
print(index.head.right.left.nodeNum)
print(index.head.right.right.nodeNum)
index.remove(6)
index.remove(5)
index.remove(4)
index.list(0,7)
index.list(0,7)
index.count(-88,7)

import random

index=RangeIndex()
addList=[]

for i in range(0,100):
  toAdd=random.randint(-999999,99999)
#  print(str(toAdd))
  index.add(toAdd)
  addList.append(toAdd)

print(str(index.count(-999999,99999)))
for i in range(0,25):
  elem=random.choice(addList)
  addList.remove(elem)
  index.remove(elem)
print(str(index.count(-999999,99999)))

print(str(len(index.list(-999999,99999))))

head=index.head.right

head.left.nodeNum
head.left.right.nodeNum+head.left.left.nodeNum

class TracedRangeIndex(RangeIndex):
  """Augments RangeIndex to build a trace for the visualizer."""
  
  def __init__(self, trace):
    """Sets the object receiving tracing info."""
    RangeIndex.__init__(self)
    self.trace = trace
  
  def add(self, key):
    self.trace.append({'type': 'add', 'id': key.wire.name})
    RangeIndex.add(self, key)
  
  def remove(self, key):
    self.trace.append({'type': 'delete', 'id': key.wire.name})
    RangeIndex.remove(self, key)
  
  def list(self, first_key, last_key):
    result = RangeIndex.list(self, first_key, last_key)
    self.trace.append({'type': 'list', 'from': first_key.key,
                       'to': last_key.key,
                       'ids': [key.wire.name for key in result]}) 
    return result
  
  def count(self, first_key, last_key):
    result = RangeIndex.count(self, first_key, last_key)
    self.trace.append({'type': 'list', 'from': first_key.key,
                       'to': last_key.key, 'count': result})
    return result

class ResultSet(object):
  """Records the result of the circuit verifier (pairs of crossing wires)."""
  
  def __init__(self):
    """Creates an empty result set."""
    self.crossings = []
  
  def add_crossing(self, wire1, wire2):
    """Records the fact that two wires are crossing."""
    self.crossings.append(sorted([wire1.name, wire2.name]))
  
  def write_to_file(self, file):
    """Write the result to a file."""
    for crossing in self.crossings:
      file.write(' '.join(crossing))
      file.write('\n')

class TracedResultSet(ResultSet):
  """Augments ResultSet to build a trace for the visualizer."""
  
  def __init__(self, trace):
    """Sets the object receiving tracing info."""
    ResultSet.__init__(self)
    self.trace = trace
    
  def add_crossing(self, wire1, wire2):
    self.trace.append({'type': 'crossing', 'id1': wire1.name,
                       'id2': wire2.name})
    ResultSet.add_crossing(self, wire1, wire2)

class KeyWirePair(object):
  """Wraps a wire and the key representing it in the range index.
  
  Once created, a key-wire pair is immutable."""
  
  def __init__(self, key, wire):
    """Creates a new key for insertion in the range index."""
    self.key = key
    if wire is None:
      raise ValueError('Use KeyWirePairL or KeyWirePairH for queries')
    self.wire = wire
    self.wire_id = wire.object_id

  def __lt__(self, other):
    # :nodoc: Delegate comparison to keys.
    return (self.key < other.key or
            (self.key == other.key and self.wire_id < other.wire_id))
  
  def __le__(self, other):
    # :nodoc: Delegate comparison to keys.
    return (self.key < other.key or
            (self.key == other.key and self.wire_id <= other.wire_id))  

  def __gt__(self, other):
    # :nodoc: Delegate comparison to keys.
    return (self.key > other.key or
            (self.key == other.key and self.wire_id > other.wire_id))
  
  def __ge__(self, other):
    # :nodoc: Delegate comparison to keys.
    return (self.key > other.key or
            (self.key == other.key and self.wire_id >= other.wire_id))

  def __eq__(self, other):
    # :nodoc: Delegate comparison to keys.
    return self.key == other.key and self.wire_id == other.wire_id
  
  def __ne__(self, other):
    # :nodoc: Delegate comparison to keys.
    return self.key == other.key and self.wire_id == other.wire_id

  def __hash__(self):
    # :nodoc: Delegate comparison to keys.
    return hash([self.key, self.wire_id])

  def __repr__(self):
    # :nodoc: nicer formatting to help with debugging
    return '<key: ' + str(self.key) + ' wire: ' + str(self.wire) + '>'

class KeyWirePairL(KeyWirePair):
  """A KeyWirePair that is used as the low end of a range query.
  
  This KeyWirePair is smaller than all other KeyWirePairs with the same key."""
  def __init__(self, key):
    self.key = key
    self.wire = None
    self.wire_id = -1000000000

class KeyWirePairH(KeyWirePair):
  """A KeyWirePair that is used as the high end of a range query.
  
  This KeyWirePair is larger than all other KeyWirePairs with the same key."""
  def __init__(self, key):
    self.key = key
    self.wire = None
    # HACK(pwnall): assuming 1 billion objects won't fit into RAM.
    self.wire_id = 1000000000

class CrossVerifier(object):
  """Checks whether a wire network has any crossing wires."""
  
  def __init__(self, layer):
    """Verifier for a layer of wires.
    
    Once created, the verifier can list the crossings between wires (the 
    wire_crossings method) or count the crossings (count_crossings)."""

    self.events = []
    self._events_from_layer(layer)
    self.events.sort()
  
    self.index = RangeIndex()
    self.result_set = ResultSet()
    self.performed = False
  
  def count_crossings(self):
    """Returns the number of pairs of wires that cross each other."""
    if self.performed:
      raise 
    self.performed = True
    return self._compute_crossings(True)

  def wire_crossings(self):
    """An array of pairs of wires that cross each other."""
    if self.performed:
      raise 
    self.performed = True
    return self._compute_crossings(False)

  def _events_from_layer(self, layer):
    """Populates the sweep line events from the wire layer."""
    for wire in layer.wires.values():
      if wire.is_horizontal():
        self.events.append([wire.x1, 0, wire.object_id, 'add', wire])
        self.events.append([wire.x2,3,wire.object_id, 'delete', wire])
      else: 
        self.events.append([wire.x1, 1, wire.object_id, 'query', wire])

  def _compute_crossings(self, count_only):
    """Implements count_crossings and wire_crossings."""
    if count_only:
      result = 0
    else:
      result = self.result_set
    for event in self.events:
      event_x, event_type, wire = event[0], event[3], event[4]
      
      if event_type == 'add':
        self.trace_sweep_line(event_x)
        self.index.add(KeyWirePair(wire.y1, wire))

      elif event_type == 'query':
        self.trace_sweep_line(event_x)
        if count_only:
          result += self.index.count(KeyWirePairL(wire.y1),
                                   KeyWirePairH(wire.y2))
        else:
          cross_wires=self.index.list(KeyWirePairL(wire.y1),
                                   KeyWirePairH(wire.y2))
          for cross_wire in cross_wires:
            result.add_crossing(wire, cross_wire.wire)
      elif event_type=='delete':
          self.trace_sweep_line(event_x)
          self.index.remove(KeyWirePair(wire.y1, wire))
          
    return result
  
  def trace_sweep_line(self, x):
    """When tracing is enabled, adds info about where the sweep line is.
    
    Args:
      x: the coordinate of the vertical sweep line
    """
    # NOTE: this is overridden in TracedCrossVerifier
    pass

class TracedCrossVerifier(CrossVerifier):
  """Augments CrossVerifier to build a trace for the visualizer."""
  
  def __init__(self, layer):
    CrossVerifier.__init__(self, layer)
    self.trace = []
    self.index = TracedRangeIndex(self.trace)
    self.result_set = TracedResultSet(self.trace)
    
  def trace_sweep_line(self, x):
    self.trace.append({'type': 'sweep', 'x': x})
    
  def trace_as_json(self):
    """List that obeys the JSON format restrictions with the verifier trace."""
    return self.trace

# Command-line controller.
if __name__ == '__main__':
    import sys
    layer = WireLayer.from_file(sys.stdin)
    verifier = CrossVerifier(layer)
    
    if os.environ.get('TRACE') == 'jsonp':
      verifier = TracedCrossVerifier(layer)
      result = verifier.wire_crossings()
      json_obj = {'layer': layer.as_json(), 'trace': verifier.trace_as_json()}
      sys.stdout.write('onJsonp(')
      json.dump(json_obj, sys.stdout)
      sys.stdout.write(');\n')
    elif os.environ.get('TRACE') == 'list':
      verifier.wire_crossings().write_to_file(sys.stdout)
    else:
      sys.stdout.write(str(verifier.count_crossings()) + "\n")