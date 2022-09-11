from distutils.core import setup

setup(
      name='src_py',
      version='1.0',
      description='Beanstalk Analytics python backend and tooling.',
      author='TBIQ',
      author_email='tbiq@bean.farm',
      packages=['notebooks', 'utils_notebook', 'utils_serverless']
)
