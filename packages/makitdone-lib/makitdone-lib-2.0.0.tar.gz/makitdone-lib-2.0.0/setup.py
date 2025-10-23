from setuptools import setup

setup(
    name='makitdone-lib',
    version='2.0.0',
    packages=[
        'makit.lib',
    ],
    namespace_package=['makit', 'makit.lib'],
    install_requires=[
        'setuptools',
        'psutil',
    ],
    python_requires='>=3.3',
    url='https://gitee.com/makitdone/makitdone-lib',
    license='MIT',
    author='liangchao',
    author_email='liang20201101@163.com',
    description='python基础库扩展'
)
