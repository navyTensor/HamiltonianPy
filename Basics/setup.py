def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config=Configuration('Basics',parent_package,top_path)
    config.add_subpackage('QuantumNumber')
    config.add_subpackage('FermionicPackage')
    config.add_subpackage('SpinPackage')
    config.add_subpackage('Extensions')
    config.add_subpackage('test')
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(configuration=configuration)
