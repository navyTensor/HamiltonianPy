'''
Fermionic operator representation test.
'''

__all__=['test_foptrep']

from numpy import *
from HamiltonianPy.Basics import *
import itertools as it
import time

def test_foptrep():
    print 'test_foptrep'
    m,n=3,4
    lattice=Lattice(name="WG",rcoords=tiling([array([0.0,0.0])],vectors=[array([1.0,0.0]),array([0.0,1.0])],translations=it.product(xrange(m),xrange(n))))
    config=IDFConfig(priority=DEFAULT_FERMIONIC_PRIORITY,map=lambda pid:Fermi(atom=0,norbital=1,nspin=2,nnambu=2),pids=lattice.pids)
    generator=Generator(bonds=lattice.bonds,config=config,table=config.table(mask=[]),terms=[Hopping('t',1.0,neighbour=1,indexpacks=sigmaz("SP"))])
    operator=generator.operators.values()[0]
    print 'operator:',operator
    basises=[FBasis(up=(m*n,m*n/2),down=(m*n,m*n/2)),FBasis((2*m*n,m*n)),FBasis(nstate=2*m*n)]
    for basis in basises:
        stime=time.time()
        matrix=foptrep(operator,basis,transpose=False)
        etime=time.time()
        print '%s mode: shape=%s, nnz=%s, time=%ss.'%(basis.mode,matrix.shape,matrix.nnz,etime-stime)
    print
