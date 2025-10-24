from setuptools import setup
setup(
   name='Mynetica',
   version='1.0',
   packages=['Mynetica'],   #### 包的名称有问题
   # install_requires=[
   #     'dependency1',
   #     'dependency2',
   # ],
   # author='Your Name',
   # author_email='your.email@example.com',
   # description='A description of your package',
   # url='https://github.com/yourusername/MyPackage',
)



# name: 包名。
# version: 包的版本号。
# packages: 使用find_packages()自动查找所有的包。
# install_requires: 需要安装的依赖包列表。
# author: 作者名称。
# author_email: 作者的电子邮件。
# description: 包的简短描述。
# url: 项目的主页或源码存储库。