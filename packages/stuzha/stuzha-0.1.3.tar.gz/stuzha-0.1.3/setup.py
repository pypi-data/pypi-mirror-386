from setuptools import setup, find_packages

setup(
    name='stuzha',
    version='0.1.3',
    packages=find_packages(),
    install_requires=[
        'colorama>=0.4.6',
    ],
    entry_points={
        'console_scripts': [
            # CIS entry points
            'vp_1 = stuzha.CIS:vp_1',
            'vp_2 = stuzha.CIS:vp_2',
            'vp_3 = stuzha.CIS:vp_3',
            'vp_4 = stuzha.CIS:vp_4',
            'vp_5 = stuzha.CIS:vp_5',
            'vp_6 = stuzha.CIS:vp_6',
            'vp_7 = stuzha.CIS:vp_7',
            'vp_8 = stuzha.CIS:vp_8',
            'vp_9 = stuzha.CIS:vp_9',
            # AoA entry points
            'pk_1 = stuzha.AoA:pk_1',
            'pk_2 = stuzha.AoA:pk_2',
            'pk_3 = stuzha.AoA:pk_3',
            'pk_4 = stuzha.AoA:pk_4',
            'pk_5 = stuzha.AoA:pk_5',
            'pk_6 = stuzha.AoA:pk_6',
            'pk_7 = stuzha.AoA:pk_7',
            'pk_8 = stuzha.AoA:pk_8',
            'pk_9 = stuzha.AoA:pk_9',
            'pk_10 = stuzha.AoA:pk_10',
            # AMT entry points
            'amt_1 = stuzha.AMT:amt_1',
            'amt_2 = stuzha.AMT:amt_2',
            'amt_3 = stuzha.AMT:amt_3',
            'amt_4 = stuzha.AMT:amt_4',
            'amt_5 = stuzha.AMT:amt_5',
            'amt_6 = stuzha.AMT:amt_6',
            'amt_7 = stuzha.AMT:amt_7',
            'amt_8 = stuzha.AMT:amt_8',
            'amt_9 = stuzha.AMT:amt_9',
            'amt_10 = stuzha.AMT:amt_10',
            # ML entry points
            'ml_1 = stuzha.ML:ml_1',
            'ml_2 = stuzha.ML:ml_2',
            'ml_3 = stuzha.ML:ml_3',
            'ml_4 = stuzha.ML:ml_4',
            'ml_5 = stuzha.ML:ml_5',
            'ml_6 = stuzha.ML:ml_6',
            'ml_7 = stuzha.ML:ml_7',
            'ml_8 = stuzha.ML:ml_8',
            'ml_9 = stuzha.ML:ml_9',
        ],
    }
)