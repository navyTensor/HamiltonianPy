'''
====================
Matrix product state
====================

Matrix product states, including:
    * classes: MPS
'''

__all__=['MPS']

import numpy as np
from numpy.linalg import norm
from HamiltonianPy import Arithmetic
from HamiltonianPy import QuantumNumber as QN
from HamiltonianPy import QuantumNumbers as QNS
from HamiltonianPy.Misc import TOL
from HamiltonianPy.TensorNetwork.Tensor import *
from copy import copy

class MPS(Arithmetic,list):
    '''
    The general matrix product state, with each of its elements being a 3d tensor.

    Attributes
    ----------
    mode : 'NB' or 'QN'
        'NB' for not using good quantum number;
        'QN' for using good quantum number.
    Lambda : DTensor
        The Lambda matrix (singular values) on the connecting link.
    cut : int
        The index of the connecting link.

    Notes
    -----
    The left-canonical MPS, right-canonical MPS and mixed-canonical MPS are considered as special cases of this form.
    '''
    L,S,R=0,1,2

    def __init__(self,mode='NB',ms=(),Lambda=None,cut=None,sites=None,bonds=None):
        '''
        Constructor.

        Parameters
        ----------
        mode : 'NB' or 'QN', optional
            'NB' for not using good quantum number;
            'QN' for using good quantum number.
        ms : list of 3d DTensor/STensor/ndarray, optional
            The matrices.
        Lambda : 1d ndarray/DTensor, optional
            The Lambda matrix (singular values) on the connecting bond.
        cut : int, optional
            The position of the connecting bond.
        sites : list of Label, optional
            The labels for the physical legs.
        bonds : list of Label, optional
            The labels for the virtual legs.
        '''
        assert mode in ('QN','NB') and (Lambda is None)==(cut is None) and (sites is None)==(bonds is None)
        self.mode=mode
        if Lambda is None:
            self.Lambda=None
            self.cut=None
        else:
            assert 0<=cut<=len(ms)
        if sites is None:
            for i,m in enumerate(ms):
                assert (isinstance(m,DTensor) or isinstance(m,STensor)) and m.ndim==3
                self.append(m)
            if Lambda is not None:
                assert isinstance(Lambda,DTensor)
                self.Lambda=Lambda
                self.cut=cut
        else:
            assert len(ms)==len(sites)==len(bonds)-1
            for i in xrange(len(ms)):
                assert ms[i].ndim==3
                if mode=='QN':
                    L,S,R=bonds[i].replace(flow=+1),sites[i].replace(flow=+1),bonds[i+1].replace(flow=-1)
                else:
                    L,S,R=bonds[i].replace(qns=ms[i].shape[MPS.L],flow=0),sites[i].replace(qns=ms[i].shape[MPS.S],flow=0),bonds[i+1].replace(qns=ms[i].shape[MPS.R],flow=0)
                self.append(DTensor(ms[i],labels=[L,S,R]))
            if Lambda is not None:
                self.Lambda=DTensor(Lambda,labels=([bonds[cut].replace(flow=None) if mode=='QN' else bonds[cut].replace(qns=len(Lambda),flow=None)]))
                self.cut=cut

    @property
    def table(self):
        '''
        The table of the mps.

        Returns
        -------
        dict
            For each of its (key,value) pair,
                * key: Label
                    The site label of each matrix in the mps.
                * value: int
                    The index of the corresponding matrix in the mps.
        '''
        return {m.labels[MPS.S]:i for i,m in enumerate(self)}

    @property
    def As(self):
        '''
        The A matrices.
        '''
        return self[0:self.cut]

    @property
    def Bs(self):
        '''
        The B matrices.
        '''
        return self[self.cut:self.nsite]

    @property
    def state(self):
        '''
        Convert to the normal representation.

        Returns
        -------
        result : ndarray
            * When `self` is a pure state, `result` is 1d.
            * When `self` is a mixed state, `result` is 2d with the rows being the pure states.
        '''
        L,R=self[0].labels[MPS.L],self[-1].labels[MPS.R]
        assert L.dim==1 or R.dim==1
        result=(np.product(self) if self.cut is None else np.product(self.As+[self.Lambda]+self.Bs)).data
        if L.dim==1 and R.dim==1:
            return result.reshape((-1,))
        elif L.dim==1:
            return result.reshape((-1,R.dim)).T
        else:
            return result.reshape((L.dim,-1))

    @property
    def nmax(self):
        '''
        The maximum bond dimension of the mps.
        '''
        return max(bond.dim for bond in self.bonds) if self.nsite>0 else None

    @property
    def nsite(self):
        '''
        The number of total sites.
        '''
        return len(self)

    @property
    def norm(self):
        '''
        The norm of the matrix product state.
        '''
        temp=copy(self)
        temp.reset(cut=0)
        temp>>=temp.nsite
        return temp.Lambda.data

    @property
    def sites(self):
        '''
        The site labels of the mps.
        '''
        return [m.labels[MPS.S].replace(flow=None) for m in self]

    @property
    def bonds(self):
        '''
        The bond labels of the mps.
        '''
        result=[]
        for i,m in enumerate(self):
            if i==0: result.append(m.labels[MPS.L].replace(flow=None))
            result.append(m.labels[MPS.R].replace(flow=None))
        return result

    @property
    def dagger(self):
        '''
        The dagger of the mps.
        '''
        return MPS(mode=self.mode,ms=[m.dagger for m in self],Lambda=None if self.Lambda is None else self.Lambda.dagger,cut=self.cut)

    @staticmethod
    def from_state(state,sites,bonds,cut=0,nmax=None,tol=None):
        '''
        Convert the normal representation of a state to the matrix product representation.

        Parameters
        ----------
        state : 1d ndarray
            The normal representation of a state.
        sites : list of Label
            The labels for the physical legs.
        bonds : list of Label
            The labels for the virtual legs.
        cut : int, optional
            The index of the connecting link.
        nmax : int, optional
            The maximum number of singular values to be kept.
        tol : np.float64, optional
            The tolerance of the singular values.

        Returns
        -------
        MPS
            The corresponding mixed-canonical mps.
        '''
        assert state.ndim==1 and len(sites)+1==len(bonds)
        qnon=next(iter(bonds)).qnon
        L=Label('__MPS_from_state_L__',bonds[+0].qns,flow=+1 if qnon else 0)
        S=Label.union(sites,'__MPS_from_state_S__',flow=+1 if qnon else 0,mode=0)
        R=Label('__MPS_from_state_R__',bonds[-1].qns,flow=-1 if qnon else 0)
        m=DTensor(state.reshape((1,-1,1)),labels=[L,S,R])
        if cut==0:
            u,s,ms=expanded_svd(m,L=[L],S=S,R=[R],E=sites,I=bonds[:-1],nmax=nmax,tol=tol,cut=0)
            Lambda=DTensor((u*(s,'ftensordot')).data.reshape((-1,)),labels=[bonds[0].replace(flow=None)])
            ms[-1].relabel(olds=[R],news=[bonds[-1].replace(flow=-1 if qnon else 0)])
        elif cut==len(sites):
            ms,s,v=expanded_svd(m,L=[L],S=S,R=[R],E=sites,I=bonds[1:],nmax=nmax,tol=tol,cut=len(sites))
            Lambda=DTensor(((s,'ftensordot')*v).data.reshape((-1,)),labels=[bonds[-1].replace(flow=None)])
            ms[0].relabel(olds=[L],news=[bonds[0].replace(flow=+1 if qnon else 0)])
        else:
            ms,Lambda=expanded_svd(m,L=[L],S=S,R=[R],E=sites,I=bonds[1:-1],nmax=nmax,tol=tol,cut=cut)
            ms[+0].relabel(olds=[L],news=[bonds[+0].replace(flow=+1 if qnon else 0)])
            ms[-1].relabel(olds=[R],news=[bonds[-1].replace(flow=-1 if qnon else 0)])
        return MPS(mode='QN' if qnon else 'NB',ms=ms,Lambda=Lambda,cut=cut)

    @staticmethod
    def productstate(ms,sites,bonds):
        '''
        Generate a product state.

        Parameters
        ----------
        ms : list of 1d ndarray
            The matrices of the product state.
        sites : list of Label
            The site labels of the product state.
        bonds : list of Label
            The bond labels of the product state.

        Returns
        -------
        MPS
            The corresponding product state.
        '''
        assert len(ms)==len(sites)==len(bonds)-1
        for i in xrange(len(ms)):
            S=sites[i]
            L,R=bonds[i].replace(qns=1) if i>0 else copy(bonds[i]),bonds[i+1].replace(qns=1)
            ms[i]=DTensor(ms[i].reshape(1,S.dim,1),labels=[L,S,R])
            if S.qnon: ms[i].qngenerate(flow=-1,axes=[0,1],qnses=[ms[i-1].labels[MPS.R].qns if i>0 else L.qns,S.qns],flows=[1,1])
        return MPS(mode='QN' if S.qnon else 'NB',ms=ms)

    @staticmethod
    def random(sites,bonds=None,cut=None,nmax=None,dtype=np.float64):
        '''
        Generate a random mps.

        Parameters
        ----------
        sites : list of Label/int/QuantumNumbers
            The labels/number-of-degrees-of-freedom/quantum-numbers of the physical legs.
        bonds : optional
            * list of Label
                The labels of the virtual legs.
            * 2-list of QuantumNumber
                The quantum number of the first and last virtual legs.
        cut : int, optional
            The index of the connecting link.
        nmax : int, optional
            The maximum number of singular values to be kept.
        dtype : np.float64, np.complex128, optional
            The data type of the random mps.

        Returns
        -------
        MPS
            The random mixed-canonical mps.
        '''
        np.random.seed()
        sites=[site if isinstance(site,Label) else Label('__MPS_RANDOM_S_%s__'%i,qns=site) for i,site in enumerate(sites)]
        if bonds is not None and all(isinstance(bond,Label) for bond in bonds):
            assert len(bonds)==len(sites)+1
        else:
            if bonds is not None: assert len(bonds)==2 and isinstance(bonds[0],QN) and isinstance(bonds[1],QN)
            iqns,oqns=(QNS.mono(bonds[0]),QNS.mono(bonds[1])) if bonds is not None else (1,1)
            bonds=[Label('__MPS_RANDOM_B_%s__'%i,qns=iqns if i==0 else oqns if i==len(sites) else None) for i in xrange(len(sites)+1)]
        mode,shape='QN' if next(iter(sites)).qnon else 'NB',tuple([site.dim for site in sites])
        if mode=='QN':
            result=0
            if dtype in (np.float32,np.float64):
                coeffs=np.random.random(nmax)
            else:
                coeffs=np.random.random(nmax)+1j*np.random.random(nmax)
            for k,indices in enumerate(QNS.decomposition([site.qns for site in sites],bonds[-1].qns[0]-bonds[0].qns[0],method='monte carlo',nmax=nmax)):
                ms=[np.array([1.0 if i==index else 0.0 for i in xrange(site.dim)],dtype=dtype) for site,index in zip(sites,indices)]
                result+=MPS.productstate(ms,sites,copy(bonds))*coeffs[k]
        else:
            ms=[]
            for i in xrange(len(sites)):
                if dtype in (np.float32,np.float64):
                    ms.append(np.random.random((nmax,shape[i],nmax)))
                else:
                    ms.append(np.random.random((nmax,shape[i],nmax))+1j*np.random.random((nmax,shape[i],nmax)))
            result=MPS(mode=mode,ms=ms,sites=sites,bonds=bonds)
        if cut is None:
            result.canonicalize(cut=len(sites)/2,nmax=nmax)
            result._merge_ABL_()
        else:
            result.canonicalize(cut=cut,nmax=nmax)
        return result

    @staticmethod
    def concatenate(mpses,mode=None,cut=None):
        '''
        Concatenate several mpses into one.

        Parameters
        ----------
        mpses : list of MPS
            The mpses to be concatenated.
        mode : 'QN' or 'NB', optional
            The mode of the result. Only when ``len(mpses)==0`` will it be considered.
        cut : int, optional
            The position of the connecting bond after the canonicalization.

        Returns
        -------
        MPS
            The result.
        '''
        if len(mpses)==0:
            result=MPS(mode=mode)
        else:
            modes=np.array([mps.mode=='QN' for mps in mpses])
            assert all(modes) or all(~modes)
            result=copy(mpses[0])
            result.reset(cut=None)
            for mps in mpses[1:]:
                assert result[-1].labels[MPS.R]==mps[0].labels[MPS.L]
                m,Lambda=mps._merge_ABL_()
                result.extend(mps)
                mps._set_ABL_(m,Lambda)
            if cut is not None: result.canonicalize(cut=cut)
        return result

    @staticmethod
    def overlap(mps1,mps2):
        '''
        The overlap between two mps.

        Parameters
        ----------
        mps1,mps2 : MPS
            The MPS between which the overlap is calculated.

        Returns
        -------
        number
            The overlap.
        '''
        assert mps1.nsite>0 and mps2.nsite>0
        result=1.0
        mps1=copy(mps1)
        mps2=mps2.dagger
        mps1.reset(cut=None)
        mps2.reset(cut=None)
        for i,(m1,m2) in enumerate(zip(mps1,mps2)):
            L,S,R=m2.labels[MPS.L],m2.labels[MPS.S],m2.labels[MPS.R]
            m2.relabel(olds=[S],news=[S.replace(prime=not S.prime)])
            if i==0: m2.relabel(olds=[L],news=[L.replace(prime=not L.prime)])
            if i==mps1.nsite-1: m2.relabel(olds=[R],news=[R.replace(prime=not R.prime)])
            result=result*m1*m2
        assert result.ndim==0
        return result.data

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        result=['L: %s\nS: %s\nR: %s\ndata:\n%s'%(m.labels[MPS.L],m.labels[MPS.S],m.labels[MPS.R],m.data) for m in self]
        if self.Lambda is not None:
            result.insert(self.cut,'Lambda: %s\ndata:\n%s'%(self.Lambda.labels[0],self.Lambda.data))
        return '\n'.join(result)

    def __repr__(self):
        '''
        Convert an instance to string.
        '''
        result=[str(m) for m in self]
        if self.Lambda is not None:
            result.insert(self.cut,'Lambda: %s'%self.Lambda)
        return '\n'.join(result)

    def __ilshift__(self,other):
        '''
        Operator "<<=", which shift the connecting link leftward by a non-negative integer.

        Parameters
        ----------
        other : int or 3-tuple
            * int
                The number of times that ``self.cut`` will be moved leftward.
            * 3-tuple in the form (k,nmax,tol)
                * k: int
                    The number of times that ``self.cut`` will be moved leftward.
                * nmax: int
                    The maximum number of singular values to be kept.
                * tol: np.float64
                    The truncation tolerance.
        '''

        k,nmax,tol=other if isinstance(other,tuple) else (other,None,None)
        if k>=0:
            for i in xrange(k):
                self._set_B_and_lmove_(self[self.cut-1]*self.Lambda,nmax,tol)
        else:
            for i in xrange(-k):
                self._set_A_and_rmove_(self.Lambda*self[self.cut],nmax,tol)
        return self

    def __lshift__(self,other):
        '''
        Operator "<<".

        Parameters
        ----------
        other : int or 3-tuple.
            Please see MPS.__ilshift__ for details.
        '''
        return copy(self).__ilshift__(other)

    def __irshift__(self,other):
        '''
        Operator ">>=", which shift the connecting link rightward by a non-negative integer.

        Parameters
        ----------
        other: int or 3-tuple
            * int
                The number of times that ``self.cut`` will be moved rightward.
            * 3-tuple in the form (k,nmax,tol)
                * k: int
                    The number of times that ``self.cut`` will be moved rightward.
                * nmax: int
                    The maximum number of singular values to be kept.
                * tol: np.float64
                    The truncation tolerance.
        '''
        return self.__ilshift__((-other[0],other[1],other[2]) if isinstance(other,tuple) else -other)

    def __rshift__(self,other):
        '''
        Operator ">>".

        Parameters
        ----------
        other : integer or 3-tuple.
            Please see MPS.__irshift__ for details.
        '''
        return copy(self).__irshift__(other)

    def __add__(self,other):
        '''
        Overloaded addition(+) operator, which supports the addition of two mpses.
        '''
        if isinstance(other,MPS):
            assert self.mode==other.mode and self.nsite==other.nsite
            if self is other:
                u,Lambda=self._merge_ABL_()
            else:
                u1,Lambda1=self._merge_ABL_()
                u2,Lambda2=other._merge_ABL_()
            mode,ms=self.mode,[]
            for i,(m1,m2) in enumerate(zip(self,other)):
                assert m1.labels==m2.labels
                labels=[label.replace(qns=None) for label in m1.labels]
                axes=[MPS.L,MPS.S] if i==0 else ([MPS.S,MPS.R] if i==self.nsite-1 else [MPS.S])
                ms.append(directsum([m1,m2],labels=labels,axes=axes))
            if self is other:
                self._set_ABL_(u,Lambda)
            else:
                self._set_ABL_(u1,Lambda1)
                other._set_ABL_(u2,Lambda2)
            return MPS(mode=mode,ms=ms)
        else:
            assert norm(other)==0
            return self

    __iadd__=__add__

    def __imul__(self,other):
        '''
        Overloaded self-multiplication(*=) operator, which supports the self-multiplication by a scalar.
        '''
        if self.Lambda is None:
            self[0]*=other
        else:
            self.Lambda*=other
        return self

    def __mul__(self,other):
        '''
        Overloaded multiplication(*) operator, which supports the multiplication of an mps with a scalar.
        '''
        result=copy(self)
        if result.Lambda is None:
            result[0]=result[0]*other
        else:
            result.Lambda=result.Lambda*other
        return result

    def relabel(self,sites,bonds):
        '''
        Change the labels of the mps.

        Parameters
        ----------
        sites : list of Label
            The new site labels of the mps.
        bonds : list of Label
            The new bond labels of the mps.
        '''
        assert len(sites)==self.nsite==len(bonds)-1
        fin,fout=(1,-1) if self.mode=='QN' else (0,0)
        for m,L,S,R in zip(self,bonds[:-1],sites,bonds[1:]):
            m.relabel(news=[L.replace(flow=fin),S.replace(flow=fin),R.replace(flow=fout)])
        if self.Lambda is not None:
            self.Lambda.relabel(news=[bonds[self.cut].replace(flow=None)])

    def is_canonical(self):
        '''
        Judge whether each site of the MPS is in the canonical form.
        '''
        result=[]
        for i,M in enumerate(self):
            temp=[M.take(index=j,axis=self.S).data for j in xrange(M.shape[self.S])]
            buff=None
            for matrix in temp:
                if buff is None:
                    buff=matrix.T.conjugate().dot(matrix) if i<self.cut else matrix.dot(matrix.T.conjugate())
                else:
                    buff+=matrix.T.conjugate().dot(matrix) if i<self.cut else matrix.dot(matrix.T.conjugate())
            result.append((np.abs(buff-np.identity(M.shape[MPS.R if i<self.cut else MPS.L]))<TOL).all())
        return result

    def canonicalize(self,cut=0,nmax=None,tol=None):
        '''
        Canonicalize an mps by svd.

        Parameters
        ----------
        cut : int, optional
            The position of the connecting bond after the canonicalization.
        nmax : int, optional
            The maximum number of singular values to be kept.
        tol : np.float64, optional
            The tolerance of the singular values.
        '''
        if cut<=self.nsite/2:
            self.reset(cut=self.nsite)
            self<<=(self.nsite,nmax,tol)
            self>>=(cut,nmax,tol)
        else:
            self.reset(cut=0)
            self>>=(self.nsite,nmax,tol)
            self<<=(self.nsite-cut,nmax,tol)

    def compress(self,nsweep=1,cut=0,nmax=None,tol=None):
        '''
        Compress an mps by svd.

        Parameters
        ----------
        nsweep : int, optional
            The number of sweeps to compress the mps.
        cut : int, optional
            The position of the connecting bond after the compression.
        nmax : int, optional
            The maximum number of singular values to be kept.
        tol : np.float64, optional
            The tolerance of the singular values.
        '''
        for sweep in xrange(nsweep):
            self.canonicalize(cut=cut,nmax=nmax,tol=tol)

    def reset(self,cut=None):
        '''
        Reset the position of the connecting bond of the mps.

        Parameters
        ----------
        cut : None or int, optional
            The position of the new connecting bond.
        '''
        self._merge_ABL_()
        if cut is not None:
            if 0<=cut<=self.nsite:
                self.cut=cut
                self.Lambda=DTensor(1.0,labels=[])
            else:
                raise ValueError("MPS reset error: cut(%s) should be None or in the range [%s,%s]"%(cut,0,self.nsite))

    def _merge_ABL_(self,merge='R'):
        '''
        Merge the Lambda matrix on the connecting bond to its left or right neighbouring matrix.

        Parameters
        ----------
        merge : 'L','R', optional
            * When 'L', self.Lambda will be merged into its left neighbouring matrix;
            * When 'R', self.Lambda will be merged into its right neighbouring matrix.

        Returns
        -------
        m : 3d DTensor/STensor
            The original left/right neighbouring matrix.
        Lambda : 1d TensorF
            The original Lambda matrix.

        Notes
        -----
        * When ``self.cut==0``, the `Lambda` matrix will be merged with `self[0]` no matter what merge is, and
        * When ``self.cut==self.nsite``, the `Lambda` matrix will be merged with `self[-1]` no matter what merge is.
        '''
        if self.cut is not None:
            assert merge.upper() in ('L','R')
            merge='L' if self.cut==self.nsite else 'R' if self.cut==0 else merge.upper()
            if merge=='L':
                m,Lambda=self[self.cut-1],self.Lambda
                self[self.cut-1]=m*Lambda
            else:
                m,Lambda=self[self.cut],self.Lambda
                self[self.cut]=Lambda*m
            self.cut=None
            self.Lambda=None
        else:
            m,Lambda=None,None
        return m,Lambda

    def _set_ABL_(self,m,Lambda):
        '''
        Set the matrix at a certain position and the Lambda of an mps.

        Parameters
        ----------
        m : DTensor/STensor
            The matrix at a certain position of the mps.
        Lambda : DTensor
            The singular values at the connecting link of the mps.
        '''
        if (isinstance(m,DTensor) or isinstance(m,STensor))and isinstance(Lambda,DTensor):
            assert m.ndim==3 and Lambda.ndim==1
            L,S,R=m.labels[MPS.L],m.labels[MPS.S],m.labels[MPS.R]
            pos=self.table[S]
            self[pos]=m
            self.Lambda=Lambda
            if Lambda.labels[0]==L:
                self.cut=pos
            elif Lambda.labels[0]==R:
                self.cut=pos+1
            else:
                raise ValueError("MPS _set_ABL_ error: the labels of m(%s) and Lambda(%s) do not match."%(m.labels,Lambda.labels))

    def _set_B_and_lmove_(self,M,nmax=None,tol=None):
        '''
        Set the B matrix at self.cut and move leftward.

        Parameters
        ----------
        M : DTensor/STensor
            The tensor used to set the B matrix.
        nmax : int, optional
            The maximum number of singular values to be kept. 
        tol : np.float64, optional
            The truncation tolerance.
        '''
        if self.cut==0: raise ValueError('MPS _set_B_and_lmove_ error: the cut is already zero.')
        L,S,R=M.labels[MPS.L],M.labels[MPS.S],M.labels[MPS.R]
        u,s,v,err=svd(M,row=[L],new=Label('__MPS_set_B_and_lmove__',None,None),col=[S,R],nmax=nmax,tol=tol,return_truncation_err=True)
        v.relabel(olds=[0],news=[v.labels[0].replace(identifier=L.identifier)])
        self[self.cut-1]=v
        if self.cut==1:
            self.Lambda=u*(s,'ftensordot')
            self.Lambda.relabel(news=[self.Lambda.labels[0].replace(flow=None)])
        else:
            self[self.cut-2]=self[self.cut-2]*u
            self[self.cut-2].relabel(olds=[2],news=[self[self.cut-2].labels[2].replace(identifier=L.identifier)])
            s.relabel(news=[s.labels[0].replace(identifier=L.identifier)])
            self.Lambda=s
        self.cut=self.cut-1

    def _set_A_and_rmove_(self,M,nmax=None,tol=None):
        '''
        Set the A matrix at self.cut and move rightward.

        Parameters
        ----------
        M : DTensor/STensor
            The tensor used to set the A matrix.
        nmax : int, optional
            The maximum number of singular values to be kept. 
        tol : np.float64, optional
            The truncation tolerance.
        '''
        if self.cut==self.nsite: raise ValueError('MPS _set_A_and_rmove_ error: the cut is already maximum.')
        L,S,R=M.labels[MPS.L],M.labels[MPS.S],M.labels[MPS.R]
        u,s,v,err=svd(M,row=[L,S],new=Label('__MPS_set_A_and_rmove__',None,None),col=[R],nmax=nmax,tol=tol,return_truncation_err=True)
        u.relabel(olds=[2],news=[u.labels[2].replace(identifier=R.identifier)])
        self[self.cut]=u
        if self.cut==self.nsite-1:
            self.Lambda=(s,'ftensordot')*v
            self.Lambda.relabel(news=[self.Lambda.labels[0].replace(flow=None)])
        else:
            self[self.cut+1]=v*self[self.cut+1]
            self[self.cut+1].relabel(olds=[0],news=[self[self.cut+1].labels[0].replace(identifier=R.identifier)])
            s.relabel(news=[s.labels[0].replace(identifier=R.identifier)])
            self.Lambda=s
        self.cut=self.cut+1

    def relayer(self,degfres,layer,nmax=None,tol=None):
        '''
        Construct a new mps with the physical indices confined on a specific layer of degfres.

        Parameters
        ----------
        degfres : DegFreTree
            The tree of the physical degrees of freedom.
        layer : int/tuple-of-string
            The layer where the physical indices are confined.
        nmax : int, optional
            The maximum number of singular values to be kept.
        tol : np.float64, optional
            The tolerance of the singular values.

        Returns
        -------
        MPS
            The new mps.
        '''
        new=layer if type(layer) in (int,long) else degfres.layers.index(layer)
        assert 0<=new<len(degfres.layers)
        old=degfres.level(next(iter(self)).labels[MPS.S].identifier)-1
        if new==old:
            return copy(self)
        else:
            t,svs=self._merge_ABL_()
            olayer,nlayer=degfres.layers[old],degfres.layers[new]
            sites,bonds=[site.replace(flow=1 if self.mode=='QN' else 0) for site in degfres.labels('S',nlayer)],degfres.labels('B',nlayer)
            Ms=[]
            if new<old:
                table=degfres.table(olayer)
                for i,site in enumerate(sites):
                    M=np.product([self[table[index]] for index in degfres.descendants(site.identifier,generation=old-new)])
                    o1,o2=M.labels[0],M.labels[-1]
                    n1,n2=bonds[i].replace(qns=o1.qns,flow=o1.flow),bonds[i+1].replace(qns=o2.qns,flow=o2.flow)
                    M.relabel(olds=[o1,o2],news=[n1,n2])
                    Ms.append(M.merge((M.labels[1:-1],site)))
                Lambda,cut=None,None
            else:
                table=degfres.table(nlayer)
                for i,m in enumerate(self):
                    if i>0: m=s*v*m
                    L,S,R=m.labels
                    indices=degfres.descendants(S.identifier,generation=new-old)
                    start,stop=table[indices[0]],table[indices[-1]]+1
                    us,s,v=expanded_svd(m,L=[L],S=S,R=[R],E=sites[start:stop],I=bonds[start+1:stop+1],cut=stop-start,nmax=nmax,tol=tol)
                    Ms.extend(us)
                Lambda,cut=(s,'ftensordot')*v,len(Ms)
                Ms[0].relabel(olds=[MPS.L],news=[Ms[0].labels[MPS.L].replace(identifier=bonds[0].identifier)])
                Lambda.relabel(news=[Lambda.labels[0].replace(identifier=bonds[-1].identifier,flow=None)])
            self._set_ABL_(t,svs)
            return MPS(mode=self.mode,ms=Ms,Lambda=Lambda,cut=cut)
