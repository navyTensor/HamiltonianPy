'''
Basics test.
'''

__all__=['test_basics']

def test_basics(arg):
    if arg in ('log','basics','all'):
        from HamiltonianPy.Basics.test.Log import test_log
        test_log()
    if arg in ('geometry','basics','all'):
        from HamiltonianPy.Basics.test.Geometry import test_geometry
        test_geometry()
    if arg in ('basespace','basics','all'):
        from HamiltonianPy.Basics.test.BaseSpace import test_basespace
        test_basespace()
    if arg in ('engineapp','basics','all'):
        from HamiltonianPy.Basics.test.EngineApp import test_engineapp
        test_engineapp()
    if arg in ('degfre','basics','all'):
        from HamiltonianPy.Basics.test.DegreeOfFreedom import test_deg_fre
        test_deg_fre()
    if arg in ('quantumnumber','basics','all'):
        from HamiltonianPy.Basics.QuantumNumber.test import test_quantum_number
        test_quantum_number()
    if arg in ('fdegfre','fermionic','basics','all'):
        from HamiltonianPy.Basics.FermionicPackage.test.DegreeOfFreedom import test_fermionic_deg_fre
        test_fermionic_deg_fre()
    if arg in ('foperator','fermionic','basics','all'):
        from HamiltonianPy.Basics.FermionicPackage.test.Operator import test_foperator
        test_foperator()
    if arg in ('fterm','fermionic','basics','all'):
        from HamiltonianPy.Basics.FermionicPackage.test.Term import test_fermionic_term
        test_fermionic_term()
    if arg in ('fbasis','fermionic','basics','all'):
        from HamiltonianPy.Basics.FermionicPackage.test.Basis import test_fbasis
        test_fbasis()
    if arg in ('foptrep','fermionic','basics','all'):
        from HamiltonianPy.Basics.FermionicPackage.test.OperatorRepresentation import test_foptrep
        test_foptrep()
    if arg in ('sdegfre','spin','basics','all'):
        from HamiltonianPy.Basics.SpinPackage.test.DegreeOfFreedom import test_spin_deg_fre
        test_spin_deg_fre()
    if arg in ('soperator','spin','basics','all'):
        from HamiltonianPy.Basics.SpinPackage.test.Operator import test_soperator
        test_soperator()
    if arg in ('soptrep','spin','basics','all'):
        from HamiltonianPy.Basics.SpinPackage.test.OperatorRepresentation import test_soptrep
        test_soptrep()
    if arg in ('sterm','spin','basics','all'):
        from HamiltonianPy.Basics.SpinPackage.test.Term import test_spin_term
        test_spin_term()
    if arg in ('lattice','database','basics','all'):
        from HamiltonianPy.Basics.DataBase.test.LatticePack import test_database_lattice
        test_database_lattice()
    if arg in ('kspace','database','basics','all'):
        from HamiltonianPy.Basics.DataBase.test.KSpacePack import test_database_kspace
        test_database_kspace()
