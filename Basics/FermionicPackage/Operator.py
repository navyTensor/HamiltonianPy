'''
------------------
Fermionic operator
------------------

Fermionic operator, including:
    * classes: FOperator, FLinear, FQuadratic, FHubbard, FCoulomb
'''

__all__=['FOperator','FLinear','FQuadratic','FHubbard','FCoulomb']

from ..Operator import *
from ..Utilities import parity
from DegreeOfFreedom import ANNIHILATION,CREATION
import numpy as np

class FOperator(Operator):
    '''
    This class gives a unified description of fermionic operators with different ranks.

    Attributes
    ----------
    indices : tuple of Index
        The associated indices of the operator, whose length should be equal to the operator's rank.
    seqs : tuple of integer
        The associated sequences of the operator, whose length should be equal to the operator's rank.
    rcoord : 1d ndarray
        The associated real coordinates of the operator.
    icoord : 1d ndarray
        The associated lattice coordinates of the operator.
    '''

    def __init__(self,value,indices,seqs=None,rcoord=None,icoord=None):
        '''
        Constructor.

        Parameters
        ----------
        value : number
            The coefficient of the operator.
        indices : tuple of Index
            The associated indices of the operator.
        seqs : tuple of integer, optional
             The associated sequences of the operator.
        rcoord : 1d ndarray, optional
            The real coordinates of the operator.
        icoord : 1d ndarray, optional
            The lattice coordinates of the operator.
        '''
        super(FOperator,self).__init__(value)
        self.indices=tuple(indices)
        self.seqs=None if seqs is None else tuple(seqs)
        if self.seqs is not None: assert len(self.seqs)==len(self.indices)
        self.rcoord=None if rcoord is None else np.array(rcoord)
        self.icoord=None if icoord is None else np.array(icoord)

    def __repr__(self):
        '''
        Convert an instance to string.
        '''
        result=[]
        result.append('%s('%self.__class__.__name__)
        result.append('%s'%self.value)
        result.append(', %s'%(self.indices,))
        if self.seqs is not None: result.append(', seqs=%s'%(self.seqs,))
        if self.rcoord is not None: result.append(', rcoord=%s'%self.rcoord)
        if self.icoord is not None: result.append(', icoord=%s'%self.icoord)
        result.append(')')
        return ''.join(result)

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        result=[]
        result.append('%s('%self.__class__.__name__)
        result.append('value=%s'%self.value)
        result.append(', indices=(%s)'%(','.join(str(index) for index in self.indices)))
        if self.seqs is not None: result.append(', seqs=%s'%(self.seqs,))
        if self.rcoord is not None: result.append(', rcoord=%s'%self.rcoord)
        if self.icoord is not None: result.append(', icoord=%s'%self.icoord)
        result.append(')')
        return ''.join(result)

    @property
    def id(self):
        '''
        The unique id of this operator.
        '''
        return self.indices if self.rcoord is None else self.indices+tuple([round(f,6) for f in self.rcoord])

    @property
    def rank(self):
        '''
        Return the rank of the operator.
        '''
        return len(self.indices)

    def is_normal_ordered(self):
        '''
        Judge whether an operator is normal ordered.
        '''
        flag=True
        for index in self.indices:
            if index.nambu==ANNIHILATION: flag=False
            if not flag and index.nambu==CREATION: return False
        return True

    def is_Hermitian(self):
        '''
        Judge whether an operator is Hermitian.
        '''
        return self==self.dagger

    def reorder(self,permutation,reverse_coord=False):
        '''
        Return the reordered fermionic operator according to the permutation information.

        Parameters
        ----------
        permutation : list of int
            The permutation of the fermionic operator.
        reverse_coord : logical, optional
            True for reversing the rcoord and icoord of the operator and False for not.

        Returns
        -------
        FOperator
            The reordered operator.
        '''
        assert len(permutation)==self.rank
        result=FOperator.__new__(self.__class__)
        super(FOperator,result).__init__(self.value)
        result.indices=tuple(self.indices[i] for i in permutation)
        result.seqs=None if self.seqs is None else tuple(self.seqs[i] for i in permutation)
        result.rcoord=None if self.rcoord is None else (-1)**reverse_coord*self.rcoord
        result.icoord=None if self.icoord is None else (-1)**reverse_coord*self.icoord
        return result

class FLinear(FOperator):
    '''
    Linear fermionic operator.
    '''

    def __init__(self,value,index,seq=None,rcoord=None,icoord=None):
        '''
        Constructor.

        Parameters
        ----------
        value : number
            The coefficient of the linear operator.
        index : Index
            The index of the linear operator.
        seq : integer, optional
            The associated sequence of the linear operator.
        rcoord : 1d ndarray, optional
            The real coordinates of the operator.
        icoord : 1d ndarray, optional
            The lattice coordinates of the operator.
        '''
        super(FLinear,self).__init__(value,indices=(index,),seqs=None if seq is None else (seq,),rcoord=rcoord,icoord=icoord)

    @property
    def index(self):
        '''
        The index of the linear operator.
        '''
        return self.indices[0]

    @property
    def seq(self):
        '''
        The associated sequence of the linear operator.
        '''
        return None if self.seqs is None else self.seqs[0]

    @property
    def dagger(self):
        '''
        The Hermitian conjugate of the linear operator.
        '''
        return FLinear(
                value=      np.conjugate(self.value),
                index=      self.index.replace(nambu=1-self.index.nambu),
                seq=        self.seq,
                rcoord=     self.rcoord,
                icoord=     self.icoord
                )

class FQuadratic(FOperator):
    '''
    Quadratic fermionic operator.
    '''

    def __init__(self,value,indices,seqs=None,rcoord=None,icoord=None):
        '''
        Constructor. See FOperator.__init__ for details.
        '''
        assert len(indices)==2
        super(FQuadratic,self).__init__(value,indices,seqs=seqs,rcoord=rcoord,icoord=icoord)

    @property
    def dagger(self):
        '''
        The Hermitian conjugate of the quadratic operator.
        '''
        return FQuadratic(
                value=      np.conjugate(self.value),
                indices=    [index.replace(nambu=1-index.nambu) for index in reversed(self.indices)],
                seqs=       None if self.seqs is None else reversed(self.seqs),
                rcoord=     None if self.rcoord is None else -self.rcoord,
                icoord=     None if self.icoord is None else -self.icoord
                )

class FHubbard(FOperator):
    '''
    Fermionic Hubbard operator.
    '''

    def __init__(self,value,indices,seqs=None,rcoord=None,icoord=None):
        '''
        Constructor. See FOperator.__init__ for details.
        '''
        assert len(indices)==4
        super(FHubbard,self).__init__(value,indices,seqs=seqs,rcoord=rcoord,icoord=icoord)

    @property
    def dagger(self):
        '''
        The Hermitian conjugate of the Hubbard operator.
        '''
        return FHubbard(
                value=      np.conjugate(self.value),
                indices=    [index.replace(nambu=1-index.nambu) for index in reversed(self.indices)],
                seqs=       None if self.seqs is None else reversed(self.seqs),
                rcoord=     self.rcoord,
                icoord=     self.icoord
                )

class FCoulomb(FOperator):
    '''
    Fermionic density-density interaction operator.
    '''

    def __init__(self,value,indices,seqs=None,rcoord=None,icoord=None):
        '''
        Constructor. See FOperator.__init__ for details.
        '''
        assert len(indices)==4
        super(FCoulomb,self).__init__(value,indices,seqs=seqs,rcoord=rcoord,icoord=icoord)

    @property
    def dagger(self):
        '''
        The Hermitian conjugate of the density-density interaction operator.
        '''
        return FCoulomb(
                value=      np.conjugate(self.value),
                indices=    [index.replace(nambu=1-index.nambu) for index in reversed(self.indices)],
                seqs=       None if self.seqs is None else reversed(self.seqs),
                rcoord=     None if self.rcoord is None else -self.rcoord,
                icoord=     None if self.icoord is None else -self.icoord
        )
