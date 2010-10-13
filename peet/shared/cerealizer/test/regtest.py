# -*- coding: latin-1 -*-

# Cerealizer
# Copyright (C) 2005-2006 Jean-Baptiste LAMY
#
# This program is free software.
# It is available under the Python licence.

# Unit tests for Cerealizer

import cerealizer
import unittest


class TestBasicType(unittest.TestCase):
  def setUp(self):
    self.obj = [1, 2, "jiba"]
    
  def loads_dumps_and_compare(self, obj1):
    obj2 = cerealizer.loads(cerealizer.dumps(obj1))
    assert obj1 == obj2
    
  def test_int1    (self): self.loads_dumps_and_compare(7828)
  def test_int2    (self): self.loads_dumps_and_compare(-579)
  def test_float1  (self): self.loads_dumps_and_compare(4.9)
  def test_float2  (self): self.loads_dumps_and_compare(-0.0043)
  def test_float3  (self): self.loads_dumps_and_compare(4.0)
  def test_complex (self): self.loads_dumps_and_compare(1+2j)
  
  def test_string1 (self): self.loads_dumps_and_compare( "jiba")
  def test_string2 (self): self.loads_dumps_and_compare( "jibé")
  def test_unicode1(self): self.loads_dumps_and_compare(u"jiba")
  def test_unicode2(self): self.loads_dumps_and_compare(u"jibé")
  
  def test_tuple1   (self): self.loads_dumps_and_compare(())
  def test_tuple2   (self): self.loads_dumps_and_compare((1, 2.2, "jiba"))
  def test_tuple3   (self): self.loads_dumps_and_compare((1, (2.2, "jiba")))
  def test_frozenset(self): self.loads_dumps_and_compare(frozenset([1, (2.2, "jiba")]))
  def test_list1    (self): self.loads_dumps_and_compare([])
  def test_list2    (self): self.loads_dumps_and_compare([1, 2.2, "jiba"])
  def test_list3    (self): self.loads_dumps_and_compare([1, [2.2, "jiba"]])
  def test_set1     (self): self.loads_dumps_and_compare(set())
  def test_set2     (self): self.loads_dumps_and_compare(set([1, 2.2, "jiba"]))
  def test_dict1    (self): self.loads_dumps_and_compare({})
  def test_dict2    (self): self.loads_dumps_and_compare({ "jiba" : 100, "other" : 0 })
  def test_dict3    (self): self.loads_dumps_and_compare({ "jiba" : range(100), "other" : { 1:2 } })
  
  def test_None    (self): self.loads_dumps_and_compare(None)
  
  def test_obj_oldstyle(self):
    class Obj1:
      def __init__(self):
        self.x = 1
        self.name = "jiba"
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.__dict__ == b.__dict__)
    cerealizer.register(Obj1)
    self.loads_dumps_and_compare(Obj1())
    
  def test_obj_newstyle(self):
    class Obj2(object):
      def __init__(self):
        self.x = 1
        self.name = "jiba"
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.__dict__ == b.__dict__)
    cerealizer.register(Obj2)
    self.loads_dumps_and_compare(Obj2())
    
  def test_obj_setstate_priority1(self):
    LIST = [1, 2, 3]
    class Obj3(object):
      def __init__(self):
        self.x = 1
        self.name = "jiba"
        self.list = LIST[:]
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.__dict__ == b.__dict__)
      def __setstate__(self, state):
        assert state["list"] == LIST # Test that list is initialized BEFORE the object
        self.__dict__ = state
    cerealizer.register(Obj3)
    self.loads_dumps_and_compare(Obj3())
    
  def test_obj_setstate_priority2(self):
    TUPLE = (1, 2, 3, (4, (5, 6, (7,))))
    class Obj6(object):
      def __init__(self):
        self.x = 1
        self.name = "jiba"
        self.list = TUPLE[:]
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.__dict__ == b.__dict__)
      def __setstate__(self, state):
        assert state["list"] == TUPLE # Test that list is initialized BEFORE the object
        self.__dict__ = state
    cerealizer.register(Obj6)
    self.loads_dumps_and_compare(Obj6())
    
  def test_obj_getstate_setstate(self):
    STATE = (1, 2, "jiba")
    class Obj4(object):
      def __init__(self):
        self.x = 1
        self.name = "jiba"
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.__dict__ == b.__dict__)
      def __getstate__(self): return STATE
      def __setstate__(self, state):
        assert state == STATE
        self.x = 1
        self.name = "jiba"
    cerealizer.register(Obj4)
    self.loads_dumps_and_compare(Obj4())
    
  def test_obj_new_and_init(self):
    nbs = [0, 0]
    class Obj5(object):
      def __new__(Class):
        nbs[0] += 1
        return object.__new__(Class)
      def __init__(self):
        nbs[1] += 1
        self.x = 1
        self.name = "jiba"
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.__dict__ == b.__dict__)
    cerealizer.register(Obj5)
    o = Obj5()
    self.loads_dumps_and_compare(o)
    assert nbs == [2, 1]
    
  def test_identity(self):
    o  = {}
    l1 = [o, o]
    l2 = cerealizer.loads(cerealizer.dumps(l1))
    assert l2[0] is l2[1]
    
  def test_cycle1(self):
    obj1 = [1, [2.2, "jiba"]]
    obj1[1].append(obj1)
    obj2 = cerealizer.loads(cerealizer.dumps(obj1))
    assert repr(obj1) == repr(obj2) # Cannot use == on cyclic list!
    
  def test_cycle2(self):
    class Obj11(object):
      pass
    cerealizer.register(Obj11)
    o = Obj11()
    o.o = o
    o2 = cerealizer.loads(cerealizer.dumps(o))
    assert o2.o is o2
    
  def test_cycle3(self):
    class Parent: pass
    class Child:
      def __init__(self, parent): self.parent = parent
      def __getstate__(self): return (self.parent,)
      def __setstate__(self, state): self.parent = state[0]
    cerealizer.register(Parent)
    cerealizer.register(Child)
    
    p = Parent()
    p.c = Child(p)
    p2 = cerealizer.loads(cerealizer.dumps(p))
    assert not p2.c.parent is None
    
    
  def test_obj_slot(self):
    class Obj7(object):
      __slots__ = ["x", "name"]
      def __init__(self):
        self.x    = 11.1
        self.name = "jiba"
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.x == b.x) and (a.name == b.name)
    cerealizer.register(Obj7)
    o = Obj7()
    self.loads_dumps_and_compare(o)
    
  def test_obj_initargs1(self):
    class Obj8:
      def __init__(self, x, name):
        self.x    = x
        self.name = name
      def __getinitargs__(self): return self.x, self.name
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.x == b.x) and (a.name == b.name)
    cerealizer.register(Obj8)
    o = Obj8(45, u"uioef")
    self.loads_dumps_and_compare(o)
    
  def test_obj_initargs2(self):
    class Obj9(object):
      def __init__(self, x, name):
        self.x    = x
        self.name = name
      def __getinitargs__(self): return self.x, self.name
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.x == b.x) and (a.name == b.name)
    cerealizer.register(Obj9)
    o = Obj9(45, u"uioef")
    self.loads_dumps_and_compare(o)
    
  def test_obj_newargs1(self):
    class Obj10(object):
      def __new__(Class, x, name):
        self      = object.__new__(Class)
        self.x    = x
        self.name = name
        return self
      def __getnewargs__(self): return self.x, self.name
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.x == b.x) and (a.name == b.name)
    cerealizer.register(Obj10)
    o = Obj10(45, u"uioef")
    self.loads_dumps_and_compare(o)
    
  def test_obj_newargs2(self):
    class Obj12(object):
      def __new__(Class, x):
        self      = object.__new__(Class)
        self.x    = x
        return self
      def __getnewargs__(self): return (self.x,)
      def __eq__(a, b): return (a.__class__ is b.__class__) and (a.x == b.x)
    cerealizer.register(Obj12)
    o  = Obj12(45)
    o2 = Obj12(o)
    self.loads_dumps_and_compare(o2)
    
  def test_alias1(self):
    class OldObj(object):
      def __init__(self):
        self.x    = 1
        self.name = "jiba"
    cerealizer.register(OldObj)
    o = OldObj()
    s = cerealizer.dumps(o)
    
    reload(cerealizer)
    class NewObj(object):
      def __init__(self):
        self.x    = 2
        self.name = "jiba2"
    cerealizer.register(NewObj)
    cerealizer.register_alias(NewObj, "__main__.OldObj")
    o = cerealizer.loads(s)
    assert o.__class__ is NewObj
    assert o.x    == 1
    assert o.name == "jiba"
    
    
    
class TestSecurity(unittest.TestCase):
  def test_register1(self):
    class Sec1: pass
    self.assertRaises(cerealizer.NonCerealizableObjectError, lambda : cerealizer.dumps(Sec1()))
    
  def test_register2(self):
    class Sec2: pass
    cerealizer.register(Sec2)
    self.assertRaises(ValueError, lambda : cerealizer.register(Sec2))
    
  def test_register3(self):
    class Sec3: pass
    cerealizer.register(Sec3)
    class Sec3: pass
    self.assertRaises(ValueError, lambda : cerealizer.register(Sec3))
    
    
  def test_setstate_hacked(self):
    class Sec4: pass
    cerealizer.register(Sec4)
    o = Sec4()
    Sec4.__setstate__ = lambda obj, state: self.fail()
    cerealizer.loads(cerealizer.dumps(o))
    
  def test_getstate_hacked(self):
    class Sec5: pass
    cerealizer.register(Sec5)
    o = Sec5()
    Sec5.__getstate__ = lambda obj: self.fail()
    cerealizer.loads(cerealizer.dumps(o))
    
  def test_new_hacked(self):
    class Sec6: pass
    cerealizer.register(Sec6)
    o = Sec6()
    Sec6.__new__ = lambda Class: self.fail()
    cerealizer.loads(cerealizer.dumps(o))
    
    
  def test_craked_file1(self):
    craked_file = "cereal1\n2\n__builtin__.dict\nfile\n0\nr0\nr1\n"
    self.assertRaises(StandardError, lambda : cerealizer.loads(craked_file))
    

if __name__ == '__main__': unittest.main()
  
  
