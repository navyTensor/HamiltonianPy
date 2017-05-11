'''
=========================
Descriptions of operators
=========================

This modulate defines the way to describe an operator and a set of operators, including
    * classes: Operator, Operators.
'''

__all__=['Operator','Operators']

from Constant import *
from copy import copy
from numpy.linalg import norm

class Operator(object):
    '''
    This class is the base class of all types of operators.

    Attributes
    ----------
    value : number
        The overall factor of the operator.
    '''

    def __init__(self,value):
        '''
        Constructor.
        '''
        self.value=value

    @property
    def id(self):
        '''
        The unique id of this operator.

        Notes
        -----
        * Two operators with the same id can be combined.
        * This property must be overridden by its child class.
        '''
        raise ValueError("%s id error: it is not implemented."%self.__class__.__name__)

    def __pos__(self):
        '''
        Overloaded positive(+) operator.
        '''
        return self

    def __add__(self,other):
        '''
        Overloaded left addition(+) operator, which supports the left addition by an instance of Operator/Operators.
        '''
        if isinstance(other,Operator):
            result=Operators()
            sid,oid=self.id,other.id
            if sid==oid:
                value=self.value+other.value
                if abs(value)>RZERO:
                    temp=copy(self)
                    temp.value=value
                    result[sid]=temp
            else:
                result[sid]=self
                result[oid]=other
        elif isinstance(other,Operators):
            result=other.__add__(self)
        else:
            assert norm(other)==0
            result=self
        return result

    def __radd__(self,other):
        '''
        Overloaded right addition(+) operator, which supports the right addition by an instance of Operator/Operators.
        '''
        return self+other

    def __imul__(self,other):
        '''
        Overloaded self-multiplication(*=) operator, which supports the self multiplication by a scalar.
        '''
        self.value*=other
        return self

    def __mul__(self,other):
        '''
        Overloaded left multiplication(*) operator, which supports the left multiplication by a scalar.
        '''
        result=copy(self)
        result.value=result.value*other
        return result

    def __rmul__(self,other):
        '''
        Overloaded right multiplication(*) operator, which supports the right multiplication by a scalar.
        '''
        return self*other

    def __neg__(self):
        '''
        Overloaded negative(-) operator.
        '''
        return self*(-1)

    def __sub__(self,other):
        '''
        Overloaded left subtraction(-) operator, which supports the left subtraction by an instance of Operator/Operators.
        '''
        return self+other*(-1)

    def __idiv__(self,other):
        '''
        Overloaded self-division(/=) operator, which supports the self division by a scalar.
        '''
        return self.__imul__(1.0/other)

    def __div__(self,other):
        '''
        Overloaded left division(/) operator, which supports the left division by a scalar.
        '''
        return self*(1.0/other)

    def __eq__(self,other):
        '''
        Overloaded operator(==).
        '''
        return self.id==other.id and abs(self.value-other.value)<RZERO

class Operators(dict):
    '''
    This class packs several operators as a whole for convenience. For each of its (key,value) pairs:
        * key: any hashable object
            The id of an operator.
        * value: Operator
            The corresponding operator.
    '''

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        return '\n'.join(['[%s]:%s'%(i,obj) for i,obj in enumerate(self.values())])

    def __pos__(self):
        '''
        Overloaded positive(+) operator.
        '''
        return self

    def __iadd__(self,other):
        '''
        Overloaded self-addition(+=) operator, which supports the self addition by an instance of Operator/Operators.
        '''
        if isinstance(other,Operator):
            id=other.id
            if id in self:
                value=self[id].value+other.value
                if abs(value)>RZERO:
                    temp=copy(other)
                    temp.value=value
                    self[id]=temp
                else:
                    del self[id]
            else:
                self[id]=other
        elif isinstance(other,Operators):
            for obj in other.values():
                self.__iadd__(obj)
        else:
            assert norm(other)==0
        return self

    def __add__(self,other):
        '''
        Overloaded left addition(+) operator, which supports the left addition by an instance of Operator/Operators.
        '''
        return copy(self).__iadd__(other)

    def __radd__(self,other):
        '''
        Overloaded right addition(+) operator, which supports the right addition by an instance of Operator/Operators.
        '''
        return self+other

    def __imul__(self,other):
        '''
        Overloaded self-multiplication(*=) operator, which supports the self multiplication by a scalar.
        '''
        for obj in self.itervalues():
            obj*=other
        return self

    def __mul__(self,other):
        '''
        Overloaded left multiplication(*) operator, which supports the left multiplication by a scalar.
        '''
        result=Operators()
        for id,obj in self.iteritems():
            result[id]=obj*other
        return result

    def __rmul__(self,other):
        '''
        Overloaded right multiplication(*) operator, which supports the right multiplication by a scalar.
        '''
        return self.__mul__(other)

    def __neg__(self):
        '''
        Overloaded negative(-) operator.
        '''
        return self*(-1)

    def __isub__(self,other):
        '''
        Overloaded self-subtraction(-=) operator, which supports the self-subtraction by an instance of Operator/Operators.
        '''
        if isinstance(other,Operator):
            id=other.id
            if id in self:
                value=self[id].value-other.value
                if abs(value)>RZERO:
                    temp=copy(other)
                    temp.value=value
                    self[id]=temp
                else:
                    del self[id]
            else:
                temp=copy(other)
                temp.value*=-1
                self[id]=temp
        elif isinstance(other,Operators):
            for obj in other.values():
                self.__isub__(obj)
        else:
            assert norm(other)==0
        return self

    def __sub__(self,other):
        '''
        Overloaded left subtraction(-) operator, which supports the left subtraction by an instance of Operator/Operators.
        '''
        return self+other*(-1)
