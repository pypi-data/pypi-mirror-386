#!/usr/bin/env python3
# coding: utf-8

#***********************************************************************
# gbapy (growth balance analysis for Python)
# Web: https://github.com/charlesrocabert/gbapy
# Copyright © 2024-2025 Charles Rocabert
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#***********************************************************************


"""gbapy (growth balance analysis for Python).

See:
https://github.com/charlesrocabert/gbapy
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
	long_description = f.read()

setup(
	name                          = "gba",
	version                       = "0.6.0",
	license                       = "GNU General Public License v3 (GPLv3)",
	description                   = "gbapy (Growth Balance Analysis for Python)",
	long_description              = long_description,
	long_description_content_type = "text/markdown",
	url                           = "https://github.com/charlesrocabert/gbapy",
	author                        = "Charles Rocabert",
	author_email                  = "charles.rocabert@hhu.de",
	maintainer                    = "Furkan Mert",
	classifiers = [
		"Development Status :: 4 - Beta",
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Operating System :: OS Independent",
		"Intended Audience :: Science/Research",
		"Topic :: Scientific/Engineering :: Mathematics",
	],
	keywords     = "constraint-based-modeling growth-balance-analysis self-replicating-model systems-biology metabolic-network resource-allocation cellular-economics kinetic-modeling first-prnciples simulation evolutionary-algorithms predictive-evolution",
	packages     = find_packages(exclude=["contrib", "docs", "tests"]),
	# package_data = {
    #     'gba.data': ['**/*.csv', '**/*.ods']
    # },
	python_requires  = ">=3",
    install_requires = ["cobra", "molmass", "numpy", "pandas", "gurobipy", "Bio", "IPython", "plotly"],
	project_urls     = {
	"Source": "https://github.com/charlesrocabert/gbapy"
	},
)

