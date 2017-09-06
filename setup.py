from setuptools import setup, find_packages

setup(name='qxpacker',
      version='0.1',
      description='Qxpacker - tool for packaging files and directories into cross-platform self-extracting single file.',
      url='https://github.com/TODOTomorrow/qxpacker',
      author='Alexander P',
      author_email='a.pokid@mail.ru',
      license='MIT',
      packages=find_packages(),
      zip_safe=True,
      keywords='packaging crossplatform',
      scripts = ['qxpacker/qxpacker'],
      include_package_data=True,
      data_files = [('./modules/',[
                    'qxpacker/modules/qxpacker.argparse.module',
                    'qxpacker/modules/qxpacker.array.module',
                    'qxpacker/modules/qxpacker.startup.script',
                    'qxpacker/modules/qxpacker.tmpfile.module',
                    'qxpacker/modules/qxpacker.toolchain.module',
                    'qxpacker/modules/qxpacker.base.module'])]
      )
