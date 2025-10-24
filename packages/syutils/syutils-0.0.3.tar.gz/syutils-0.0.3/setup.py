from setuptools import setup, find_packages
setup(name='syutils',
      version='0.0.3',
      description='High frequency functions and class',
      url='https://gitee.com/wdy0401/syutils',
      author='wangdeyang',
      author_email='wdy0401@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
        # 依赖的库
        "trade_date",
        "py7zr",
    	],
      zip_safe=False)