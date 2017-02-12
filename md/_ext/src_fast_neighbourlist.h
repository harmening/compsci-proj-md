/*  md - Molecular Dynamics Applied to ionic solids.
*   Copyright (C) 2017 Nils Harmening, Marco Manni,
*   Darian Steven Viezzer, Steffanie Kieninger, Henrik Narvaez
*
*   This program is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   This program is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef MD
#define MD

double _fast_neighbourlist(double *R, int N, double box_length, double r_cutoff);

#endif