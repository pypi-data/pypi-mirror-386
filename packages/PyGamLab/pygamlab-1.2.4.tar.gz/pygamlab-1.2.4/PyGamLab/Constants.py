'''
Constants.py ==> 


This module contains scientific constants intended for use throughout the package.
'''

#" IN GOD WE TRUST, ALL OTHERS MUST BRING DATA"
#                                               -W. Edwards Deming
#------------------------------------------------------------------------------
# Copyright 2023 The Gamlab Authors. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------
''' 
The Scientific experimental simulation library 
-------------------------------------------------------------------------------
Graphen & Advanced Material Laboratory 

it aimes to provide new scientist to use data,simlation, prepared data 
and Artificial intelligence models.

See http://gamlab.aut.ac.ir for complete documentation.
'''
__doc__='''

@author: Ali Pilehvar Meibody (Alipilehvar1999@gmail.com)

                                         888                    888
 .d8888b    .d88b.     88888b.d88b.      888         .d88b.     888
d88P"      d88""88b    888 "888 "88b     888        d88""88b    88888PP
888  8888  888  888    888  888  888     888        888  888    888  888
Y88b.  88  Y88..88PP.  888  888  888     888......  Y88..88PP.  888  888
 "Y8888P8   "Y88P8888  888  888  888     888888888   "Y88P8888  88888888  


@Director of Gamlab: Professor M. Naderi (Mnaderi@aut.ac.ir)    

@Graphene Advanced Material Laboratory: https://www.GamLab.Aut.ac.ir

'''
import math

# ==============================================================================
# Physical and Scientific Constants
# ==============================================================================

# A
A_lattice_constant = 0.413  # lattice constant in nanometers
alpha_stefan_boltzmann = 5.67e-8  # Stefan-Boltzmann constant (W/m²/K⁴)
Avogadro_Number = 6.022e23  # Avogadro's number (mol⁻¹)

# B
Boltzmann_constant = 1.380649e-23  # More precise value (J/K)

# C
c_speed_of_light = 2.998e8  # Speed of light in vacuum (m/s)
Conductivity_P3HT = 2.4  # Electrical conductivity of P3HT
Conductivity_PLN = 10  # Electrical conductivity of PLN
Conductivity_PPY = 105  # Electrical conductivity of polypyrrole
Conductivity_pT = 33.7  # Electrical conductivity of polythiophene

# D
D_oxygen_diffusion_coeff = 2.3e-5  # Oxygen diffusion coefficient in water (µm²/s)
density_of_Al = 2.7  # g/cm³
density_of_Cu = 8.96  # g/cm³
density_of_Fe = 7.87  # g/cm³

# E
Earth_Accel = 9.8  # Acceleration due to gravity on Earth (m/s²)
Electron_Charge = 1.6e-19  # Elementary charge (C)
e_euler_number = 2.718281828459045  # Euler's number
Eutectic_Percent = 4.3  # Carbon % in eutectic reaction
Eutectic_T = 1148  # Eutectic temperature (°C)
Eutectoid_persent = 0.76  # Carbon % in eutectoid reaction
Eutectoid_T = 727  # Eutectoid temperature (°C)

# F
Faraday_constant = 96485  # Faraday constant (C/mol)
Fe_Density = 7.87  # Density of iron
Fe_Tm_Alpha = 910  # Melting point of alpha-phase iron (°C)
Fe_Tm_Delta = 1539  # Melting point of delta-phase iron (°C)
Fe_Tm_Gama = 1495  # Melting point of gamma-phase iron (°C)

# G
G = 6.674e-11  # Gravitational constant (m³/kg/s²)
G_Mol_Ba = 137.33  # Molar mass of barium
G_Mol_O = 16.00  # Molar mass of oxygen
G_Mol_Si = 28.09  # Molar mass of silicon
G_Mol_Ti = 47.87  # Molar mass of titanium
G_Mol_Zr = 91.22  # Molar mass of zirconium
g = 9.81  # Standard gravity (m/s²)

# H
h_plank = 6.62607015e-34  # Planck’s constant (J·s)

# I
# (None explicitly declared)

# K
K_boltzman = 1.380649e-23   # Boltzmann constant (J/K)

k_z_value_standard = 1.96  # Z value for standard normal distribution

# L
Latent_heat = 1.16e9  # Latent heat 

# M
max_C_inSteel = 2.11  # Max carbon % in steel before it becomes cast iron
melting_point_of_Al = 660  # °C
melting_point_of_Cu = 1085  # °C
melting_point_of_Fe = 1538  # °C

# N
N_A = 6.022e23  # Avogadro’s constant


# P
P_0 = 101325  # Standard atmospheric pressure (Pa)
phi_golden_ratio = 1.618  # Golden ratio
Pi = 3.141592653589793  # Pi
π = 3.141592653589793  # Duplicate with symbol

# Q
# (None explicitly declared)


# R
R = 8.314  # Ideal gas constant (J/mol·K)
R_Cal = 1.987  # Gas constant in cal/(mol·K)
R_LA = 0.08205  # Ideal gas constant in (L·atm)/(mol·K)

# S
S = 28.34  # Standard entropy for solid aluminum (J/mol·K)
Speed_Of_Light = 2.99e8  # Another duplicate of c

# T
Tau = 2 * Pi  # Tau (2π)
thermal_conductivity_coefficient_of_Al = 237  # W/m·K
thermal_conductivity_coefficient_of_Cu = 385  # W/m·K
thermal_conductivity_coefficient_of_Fe = 221  # W/m·K
t_stu = 0.9277  # t-Student value

# V
vacuum_permeability = 1  # Simplified value

# X, Z
Xd = 0.95
Xw = 0.05
Zf = 0.25
zeta = 1.202  # Riemann zeta function at 3 (used in physics)






# --- Fluid Dynamics ---

# Kinematic viscosity of air (m²/s)
nu_air_kinematic = 1.48e-5  # m²/s

# Kinematic viscosity of water at 20°C (m²/s)
nu_water_kinematic = 1.004e-6  # m²/s


# Dynamic Viscosity of air at 20°C (Pa·s)
mu_air_20C = 1.81e-5  # Pa·s

# Dynamic Viscosity of water at 20°C (Pa·s)
mu_water_20C = 0.001002  # Pa·s

# Speed of sound in air at 20°C (m/s)
speed_of_sound_air = 343  # m/s

# Speed of sound in water at 25°C (m/s)
speed_of_sound_water = 1482  # m/s

# Critical velocity for pipe flow (m/s)
critical_velocity = 1.0  # m/s

# Reynolds number for laminar flow (dimensionless)
Re_laminar = 2000  # dimensionless

# Reynolds number for turbulent flow (dimensionless)
Re_turbulent = 4000  # dimensionless

# --- Fluid Properties ---

# Density of air at 20°C (kg/m³)
density_air_20C = 1.204  # kg/m³

# Density of water at 20°C (kg/m³)
density_water_20C = 998  # kg/m³

# Surface tension of water at 25°C (N/m)
surface_tension_water_25C = 0.0728  # N/m

# Vapor pressure of water at 25°C (Pa)
vapor_pressure_water_25C = 3.17e3  # Pa




# --- Thermal Conductivity ---

# Thermal conductivity of air at 300K (W/m·K)
thermal_conductivity_air = 0.0262  # W/m·K

# Thermal conductivity of water at 25°C (W/m·K)
thermal_conductivity_water = 0.606  # W/m·K


# --- Heat Transfer Constants ---

# Convective heat transfer coefficient for water (W/m²·K)
convective_heat_transfer_water = 500  # W/m²·K

# Convective heat transfer coefficient for air (W/m²·K)
convective_heat_transfer_air = 10  # W/m²·K


# Heat transfer coefficient for forced convection (W/m²·K)
heat_transfer_coefficient_forced_convection = 100  # W/m²·K

# Stefan-Boltzmann constant (W/m²·K⁴)
stefan_boltzmann_constant = 5.67e-8  # W/m²·K⁴

# Specific heat capacity of water at 25°C (J/g·K)
specific_heat_water = 4.18  # J/g·K

# Specific heat capacity of air at 25°C (J/g·K)
specific_heat_air = 1.005  # J/g·K

# Latent heat of fusion for ice (J/g)
latent_heat_fusion_ice = 334  # J/g

# Latent heat of vaporization for water (J/g)
latent_heat_vaporization_water_25C = 2260  # J/g


# --- Material Science ---

# Young's Modulus for Steel (Pa)
youngs_modulus_steel = 2.1e11  # Pa

# Young's Modulus for Aluminum (Pa)
youngs_modulus_aluminum = 7.0e10  # Pa

# Poisson's Ratio for Steel
poissons_ratio_steel = 0.3  # dimensionless

# Poisson's Ratio for Aluminum
poissons_ratio_aluminum = 0.33  # dimensionless

# --- Mass Transfer Constants ---

# Diffusion coefficient of oxygen in water at 25°C (m²/s)
diffusion_oxygen_water = 2.3e-9  # m²/s

# Diffusion coefficient of carbon dioxide in water at 25°C (m²/s)
diffusion_CO2_water = 1.3e-9  # m²/s

# Diffusion coefficient of air in water (m²/s)
diffusion_air_water = 2.2e-5  # m²/s

# Diffusion coefficient of hydrogen in water (m²/s)
diffusion_hydrogen_water = 5.2e-9  # m²/s

# Diffusion coefficient of sodium chloride in water (m²/s)
diffusion_NaCl_water = 1.2e-9  # m²/s

# --- Electrical Constants ---

# Permittivity of free space (F/m)
epsilon_0 = 8.854187817e-12  # F/m

# Electric constant (C²/N·m²)
epsilon_0_SI = 8.854187817e-12  # C²/N·m²

# Vacuum permeability (T·m/A)
mu_0 = 4 * Pi * 1e-7  # T·m/A

# Electric potential of the electron (V)
electric_potential_electron = 4.8032e-10  # V

# Resistivity of Copper (Ω·m)
resistivity_copper = 1.68e-8  # Ω·m

# Resistivity of Aluminum (Ω·m)
resistivity_aluminum = 2.82e-8  # Ω·m

# Resistivity of Iron (Ω·m)
resistivity_iron = 9.71e-8  # Ω·m

# --- Magnetism & Electromagnetic Fields ---

# Magnetic permeability of free space (T·m/A)
magnetic_permeability = 4 * Pi * 1e-7  # T·m/A

# Bohr magneton (J/T)
bohr_magneton = 9.274e-24  # J/T

# Magnetic field of the Earth (T)
earth_magnetic_field = 25e-6  # T


# --- Geophysical Constants ---

# Earth's radius (m)
radius_earth = 6.371e6  # meters

# Earth's surface area (m²)
area_earth = 4 * Pi * radius_earth**2  # m²

# Earth's mass (kg)
earth_mass = 5.972e24  # kg

# Earth's volume (m³)
earth_volume = 1.08321e12  # km³

# Earth's surface area (m²)
earth_surface_area = 5.100e14  # m²


# --- Thermodynamic Constants ---

# Critical temperature of water (K)
critical_temperature_water = 647.1  # K

# Critical pressure of water (Pa)
critical_pressure_water = 22.064e6  # Pa

# Latent heat of vaporization of water at 100°C (J/kg)
latent_heat_vaporization_water = 2260e3  # J/kg


# Standard enthalpy of formation of water at 25°C (kJ/mol)
enthalpy_formation_water = -241.8  # kJ/mol

# Standard Gibbs free energy of formation of water at 25°C (kJ/mol)
gibbs_free_energy_water = -237.13  # kJ/mol

# Boltzmann constant (J/K)
boltzmann_constant = 1.380649e-23  # J/K

# Ideal gas constant (J/mol·K)
R_ideal = 8.314462618  # J/mol·K

# Avogadro’s constant (mol⁻¹)
avogadro_constant = 6.02214076e23  # mol⁻¹

# --- Atomic Constants ---

# Atomic mass unit (kg)
atomic_mass_unit = 1.66053906660e-27  # kg

# Rest mass of electron (kg)
electron_mass = 9.10938356e-31  # kg

# Rest mass of proton (kg)
proton_mass = 1.6726219e-27  # kg

# Rest mass of neutron (kg)
neutron_mass = 1.675e-27  # kg

# --- Quantum Mechanics ---

# Reduced Planck's constant (J·s)
h_bar = 1.0545718e-34  # J·s

# Fine structure constant (dimensionless)
alpha_fine_structure = 7.297e-3  # dimensionless

# --- Fluid Dynamics ---

# Reynolds number for transition (dimensionless)
Re_transition = 2000  # dimensionless

# Reynolds number for turbulence (dimensionless)
Re_turbulence = 4000  # dimensionless


# Fine-structure constant (dimensionless)
alpha_fine_structure = 7.297e-3  # dimensionless

# Compton wavelength of the electron (m)
compton_wavelength_electron = 2.426e-12  # m

# Planck length (m)
planck_length = 1.616255e-35  # m

# Planck mass (kg)
planck_mass = 2.176434e-8  # kg

# Planck time (s)
planck_time = 5.391e-44  # s

# Planck temperature (K)
planck_temperature = 1.416784e32  # K



# --- Electrochemistry ---

# Electrode potential of the standard hydrogen electrode (V)
standard_hydrogen_potential = 0  # Volts

# --- Nuclear Physics ---

# Rydberg constant (m⁻¹)
rydberg_constant = 1.097373e7  # m⁻¹

# Neutron capture cross-section for Uranium-235 (barns)
neutron_capture_cross_section_U235 = 680  # barns

# Nuclear fusion energy of Deuterium-Tritium reaction (J)
fusion_energy_D_T = 17.6e6  # Joules

# --- Optics ---

# Refractive index of vacuum (dimensionless)
n_vacuum = 1  # dimensionless

# Refractive index of water (dimensionless)
n_water = 1.333  # dimensionless

# Refractive index of air (dimensionless)
n_air = 1.0003  # dimensionless

# --- Thermodynamics ---

# Standard temperature (K)
T_standard = 298.15  # K

# Standard pressure (Pa)
P_standard = 101325  # Pa



# --- Surface Tension ---

# Surface tension of water at 25°C (N/m)
surface_tension_water = 0.0728  # N/m

# Surface tension of mercury at 25°C (N/m)
surface_tension_mercury = 0.485  # N/m



#----------------------------
#----------------------------
#-----Material Properties----
#----------------------------
#----------------------------


# Periodic Table: Elements and Their Melting Points (Tm in Kelvin)

ELEMENTS_Tm = {
    "H": 14.01,     # Hydrogen
    "He": 0.95,     # Helium
    "Li": 453.65,   # Lithium
    "Be": 1560,     # Beryllium
    "B": 2349,      # Boron
    "C": 3823,      # Carbon (graphite)
    "N": 63.15,     # Nitrogen
    "O": 54.36,     # Oxygen
    "F": 53.53,     # Fluorine
    "Ne": 24.56,    # Neon
    "Na": 370.87,   # Sodium
    "Mg": 923,      # Magnesium
    "Al": 933.47,   # Aluminum
    "Si": 1687,     # Silicon
    "P": 317.3,     # Phosphorus (white)
    "S": 388.36,    # Sulfur
    "Cl": 171.6,    # Chlorine
    "Ar": 83.8,     # Argon
    "K": 336.53,    # Potassium
    "Ca": 1115,     # Calcium
    "Sc": 1814,     # Scandium
    "Ti": 1941,     # Titanium
    "V": 2183,      # Vanadium
    "Cr": 2180,     # Chromium
    "Mn": 1519,     # Manganese
    "Fe": 1811,     # Iron
    "Co": 1768,     # Cobalt
    "Ni": 1728,     # Nickel
    "Cu": 1357.77,  # Copper
    "Zn": 692.68,   # Zinc
    "Ga": 302.91,   # Gallium
    "Ge": 1211.4,   # Germanium
    "As": 1090,     # Arsenic (sublimes)
    "Se": 494,      # Selenium
    "Br": 265.8,    # Bromine
    "Kr": 115.78,   # Krypton
    "Rb": 312.46,   # Rubidium
    "Sr": 1050,     # Strontium
    "Y": 1799,      # Yttrium
    "Zr": 2128,     # Zirconium
    "Nb": 2750,     # Niobium
    "Mo": 2896,     # Molybdenum
    "Tc": 2430,     # Technetium
    "Ru": 2607,     # Ruthenium
    "Rh": 2237,     # Rhodium
    "Pd": 1828.05,  # Palladium
    "Ag": 1234.93,  # Silver
    "Cd": 594.22,   # Cadmium
    "In": 429.75,   # Indium
    "Sn": 505.08,   # Tin
    "Sb": 903.78,   # Antimony
    "Te": 722.66,   # Tellurium
    "I": 386.85,    # Iodine
    "Xe": 161.36,   # Xenon
    "Cs": 301.59,   # Cesium
    "Ba": 1000,     # Barium
    "La": 1193,     # Lanthanum
    "Ce": 1068,     # Cerium
    "Pr": 1208,     # Praseodymium
    "Nd": 1297,     # Neodymium
    "Pm": 1315,     # Promethium
    "Sm": 1345,     # Samarium
    "Eu": 1099,     # Europium
    "Gd": 1585,     # Gadolinium
    "Tb": 1629,     # Terbium
    "Dy": 1680,     # Dysprosium
    "Ho": 1743,     # Holmium
    "Er": 1802,     # Erbium
    "Tm": 1818,     # Thulium
    "Yb": 1097,     # Ytterbium
    "Lu": 1925,     # Lutetium
    "Hf": 2506,     # Hafnium
    "Ta": 3290,     # Tantalum
    "W": 3695,      # Tungsten
    "Re": 3459,     # Rhenium
    "Os": 3306,     # Osmium
    "Ir": 2719,     # Iridium
    "Pt": 2041.4,   # Platinum
    "Au": 1337.33,  # Gold
    "Hg": 234.43,   # Mercury
    "Tl": 577,      # Thallium
    "Pb": 600.61,   # Lead
    "Bi": 544.7,    # Bismuth
    "Po": 527,      # Polonium
    "At": 575,      # Astatine (estimated)
    "Rn": 202,      # Radon
    "Fr": 300,      # Francium (estimated)
    "Ra": 973,      # Radium
    "Ac": 1323,     # Actinium
    "Th": 2023,     # Thorium
    "Pa": 1841,     # Protactinium
    "U": 1405.3,    # Uranium
    "Np": 917,      # Neptunium
    "Pu": 912.5,    # Plutonium
    "Am": 1449,     # Americium
    "Cm": 1613,     # Curium
    "Bk": 1323,     # Berkelium
    "Cf": 1173,     # Californium
    "Es": 1133,     # Einsteinium
    "Fm": 1125,     # Fermium
    "Md": 1100,     # Mendelevium (est.)
    "No": 1100,     # Nobelium (est.)
    "Lr": 1900,     # Lawrencium (est.)
    "Rf": None,     # Rutherfordium (unknown)
    "Db": None,     # Dubnium
    "Sg": None,     # Seaborgium
    "Bh": None,     # Bohrium
    "Hs": None,     # Hassium
    "Mt": None,     # Meitnerium
    "Ds": None,     # Darmstadtium
    "Rg": None,     # Roentgenium
    "Cn": None,     # Copernicium
    "Nh": None,     # Nihonium
    "Fl": None,     # Flerovium
    "Mc": None,     # Moscovium
    "Lv": None,     # Livermorium
    "Ts": None,     # Tennessine
    "Og": None,     # Oganesson
}




# Periodic Table: Elements and Their Densities (g/cm³ at ~20°C)

ELEMENTS_DENSITY = {
    "H": 0.00008988,  # Hydrogen
    "He": 0.0001785,  # Helium
    "Li": 0.534,      # Lithium
    "Be": 1.85,       # Beryllium
    "B": 2.34,        # Boron
    "C": 2.267,       # Carbon (graphite)
    "N": 0.0012506,   # Nitrogen
    "O": 0.001429,    # Oxygen
    "F": 0.001696,    # Fluorine
    "Ne": 0.0008999,  # Neon
    "Na": 0.971,      # Sodium
    "Mg": 1.738,      # Magnesium
    "Al": 2.70,       # Aluminum
    "Si": 2.3296,     # Silicon
    "P": 1.82,        # Phosphorus (white)
    "S": 2.067,       # Sulfur
    "Cl": 0.003214,   # Chlorine
    "Ar": 0.0017837,  # Argon
    "K": 0.862,       # Potassium
    "Ca": 1.54,       # Calcium
    "Sc": 2.989,      # Scandium
    "Ti": 4.54,       # Titanium
    "V": 6.11,        # Vanadium
    "Cr": 7.19,       # Chromium
    "Mn": 7.21,       # Manganese
    "Fe": 7.874,      # Iron
    "Co": 8.90,       # Cobalt
    "Ni": 8.908,      # Nickel
    "Cu": 8.96,       # Copper
    "Zn": 7.134,      # Zinc
    "Ga": 5.91,       # Gallium
    "Ge": 5.323,      # Germanium
    "As": 5.776,      # Arsenic
    "Se": 4.809,      # Selenium
    "Br": 3.119,      # Bromine
    "Kr": 0.003733,   # Krypton
    "Rb": 1.532,      # Rubidium
    "Sr": 2.64,       # Strontium
    "Y": 4.469,       # Yttrium
    "Zr": 6.52,       # Zirconium
    "Nb": 8.57,       # Niobium
    "Mo": 10.22,      # Molybdenum
    "Tc": 11.5,       # Technetium
    "Ru": 12.37,      # Ruthenium
    "Rh": 12.41,      # Rhodium
    "Pd": 12.02,      # Palladium
    "Ag": 10.49,      # Silver
    "Cd": 8.65,       # Cadmium
    "In": 7.31,       # Indium
    "Sn": 7.287,      # Tin
    "Sb": 6.685,      # Antimony
    "Te": 6.24,       # Tellurium
    "I": 4.933,       # Iodine
    "Xe": 0.005887,   # Xenon
    "Cs": 1.873,      # Cesium
    "Ba": 3.62,       # Barium
    "La": 6.145,      # Lanthanum
    "Ce": 6.770,      # Cerium
    "Pr": 6.773,      # Praseodymium
    "Nd": 7.007,      # Neodymium
    "Pm": 7.26,       # Promethium
    "Sm": 7.52,       # Samarium
    "Eu": 5.243,      # Europium
    "Gd": 7.90,       # Gadolinium
    "Tb": 8.229,      # Terbium
    "Dy": 8.55,       # Dysprosium
    "Ho": 8.795,      # Holmium
    "Er": 9.066,      # Erbium
    "Tm": 9.321,      # Thulium
    "Yb": 6.90,       # Ytterbium
    "Lu": 9.841,      # Lutetium
    "Hf": 13.31,      # Hafnium
    "Ta": 16.69,      # Tantalum
    "W": 19.25,       # Tungsten
    "Re": 21.02,      # Rhenium
    "Os": 22.59,      # Osmium (densest element)
    "Ir": 22.56,      # Iridium
    "Pt": 21.45,      # Platinum
    "Au": 19.32,      # Gold
    "Hg": 13.534,     # Mercury
    "Tl": 11.85,      # Thallium
    "Pb": 11.34,      # Lead
    "Bi": 9.78,       # Bismuth
    "Po": 9.196,      # Polonium
    "At": 7.0,        # Astatine (estimated)
    "Rn": 0.00973,    # Radon
    "Fr": 1.87,       # Francium (estimated)
    "Ra": 5.5,        # Radium
    "Ac": 10.07,      # Actinium
    "Th": 11.72,      # Thorium
    "Pa": 15.37,      # Protactinium
    "U": 18.95,       # Uranium
    "Np": 20.45,      # Neptunium
    "Pu": 19.84,      # Plutonium
    "Am": 13.69,      # Americium
    "Cm": 13.51,      # Curium
    "Bk": 14.79,      # Berkelium
    "Cf": 15.1,       # Californium
    "Es": None,       # Einsteinium (unknown)
    "Fm": None,       # Fermium
    "Md": None,       # Mendelevium
    "No": None,       # Nobelium
    "Lr": None,       # Lawrencium
    "Rf": None,       # Rutherfordium
    "Db": None,       # Dubnium
    "Sg": None,       # Seaborgium
    "Bh": None,       # Bohrium
    "Hs": None,       # Hassium
    "Mt": None,       # Meitnerium
    "Ds": None,       # Darmstadtium
    "Rg": None,       # Roentgenium
    "Cn": None,       # Copernicium
    "Nh": None,       # Nihonium
    "Fl": None,       # Flerovium
    "Mc": None,       # Moscovium
    "Lv": None,       # Livermorium
    "Ts": None,       # Tennessine
    "Og": None,       # Oganesson
}




electronegativity = {
    "H": 2.20, "He": None,
    "Li": 0.98, "Be": 1.57, "B": 2.04, "C": 2.55, "N": 3.04, "O": 3.44, "F": 3.98, "Ne": None,
    "Na": 0.93, "Mg": 1.31, "Al": 1.61, "Si": 1.90, "P": 2.19, "S": 2.58, "Cl": 3.16, "Ar": None,
    "K": 0.82, "Ca": 1.00, "Sc": 1.36, "Ti": 1.54, "V": 1.63, "Cr": 1.66, "Mn": 1.55, "Fe": 1.83, "Co": 1.88, "Ni": 1.91, "Cu": 1.90, "Zn": 1.65, "Ga": 1.81, "Ge": 2.01, "As": 2.18, "Se": 2.55, "Br": 2.96, "Kr": 3.00,
    "Rb": 0.82, "Sr": 0.95, "Y": 1.22, "Zr": 1.33, "Nb": 1.6, "Mo": 2.16, "Tc": 1.9, "Ru": 2.2, "Rh": 2.28, "Pd": 2.20, "Ag": 1.93, "Cd": 1.69, "In": 1.78, "Sn": 1.96, "Sb": 2.05, "Te": 2.1, "I": 2.66, "Xe": 2.6,
    "Cs": 0.79, "Ba": 0.89, "La": 1.10, "Ce": 1.12, "Pr": 1.13, "Nd": 1.14, "Pm": 1.13, "Sm": 1.17, "Eu": 1.2, "Gd": 1.2, "Tb": 1.1, "Dy": 1.22, "Ho": 1.23, "Er": 1.24, "Tm": 1.25, "Yb": 1.1, "Lu": 1.27,
    "Hf": 1.3, "Ta": 1.5, "W": 2.36, "Re": 1.9, "Os": 2.2, "Ir": 2.20, "Pt": 2.28, "Au": 2.54, "Hg": 2.00, "Tl": 1.62, "Pb": 2.33, "Bi": 2.02, "Po": 2.0, "At": 2.2, "Rn": None,
    "Fr": 0.7, "Ra": 0.9, "Ac": 1.1, "Th": 1.3, "Pa": 1.5, "U": 1.38, "Np": 1.36, "Pu": 1.28, "Am": 1.13, "Cm": 1.28, "Bk": 1.3, "Cf": 1.3, "Es": 1.3, "Fm": None, "Md": None, "No": None, "Lr": None,
    "Rf": None, "Db": None, "Sg": None, "Bh": None, "Hs": None, "Mt": None, "Ds": None, "Rg": None, "Cn": None, "Nh": None, "Fl": None, "Mc": None, "Lv": None, "Ts": None, "Og": None
}



atomic_radius = {
    "H": 31, "He": 28,
    "Li": 128, "Be": 96, "B": 84, "C": 76, "N": 71, "O": 66, "F": 57, "Ne": 58,
    "Na": 166, "Mg": 141, "Al": 121, "Si": 111, "P": 107, "S": 105, "Cl": 102, "Ar": 106,
    "K": 203, "Ca": 176, "Sc": 170, "Ti": 160, "V": 153, "Cr": 139, "Mn": 139, "Fe": 132, "Co": 126, "Ni": 124, "Cu": 132, "Zn": 122, "Ga": 122, "Ge": 120, "As": 119, "Se": 120, "Br": 120, "Kr": 116,
    "Rb": 220, "Sr": 195, "Y": 190, "Zr": 175, "Nb": 164, "Mo": 154, "Tc": 147, "Ru": 146, "Rh": 142, "Pd": 139, "Ag": 145, "Cd": 144, "In": 142, "Sn": 139, "Sb": 139, "Te": 138, "I": 139, "Xe": 140,
    "Cs": 244, "Ba": 215, "La": 195, "Ce": 185, "Pr": 247, "Nd": 206, "Pm": 205, "Sm": 238, "Eu": 231, "Gd": 233, "Tb": 225, "Dy": 228, "Ho": 226, "Er": 226, "Tm": 222, "Yb": 222, "Lu": 217,
    "Hf": 208, "Ta": 200, "W": 193, "Re": 188, "Os": 185, "Ir": 180, "Pt": 177, "Au": 174, "Hg": 171, "Tl": 156, "Pb": 154, "Bi": 143, "Po": 135, "At": 127, "Rn": 120,
    "Fr": 260, "Ra": 221, "Ac": 215, "Th": 206, "Pa": 200, "U": 196, "Np": 190, "Pu": 187, "Am": 180, "Cm": 169, "Bk": 168, "Cf": 168, "Es": 165, "Fm": 167, "Md": None, "No": None, "Lr": None,
    "Rf": None, "Db": None, "Sg": None, "Bh": None, "Hs": None, "Mt": None, "Ds": None, "Rg": None, "Cn": None, "Nh": None, "Fl": None, "Mc": None, "Lv": None, "Ts": None, "Og": None
}



#Thermal Conductivity (Unit: W/(m·K), at 300 K

thermal_conductivity = {
    "H": 0.1815, "He": 0.1513,
    "Li": 84.7, "Be": 200, "B": 27, "C": 1400, "N": 0.02583, "O": 0.02658, "F": 0.0277, "Ne": 0.0491,
    "Na": 142, "Mg": 156, "Al": 237, "Si": 149, "P": 0.236, "S": 0.269, "Cl": 0.0089, "Ar": 0.0177,
    "K": 102, "Ca": 201, "Sc": 16, "Ti": 21.9, "V": 30.7, "Cr": 93.7, "Mn": 7.81, "Fe": 80.2, "Co": 100, "Ni": 90.9,
    "Cu": 401, "Zn": 116, "Ga": 29, "Ge": 60.2, "As": 50, "Se": 0.52, "Br": 0.122, "Kr": 0.0095,
    "Rb": 58.2, "Sr": 35.4, "Y": 17.2, "Zr": 22.7, "Nb": 53.7, "Mo": 138, "Tc": 50.6, "Ru": 117, "Rh": 150, "Pd": 71.8,
    "Ag": 429, "Cd": 96.6, "In": 81.8, "Sn": 66.8, "Sb": 24.4, "Te": 2.35, "I": 0.449, "Xe": 0.00565,
    "Cs": 36, "Ba": 18.4, "La": 13.4, "Ce": 11.3, "Pr": 12.5, "Nd": 16.5, "Pm": None, "Sm": 13.3, "Eu": 13.9,
    "Gd": 10.6, "Tb": 11.1, "Dy": 10.7, "Ho": 16.2, "Er": 14.5, "Tm": 16.9, "Yb": 38.6, "Lu": 16.4,
    "Hf": 23.0, "Ta": 57.5, "W": 173, "Re": 48, "Os": 87.6, "Ir": 147, "Pt": 71.6, "Au": 318, "Hg": 8.3,
    "Tl": 46.1, "Pb": 35.3, "Bi": 7.97, "Po": None, "At": None, "Rn": 0.00361,
    "Fr": None, "Ra": None, "Ac": None, "Th": 54, "Pa": None, "U": 27.5, "Np": None, "Pu": 6.74
}




#electrical Conductivity (Unit: 10⁶ S/m)
electrical_conductivity = {
    "Li": 10.7, "Be": 25, "B": 1e-4, "C": 1e-5, "Na": 21, "Mg": 22.7, "Al": 37.7, "Si": 1.56e-4,
    "P": 1e-9, "S": 5e-13, "K": 14, "Ca": 29.8, "Sc": 18.4, "Ti": 2.38, "V": 5, "Cr": 7.9, "Mn": 0.62,
    "Fe": 10, "Co": 17.1, "Ni": 14.3, "Cu": 59.6, "Zn": 16.6, "Ga": 7.1, "Ge": 2.0, "As": 0.8,
    "Se": 1e-9, "Br": 1e-11, "Rb": 7.9, "Sr": 7.7, "Y": 7.1, "Zr": 2.4, "Nb": 6.7, "Mo": 18.7,
    "Tc": 5.8, "Ru": 14.1, "Rh": 22.8, "Pd": 9.5, "Ag": 62.1, "Cd": 13, "In": 11.5, "Sn": 8.7,
    "Sb": 2.5, "Te": 0.5, "I": 1e-10, "Cs": 5.5, "Ba": 3.7, "La": 1.7, "Ce": 1.4, "Nd": 1.1,
    "Sm": 1.2, "Gd": 1.0, "Tb": 0.85, "Dy": 1.1, "Ho": 1.2, "Er": 1.1, "Tm": 1.1, "Yb": 3.5,
    "Lu": 2.2, "Hf": 3.1, "Ta": 7.9, "W": 18.2, "Re": 5.6, "Os": 10.6, "Ir": 18.7, "Pt": 9.43,
    "Au": 45.2, "Hg": 10.4, "Tl": 5.8, "Pb": 4.55, "Bi": 0.77, "U": 3.57
}






#======================================
'''
The Element class is a Python class used to represent the properties of a chemical element. It holds attributes for various properties that define each element in terms of its atomic structure, physical properties, and electrical behavior. The class is initialized with the following parameters:

Parameters:

symbol: (str) The chemical symbol of the element (e.g., "H" for Hydrogen, "O" for Oxygen).
atomic_number: (int) The atomic number of the element, which represents the number of protons in the nucleus of an atom.
atomic_mass: (float) The atomic mass of the element, typically given in unified atomic mass units (u).
density: (float) The density of the element, given in grams per cubic centimeter (g/cm³).
melting_point: (float) The temperature at which the element changes from a solid to a liquid, given in Kelvin (K).
electronegativity: (float) The electronegativity of the element, which measures the ability of an atom to attract electrons towards itself when it forms a bond.
thermal_conductivity: (float) The ability of the element to conduct heat, expressed in watts per meter per Kelvin (W/(m·K)).
electrical_conductivity: (float) The ability of the element to conduct electricity, given in MegaSiemens per meter (MS/m).
atomic_radius: (float) The average distance from the nucleus to the outermost electron shell of the atom, measured in picometers (pm).
Methods:

__repr__: This method defines a string representation for the element object, which is useful when inspecting or printing the object. It provides a readable format for displaying the properties of the element.
'''





class Element:
    """
    A class representing a chemical element with key physical and atomic properties.
    
    Attributes:
    - symbol (str): The chemical symbol of the element (e.g., "H" for Hydrogen).
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).
    """
    def __init__(self, symbol, atomic_number, atomic_mass, density, melting_point,
                 electronegativity, thermal_conductivity, electrical_conductivity, atomic_radius):
        self.symbol = symbol
        self.atomic_number = atomic_number
        self.atomic_mass = atomic_mass
        self.density = density
        self.melting_point = melting_point
        self.electronegativity = electronegativity
        self.thermal_conductivity = thermal_conductivity
        self.electrical_conductivity = electrical_conductivity
        self.atomic_radius = atomic_radius

    def __repr__(self):
        return (f"{self.symbol}: Atomic Number={self.atomic_number}, Mass={self.atomic_mass} u, "
                f"Density={self.density} g/cm³, Melting Point={self.melting_point} K, "
                f"Electronegativity={self.electronegativity}, Thermal Conductivity={self.thermal_conductivity} W/(m·K), "
                f"Electrical Conductivity={self.electrical_conductivity} MS/m, Radius={self.atomic_radius} pm")



# Specific element types
class H_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("H", 1, 1.008, 0.00008988, 14.01, 2.20, 0.1815, None, 53)



class He_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("He", 2, 4.0026, 0.0001785, 0.95, None, 0.1513, None, 31)



class Li_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Li", 3, 6.94, 0.534, 453.65, 0.98, 84.7, 1.08e7, 167)



class Be_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Be", 4, 9.0122, 1.848, 1560, 1.57, 200, 2.5e7, 112)



class B_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("B", 5, 10.81, 2.34, 2349, 2.04, 27, 1e4, 87)



class C_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("C", 6, 12.011, 2.267, 3823, 2.55, 140, 1e4, 67)



class N_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("N", 7, 14.007, 0.0012506, 63.15, 3.04, 0.02583, None, 56)



class O_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("O", 8, 15.999, 0.001429, 54.36, 3.44, 0.02658, None, 48)



class F_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("F", 9, 18.998, 0.001696, 53.53, 3.98, 0.0277, None, 42)



class Ne_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ne", 10, 20.180, 0.0008999, 24.56, None, 0.0491, None, 38)



class Na_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Na", 11, 22.990, 0.971, 370.87, 0.93, 144, 2.1e7, 186)



class Mg_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Mg", 12, 24.305, 1.738, 923, 1.31, 156, 2.3e7, 160)



class Al_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Al", 13, 26.982, 2.70, 933.47, 1.61, 235, 3.77e7, 143)



class Si_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Si", 14, 28.085, 2.329, 1687, 1.90, 149, 1.38e7, 118)



class P_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("P", 15, 30.974, 1.82, 317.3, 2.19, 0.0185, None, 110)



class S_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("S", 16, 32.06, 2.067, 388.36, 2.58, 0.205, None, 105)



class Cl_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Cl", 17, 35.45, 0.003214, 171.6, 3.16, 0.00898, None, 99)



class Ar_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ar", 18, 39.948, 0.0017837, 83.80, None, 0.0163, None, 71)


class K_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("K", 19, 39.098, 0.856, 336.53, 0.82, 102, 1.0e7, 196)


class Ca_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ca", 20, 40.078, 1.54, 1115, 1.00, 200, 2.3e7, 174)



class Sc_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Sc", 21, 44.956, 2.989, 1814, 1.36, 15.6, 1.2e7, 162)



class Ti_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ti", 22, 47.867, 4.506, 1941, 1.54, 21.9, 2.4e7, 147)



class V_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("V", 23, 50.9415, 6.11, 2183, 1.63, 30.7, 5.6e7, 134)



class Cr_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Cr", 24, 52.00, 7.19, 2180, 1.66, 24.9, 6.0e7, 128)



class Mn_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Mn", 25, 54.938, 7.43, 1519, 1.55, 73, 1.7e7, 127)



class Fe_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Fe", 26, 55.845, 7.874, 1811, 1.83, 100, 1.0e7, 126)



class Co_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Co", 27, 58.933, 8.90, 1768, 1.88, 68, 1.2e7, 125)



class Ni_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ni", 28, 58.693, 8.912, 1728, 1.91, 91, 1.4e7, 124)


class Cu_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Cu", 29, 63.546, 8.96, 1357.77, 1.90, 398, 5.8e7, 135)



class Zn_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Zn", 30, 65.38, 7.14, 692.68, 1.65, 116, 2.4e7, 139)



class Ga_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ga", 31, 69.723, 5.91, 302.91, 1.81, 40, 4.5e7, 135)



class Ge_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ge", 32, 72.630, 5.323, 1211.40, 2.01, 60, 4.0e7, 125)



class As_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("As", 33, 74.922, 5.776, 1090, 2.18, 35, None, 120)



class Se_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Se", 34, 78.971, 4.79, 494.15, 2.55, 51, None, 116)



class Br_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Br", 35, 79.904, 3.12, 265.8, 2.96, 40, None, 114)



class Kr_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Kr", 36, 83.798, 3.749, 115.79, None, 0.00894, None, 112)


class Rb_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Rb", 37, 85.468, 1.532, 312.46, 0.82, 73, 1.2e7, 303)



class Sr_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Sr", 38, 87.62, 2.64, 1382, 0.95, 35, 1.5e7, 249)



class Y_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Y", 39, 88.906, 4.469, 1795, 1.22, 29.3, 2.0e7, 220)



class Zr_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Zr", 40, 91.224, 6.52, 2128, 1.33, 20, 2.5e7, 206)



class Nb_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Nb", 41, 92.906, 8.57, 2750, 1.60, 24.7, 2.7e7, 198)



class Mo_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Mo", 42, 95.95, 10.22, 2896, 2.16, 142, 3.1e7, 190)



class Tc_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Tc", 43, 98.0, 11.50, 2430, 1.9, 80, 2.8e7, 179)



class Ru_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ru", 44, 101.07, 12.37, 2607, 2.20, 123, 3.0e7, 171)



class Rh_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Rh", 45, 102.91, 12.41, 1964, 2.28, 123, 3.2e7, 169)



class Pd_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Pd", 46, 106.42, 12.02, 1828.05, 2.20, 96, 4.0e7, 165)



class Ag_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ag", 47, 107.87, 10.49, 1235.08, 1.93, 63.1, 6.3e7, 162)



class Cd_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Cd", 48, 112.41, 8.69, 594.22, 1.69, 62, 1.8e7, 158)



class In_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("In", 49, 114.82, 7.31, 156.6, 1.78, 82, 3.5e7, 156)



class Sn_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Sn", 50, 118.71, 7.31, 231.93, 1.96, 66, 2.2e7, 145)



class Sb_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Sb", 51, 121.76, 6.684, 904, 2.05, 8.6, None, 138)



class I_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("I", 53, 126.90, 4.933, 113.7, 2.66, 0.149, None, 133)



class Xe_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Xe", 54, 131.29, 5.894, 165.03, None, 0.0055, None, 130)



class Cs_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Cs", 55, 132.91, 1.93, 301.59, 0.79, 72, 1.0e7, 265)



class Ba_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ba", 56, 137.33, 3.62, 1000, 0.89, 182, 1.2e7, 253)



class La_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("La", 57, 138.91, 6.15, 1191, 1.10, 214, 2.1e7, 250)



class Ce_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ce", 58, 140.12, 6.77, 1071, 1.12, 175, 2.2e7, 249)



class Pr_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Pr", 59, 140.91, 6.77, 1299, 1.13, 120, 2.3e7, 248)



class Nd_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Nd", 60, 144.24, 7.01, 1294, 1.14, 102, 2.4e7, 246)



class Pm_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Pm", 61, 145.0, 7.26, 1380, 1.13, 50, 2.5e7, 245)



class Sm_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Sm", 62, 150.36, 7.52, 1347, 1.17, 110, 2.5e7, 243)



class Eu_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Eu", 63, 151.98, 5.243, 1527, 1.20, 59, 2.6e7, 242)



class Gd_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Gd", 64, 157.25, 8.23, 1585, 1.20, 66, 2.7e7, 240)



class Tb_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Tb", 65, 158.93, 8.23, 1629, 1.10, 80, 2.7e7, 239)



class Dy_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Dy", 66, 162.50, 8.55, 1680, 1.22, 85, 2.8e7, 237)


class Ho_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ho", 67, 164.93, 8.79, 1734, 1.23, 90, 2.8e7, 236)



class Er_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Er", 68, 167.26, 9.066, 1802, 1.24, 150, 2.9e7, 234)



class Tm_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Tm", 69, 168.93, 9.32, 1818, 1.25, 88, 3.0e7, 233)



class Yb_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Yb", 70, 173.04, 6.98, 1092, 1.10, 90, 3.1e7, 231)



class Lu_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Lu", 71, 174.97, 9.84, 1925, 1.27, 52, 3.2e7, 229)



class Hf_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Hf", 72, 178.49, 13.31, 2506, 1.30, 175, 3.3e7, 227)



class Ta_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ta", 73, 180.95, 16.65, 3290, 1.50, 68, 3.4e7, 225)



class W_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("W", 74, 183.84, 19.25, 3422, 2.36, 174, 3.5e7, 223)



class Re_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Re", 75, 186.21, 21.02, 3186, 1.9, 130, 3.6e7, 222)



class Os_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Os", 76, 190.23, 22.59, 3306, 2.2, 140, 3.7e7, 220)



class Ir_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Ir", 77, 192.22, 22.56, 2719, 2.2, 130, 3.8e7, 218)



class Pt_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Pt", 78, 195.08, 21.45, 2041, 2.28, 156, 3.9e7, 216)



class Au_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Au", 79, 196.97, 19.32, 1337.33, 2.54, 45, 4.1e7, 214)



class Hg_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Hg", 80, 200.59, 13.53, 234.32, 2.00, 8.3, 4.3e7, 212)



class Tl_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Tl", 81, 204.38, 11.85, 577, 1.62, 0.78, 4.5e7, 210)



class Pb_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Pb", 82, 207.2, 11.34, 600.61, 2.33, 35, 4.6e7, 208)



class Bi_Type(Element):
    '''
    Attributes:
    - symbol (str): The chemical symbol of the element.
    - atomic_number (int): The number of protons in the element's nucleus.
    - atomic_mass (float): The atomic mass in unified atomic mass units (u).
    - density (float): The density of the element in g/cm³.
    - melting_point (float): The melting point of the element in Kelvin (K).
    - electronegativity (float): The electronegativity of the element, a measure of its ability to attract electrons.
    - thermal_conductivity (float): The thermal conductivity in W/(m·K).
    - electrical_conductivity (float): The electrical conductivity in MS/m.
    - atomic_radius (float): The atomic radius in picometers (pm).

    '''
    def __init__(self):
        super().__init__("Bi", 83, 208.98, 9.78, 271.3, 2.02, 0.9, 4.7e7, 206)




#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================
#=========================


#Band_gap (eV at 300K) : 

#references: 

#https://doi.org/10.1088/1742-6596/1013/1/012190 
#https://doi.org/10.1016/j.cjph.2020.03.014 
#https://doi.org/10.1103/PhysRevB.69.085102 
#https://doi.org/10.1088/1742-6596/1816/1/012114 
#Photovoltaic Conversion: Space Applications, PETER A. ILES, 2004 
#http://dx.doi.org/10.1016/B978-1-4377-3471-3.00013-7 
#https://doi.org/10.1016/j.ijhydene.2018.08.159 
#Band structure of cadmium arsenide at room temperature, M. J. Aubin, 1977 
#http://iopscience.iop.org/0370-1328/72/4/309 
#Better band gaps for wide-gap semiconductors from a locally corrected exchange-correlation potential that nearly eliminates self-interaction errors, Prashant Singh, 2018 
#Theoretical study of the insulating oxides and nitrides: SiO2, GeO2, Al2O3, Si3N4, and Ge3N4, C. Sevik, 2024 
#Electron states in a~uartz: A self-consistent pseufiopotential calculation, James R. Chelikowsky, 1977 
#Electronic energy-band structure of n quartz, Eduardo Calabrese, 1978 
#ELECTRONIC STRUCTURE OF ELEMENTAL BORON, Liaoyuan Wang, Kansas City, Missouri, 2010 
#https://link.springer.com/chapter/10.1007/978-1-4615-5247-5_26 
#https://doi.org/10.1007/978-1-4615-5247-5_26 
#https://www.ioffe.ru/SVA/NSM/Semicond/GaSb/bandstr.html 

#Conductors 



#Semiconductors 

Silicon_Bandgap= 1.14 
Germanium_Bandgap= 0.67 
Gallium_Nitride_Bandgap= 3.4 
Gallium_Phosphide_Bandgap= 2.26 
Gallium_Arsenide_Bandgap= 1.43 
Silicon_Nitride_Bandgap= 4.9 #4.3-5.5 
Lead2_Sulfide_Bandgap= 0.37 
Copper1_Oxide_Bandgap= 2.1 
Copper2_Oxide_Bandgap= 1.4 
Boron_Indirectbandgap= 2.0 #1.4-2.6 
Silicon_Carbide_Bandgap= 2.8 #2.3-3.3 
Aluminium_Phosphide_Bandgap= 2.45 
Aluminium_Arsenide_Bandgap= 2.16 
Cadmium_Sulfide_Bandgap= 2.42 
Zinc_Oxide_Bandgap= 3.37 
Zinc_Selenide_Bandgap= 2.7 
Zinc_Sulfide_Bandgap= 3.725 #3.54-3.91 
Zinc_Telluride_Bandgap= 2.3 
Tin_Dioxide_Bandgap= 3.7 
Indium_Antimonide_Bandgap= 0.17 
Indium_Arsenide_Bandgap= 0.36 
Indium_Phosphide_Bandgap= 1.29 
Gallium_Antimonide_Bandgap= 0.726 
Gallium_Arsenide_Bandgap= 1.42 
Cadmium_Selenide_Bandgap= 1.74 
Cadmium_Telluride_Bandgap= 1.5 
Mercury_Cadmium_Telluride_Bandgap= 0.75 #0-1.5 
Mercury_Zinc_Telluride_Bandgap= 1.2 #0.15-2.25 
Lead_Selenide_Bandgap= 0.27 
Tellurium_Bandgap= 0.33 
Lead_Telluride_Bandgap= 0.32 
Magnetite_Bandgap= 1.45 
Cadmium_Arsenide_Bandgap= 0.3 #0.04-0.6
Bismuth_Telluride_Bandgap= 0.14 
Tin_Telluride_Bandgap= 0.18 
Tin_Selenide_Bandgap= 0.9 
Silver1_Selenide_Bandgap= 0.07 #0.04-0.1 
Magnesium_Silicide_Bandgap= 0.79 

#Insulators 

Aluminium_Nitride_Bandgap= 6.0 
Diamond_Bandgap= 5.5 
Amorphous_Silicon_Dioxide_Bandgap= 9.3 
AlfaQuartz_Silicon_Dioxide_Bandgap= 9.2 
BetaCristobalite_Silicon_Dioxide_Directbandgap= 5.605 #5.48-5.73 
BetaCristobalite_Silicon_Dioxide_Indirectbandgap= 9.11 
AlfaCristobalite_Silicon_Dioxide_Indirectbandgap= 9.21 
Silicon_Oxide_Bandgap= 6.2 
Boron_Nitride_Bandgap= 6.16 #5.96-6.36 

#bond length (picometers at 300 K) : 

#references: 
#https://www.webassign.net/question_assets/wertzcams3/bond_lengths/manual.html 
#https://www.chem.uzh.ch/en/research/services/xray/bond_lenghts.html 
#https://doi.org/10.1021/jp1036475 
#https://doi.org/10.1021/ja034656e 
#https://doi.org/10.1016/j.molstruc.2009.04.029 

#C bonds 

C_H_Bondlength = 109 #106-112 
C_Be_Bondlength = 193 
C_Mg_Bondlength = 230 #212-247 
C_B_Bondlength = 156 
C_Al_Bondlength = 191 
C_In_Bondlength = 216 
C_C_Bondlength = 137 #120-154 
C_Si_Bondlength = 186 
C_Sn_Bondlength = 214 
C_Pb_Bondlength = 229  
C_N_Bondlength = 131 #115-147 
C_P_Bondlength = 187 
C_As_Bondlength = 198 
C_Sb_Bondlength = 205 
C_Bi_Bondlength = 230 
C_O_Bondlength = 128 #113-143 
C_S_Bondlength = 168 #155-182 
C_Cr_Bondlength = 198 
C_Se_Bondlength = 183 #168-198  
C_Te_Bondlength = 202 #190-215 
C_Mo_Bondlength = 208 
C_W_Bondlength = 206 
C_F_Bondlength = 134 
C_Cl_Bondlength = 176 
C_Br_Bondlength = 193 
C_I_Bondlength = 213 

#H bonds 

B_H_Bondlength = 132 
H_F_Bondlength = 92 
N_H_Bondlength = 101 
H_O_Bondlength = 96 
H_Cl_Bondlength = 127 
H_H_Bondlength = 74 

#O bonds 

O_F_Bondlength = 142 
N_O_Bondlength = 132 #120-144 
O_O_Bondlength = 134 #121-148 

#N bonds 

Si_N_Bondlength = 173 
N_N_Bondlength = 128 #110-147 


#others 

B_Cl_Bondlength = 174 
Cl_Br_Bondlength = 214 
S_Al_Bondlength = 243 

#dielectric constants : 

#polymers 

Polyacrylonitrile_Dielectric_Constant_1kHz = 5.50 #temperature=25 C 
Polyacrylonitrile_Dielectric_Constant_1MHz = 4.20 #temperature=25 C 
Polyamide_Dielectric_Constant_1kHz = 3.50 #temperature=25 C 
Polyamide_Dielectric_Constant_1MHz = 3.14 #temperature=25 C 
Polyamide_Dielectric_Constant_1GHz = 2.80 #temperature=25 C 
Polyamide_Dielectric_Constant_1kHz = 11.00 #temperature=84 C 
Polyamide_Dielectric_Constant_1MHz = 4.400 #temperature=84 C 
Polyamide_Dielectric_Constant_1GHz = 2.800 #temperature=84 C 
Polyabutadiene_Dielectric_Constant_1kHz = 2.50 #temperature=25 C 
Polycarbonate_Dielectric_Constant_1kHz = 2.92 #temperature=23 C 
Polycarbonate_Dielectric_Constant_1MHz = 2.80 #temperature=23 C 
Polychloroprene_Dielectric_Constant_1kHz = 6.60 #temperature=25 C 
Polychloroprene_Dielectric_Constant_1MHz = 6.30 #temperature=25 C 
Polychloroprene_Dielectric_Constant_1GHz = 4.20 #temperature=25 C 
Polychlorotrifluorethylene_Dielectric_Constant_1kHz = 2.65 #temperature=23 C 
Polychlorotrifluorethylene_Dielectric_Constant_1MHz = 2.46 #temperature=23 C 
Polychlorotrifluorethylene_Dielectric_Constant_1GHz = 2.39 #temperature=23 C 
Polyethylene_Dielectric_Constant_1kHz = 2.30 #temperature=23 C 
Poly_Ethyleneterephthalate_Dielectric_Constant_1kHz = 3.25 #temperature=23 C 
Poly_Ethyleneterephthalate_Dielectric_Constant_1MHz = 3.00 #temperature=23 C 
Poly_Ethyleneterephthalate_Dielectric_Constant_1GHz = 2.80 #temperature=23 C 
Polyisoprene_Dielectric_Constant_1kHz = 2.60 #temperature=27 C 
Polyisoprene_Dielectric_Constant_1MHz = 2.50 #temperature=27 C 
Polyisoprene_Dielectric_Constant_1GHz = 2.40 #temperature=27 C 
Poly_Methylmethacrylate_Dielectric_Constant_1kHz = 3.12 #temperature=27 C 
Poly_Methylmethacrylate_Dielectric_Constant_1MHz = 2.76 #temperature=27 C 
Poly_Methylmethacrylate_Dielectric_Constant_1GHz = 2.60 #temperature=27 C 
Poly_Methylmethacrylate_Dielectric_Constant_1kHz = 3.80 #temperature=80 C 
Poly_Methylmethacrylate_Dielectric_Constant_1MHz = 2.70 #temperature=80 C 
Poly_Methylmethacrylate_Dielectric_Constant_1GHz = 2.60 #temperature=80 C 
Polyformaldehyde_Dielectric_Constant_1kHz = 3.80 #temperature=25 C 
Poly_Phenyleneoxide_Dielectric_Constant_1kHz = 2.59 #temperature=23 C 
Poly_Phenyleneoxide_Dielectric_Constant_1MHz = 2.59 #temperature=23 C 
Polypropylene_Dielectric_Constant_1kHz = 2.30 #temperature=25 C 
Polypropylene_Dielectric_Constant_1MHz = 2.30 #temperature=25 C 
Polypropylene_Dielectric_Constant_1GHz = 2.30 #temperature=25 C 
Polystyrene_Dielectric_Constant_1kHz = 2.60 #temperature=25 C 
Polystyrene_Dielectric_Constant_1MHz = 2.60 #temperature=25 C 
Polystyrene_Dielectric_Constant_1GHz = 2.60 #temperature=25 C 
Polysulfone_Dielectric_Constant_1kHz = 3.13 #temperature=25 C 
Polysulfone_Dielectric_Constant_1MHz = 2.10 #temperature=25 C 
Polytetrafluoroethylene_Dielectric_Constant_1kHz = 2.10 #temperature=25 C 
Polytetrafluoroethylene_Dielectric_Constant_1MHz = 2.10 #temperature=25 C 
Polytetrafluoroethylene_Dielectric_Constant_1GHz = 2.10 #temperature=25 C 
Poly_Vinylacetate_Dielectric_Constant_1MHz = 3.50 #temperature=50 C 
Poly_Vinylacetate_Dielectric_Constant_1MHz = 8.30 #temperature=150 C 
Poly_Vinylchloride_Dielectric_Constant_1kHz = 3.39 #temperature=25 C 
Poly_Vinylchloride_Dielectric_Constant_1MHz = 2.90 #temperature=25 C 
Poly_Vinylchloride_Dielectric_Constant_1GHz = 2.80 #temperature=25 C 
Poly_Vinylchloride_Dielectric_Constant_1kHz = 5.30 #temperature=100 C 
Poly_Vinylchloride_Dielectric_Constant_1MHz = 2.70 #temperature=100 C 
Poly_Vinylidenechloride_Dielectric_Constant_1kHz = 4.60 #temperature=23 C 
Poly_Vinylidenechloride_Dielectric_Constant_1MHz = 3.20 #temperature=23 C 
Poly_Vinylidenechloride_Dielectric_Constant_1GHz = 2.70 #temperature=23 C 
Poly_Vinylidenefluoride_Dielectric_Constant_1kHz = 12.20 #temperature=23 C 
Poly_Vinylidenefluoride_Dielectric_Constant_1MHz = 8.90 #temperature=23 C 
Poly_Vinylidenefluoride_Dielectric_Constant_1GHz = 4.70 #temperature=23 C 

#fermi energy (eV), fermi temperature (K), fermi velocity (cm/sec), fermi wave vector of metals (1/cm) 
#Wingerseitsradius_Bohrradius = Wingerseits radius/Bohr radius = rs/a0 
#Z = number of conduction electrons in each atom (dimensionless) 
#n = number of conduction electrons per unit volume (atoms/cm**3) 
#all datas are reported at room temperature and atmospheric pressure unless those reporting with hashtag 

#reference: Ashcroft, N. W., & Mermin, N. D., Solid State Physics. , 1976. 

Lithium_Z = 1 #78 K 
Lithium_n = 4.70 * 10**22 
Lithium_Fermi_Energy = 4.74 
Lithium_Fermi_Temperature = 5.51 * 10**4 
Lithium_Fermi_Wavevector = 1.12 * 10**8 
Lithium_Fermi_Velocity = 1.29 * 10**8 
Lithium_Wingerseitsradius_Bohrradius = 3.25 
Sodium_Z = 1 #5 K 
Sodium_n = 2.65 * 10**22 
Sodium_Fermi_Energy = 3.24 
Sodium_Fermi_Temperature = 3.77 * 10**4 
Sodium_Fermi_Wavevector = 0.92 * 10**8 
Sodium_Fermi_Velocity = 1.07 * 10**8 
Sodium_Wingerseitsradius_Bohrradius = 3.93 
Potassium_Z = 1 #5 K 
Potassium_n = 1.40 * 10**22 
Potassium_Fermi_Energy = 2.12 
Potassium_Fermi_Temperature = 2.46 * 10**4 
Potassium_Fermi_Wavevector = 0.75 * 10**8 
Potassium_Fermi_Velocity = 0.86 * 10**8 
Potassium_Wingerseitsradius_Bohrradius = 4.86 
Rubidium_Z = 1 #5 K 
Rubidium_n = 1.15 * 10**22 
Rubidium_Fermi_Energy = 1.85 
Rubidium_Fermi_Temperature = 2.15 * 10**4 
Rubidium_Fermi_Wavevector = 0.70 * 10**8 
Rubidium_Fermi_Velocity = 0.81 * 10**8 
Rubidium_Wingerseitsradius_Bohrradius = 5.20 
Caesium_Z = 1 #5 K 
Caesium_n = 0.91 * 10**22 
Caesium_Fermi_Energy = 1.59 
Caesium_Fermi_Temperature = 1.84 * 10**4 
Caesium_Fermi_Wavevector = 0.65 * 10**8 
Caesium_Fermi_Velocity = 0.75 * 10**8 
Caesium_Wingerseitsradius_Bohrradius = 5.62 
Copper_Z = 1 
Copper_n = 8.47 * 10**22 
Copper_Fermi_Energy = 7.00 
Copper_Fermi_Temperature = 8.16 * 10**4 
Copper_Fermi_Wavevector = 1.36 * 10**8 
Copper_Fermi_Velocity = 1.57 * 10**8 
Copper_Wingerseitsradius_Bohrradius = 2.67 
Silver_Z = 1 
Silver_n = 5.86 * 10**22 
Silver_Fermi_Energy = 5.49 
Silver_Fermi_Temperature = 6.38 * 10**4 
Silver_Fermi_Wavevector = 1.20 * 10**8 
Silver_Fermi_Velocity = 1.39 * 10**8 
Silver_Wingerseitsradius_Bohrradius = 3.02 
Gold_Z = 1 
Gold_n = 5.90 * 10**22 
Gold_Fermi_Energy = 5.53 
Gold_Fermi_Temperature = 6.42 * 10**4 
Gold_Fermi_Wavevector = 1.21 * 10**8 
Gold_Fermi_Velocity = 1.40 * 10**8 
Gold_Wingerseitsradius_Bohrradius = 3.01 
Beryllium_Z = 2 
Beryllium_n = 24.7 * 10**22 
Beryllium_Fermi_Energy = 14.3 
Beryllium_Fermi_Temperature = 16.6 * 10**4 
Beryllium_Fermi_Wavevector = 1.94 * 10**8 
Beryllium_Fermi_Velocity = 2.25 * 10**8 
Beryllium_Wingerseitsradius_Bohrradius = 1.87 
Magnesium_Z = 2 
Magnesium_n = 8.61 * 10**22 
Magnesium_Fermi_Energy = 7.08 
Magnesium_Fermi_Temperature = 8.23 * 10**4 
Magnesium_Fermi_Wavevector = 1.36 * 10**8 
Magnesium_Fermi_Velocity = 1.58 * 10**8 
Magnesium_Wingerseitsradius_Bohrradius = 2.66 
Calcium_Z = 2 
Calcium_n = 4.61 * 10**22 
Calcium_Fermi_Energy = 4.69 
Calcium_Fermi_Temperature = 5.44 * 10**4 
Calcium_Fermi_Wavevector = 1.11 * 10**8 
Calcium_Fermi_Velocity = 1.28 * 10**8 
Calcium_Wingerseitsradius_Bohrradius = 3.27 
Strontium_Z = 2 
Strontium_n = 3.55 * 10**22 
Strontium_Fermi_Energy = 3.93 
Strontium_Fermi_Temperature = 4.57 * 10**4 
Strontium_Fermi_Wavevector = 1.02 * 10**8 
Strontium_Fermi_Velocity = 1.18 * 10**8 
Strontium_Wingerseitsradius_Bohrradius = 3.57 
Barium_Z = 2 
Barium_n = 3.15 * 10**22 
Barium_Fermi_Energy = 3.64 
Barium_Fermi_Temperature = 4.23 * 10**4 
Barium_Fermi_Wavevector = 0.98 * 10**8 
Barium_Fermi_Velocity = 1.13 * 10**8 
Barium_Wingerseitsradius_Bohrradius = 3.71 
Niobium_Z = 1 
Niobium_n = 5.56 * 10**22 
Niobium_Fermi_Energy = 5.32 
Niobium_Fermi_Temperature = 6.18 * 10**4 
Niobium_Fermi_Wavevector = 1.18 * 10**8 
Niobium_Fermi_Velocity = 1.37 * 10**8 
Niobium_Wingerseitsradius_Bohrradius = 3.07 
Iron_Z = 2 
Iron_n = 17.0 * 10**22 
Iron_Fermi_Energy = 11.1 
Iron_Fermi_Temperature = 13.0 * 10**4 
Iron_Fermi_Wavevector = 1.71 * 10**8 
Iron_Fermi_Velocity = 1.98 * 10**8 
Iron_Wingerseitsradius_Bohrradius = 2.12 
Manganese_Z = 2 
Manganese_n = 16.5 * 10**22 
Manganese_Fermi_Energy = 10.9 
Manganese_Fermi_Temperature = 12.7 * 10**4 
Manganese_Fermi_Wavevector = 1.70 * 10**8 
Manganese_Fermi_Velocity = 1.96 * 10**8 
Manganese_Wingerseitsradius_Bohrradius = 2.14 
Zinc_Z = 2 
Zinc_n = 13.2 * 10**22 
Zinc_Fermi_Energy = 9.47 
Zinc_Fermi_Temperature = 11.0 * 10**4 
Zinc_Fermi_Wavevector = 1.58 * 10**8 
Zinc_Fermi_Velocity = 1.83 * 10**8 
Zinc_Wingerseitsradius_Bohrradius = 2.30 
Cadmium_Z = 2 
Cadmium_n = 9.27 * 10**22 
Cadmium_Fermi_Energy = 7.47 
Cadmium_Fermi_Temperature = 8.68 * 10**4 
Cadmium_Fermi_Wavevector = 1.40 * 10**8 
Cadmium_Fermi_Velocity = 1.62 * 10**8 
Cadmium_Wingerseitsradius_Bohrradius = 2.59 
Mercury_Z = 2 #78 K 
Mercury_n = 8.65 * 10**22 
Mercury_Fermi_Energy = 7.13 
Mercury_Fermi_Temperature = 8.29 * 10**4 
Mercury_Fermi_Wavevector = 1.37 * 10**8 
Mercury_Fermi_Velocity = 1.58 * 10**8 
Mercury_Wingerseitsradius_Bohrradius = 2.65 
Aluminium_Z = 3 
Aluminium_n = 18.1 * 10**22 
Aluminium_Fermi_Energy = 11.7 
Aluminium_Fermi_Temperature = 13.6 * 10**4 
Aluminium_Fermi_Wavevector = 1.75 * 10**8 
Aluminium_Fermi_Velocity = 2.03 * 10**8 
Aluminium_Wingerseitsradius_Bohrradius = 2.07 
Gallium_Z = 3 
Gallium_n = 15.4 * 10**22  
Gallium_Fermi_Energy = 10.4 
Gallium_Fermi_Temperature = 12.1 * 10**4 
Gallium_Fermi_Wavevector = 1.66 * 10**8 
Gallium_Fermi_Velocity = 1.92 * 10**8 
Gallium_Wingerseitsradius_Bohrradius = 2.19 
Indium_Z = 3 
Indium_n = 11.5 * 10**22 
Indium_Fermi_Energy = 8.63 
Indium_Fermi_Temperature = 10.0 * 10**4 
Indium_Fermi_Wavevector = 1.51 * 10**8 
Indium_Fermi_Velocity = 1.74 * 10**8 
Indium_Wingerseitsradius_Bohrradius = 2.41 
Thallium_Z = 3 
Thallium_n = 10.5 * 10**22 
Thallium_Fermi_Energy = 8.15 
Thallium_Fermi_Temperature = 9.46 * 10**4 
Thallium_Fermi_Wavevector = 1.46 * 10**8 
Thallium_Fermi_Velocity = 1.69 * 10**8 
Thallium_Wingerseitsradius_Bohrradius = 2.48 
Tin_Z = 4 
Tin_n = 14.8 * 10**22 
Tin_Fermi_Energy = 10.2 
Tin_Fermi_Temperature = 11.8 * 10**4 
Tin_Fermi_Wavevector = 1.64 * 10**8 
Tin_Fermi_Velocity = 1.90 * 10**8 
Tin_Wingerseitsradius_Bohrradius = 2.22 
Lead_Z = 4 
Lead_n = 13.2 * 10**22 
Lead_Fermi_Energy = 9.47 
Lead_Fermi_Temperature = 11.0 * 10**4 
Lead_Fermi_Wavevector = 1.58 * 10**8 
Lead_Fermi_Velocity = 1.83 * 10**8 
Lead_Wingerseitsradius_Bohrradius = 2.30 
Bismuth_Z = 5 
Bismuth_n = 14.1 * 10**22 
Bismuth_Fermi_Energy = 9.90 
Bismuth_Fermi_Temperature = 11.5 * 10**4 
Bismuth_Fermi_Wavevector = 1.61 * 10**8 
Bismuth_Fermi_Velocity = 1.87 * 10**8 
Bismuth_Wingerseitsradius_Bohrradius = 2.25 
Antimony_Z = 5 
Antimony_n = 16.5 * 10**22 
Antimony_Fermi_Energy = 10.9 
Antimony_Fermi_Temperature = 12.7 * 10**4 
Antimony_Fermi_Wavevector = 1.70 * 10**8 
Antimony_Fermi_Velocity = 1.96 * 10**8 
Antimony_Wingerseitsradius_Bohrradius = 2.14 

#thermal conductivity (W/(mC)), density (kg/m**3), 
# specific heat at constant pressure (kJ/(kg.C)), thermal diffusivity (m**2/s) 

#heat transfer, Holman, 2010 

#metals 

#all properties are reported at temperature=20 C 

Aluminium_Density = 2707 
Aluminium_Specific_heat_at_constant_pressure = 0.896 
Aluminium_Thermal_Conductivity = 204 
Aluminium_Thrmal_Diffusivity = 8.418 * 10**-5 
Lead_Density = 11373 
Lead_Specific_heat_at_constant_pressure = 0.130 
Lead_Thermal_Conductivity = 35 
Lead_Thrmal_Diffusivity = 3.343 * 10**-5 
Iron_Density = 7897 
Iron_Specific_heat_at_constant_pressure = 0.452 
Iron_Thermal_Conductivity = 73 
Iron_Thrmal_Diffusivity = 2.034 * 10**-5 
SteelC05_Density = 7833 #Iron with 0.5 % C 
SteelC05_Specific_heat_at_constant_pressure = 0.465 
SteelC05_Thermal_Conductivity = 54 
SteelC05_Thrmal_Diffusivity = 1.474 * 10**-5 
SteelC1_Density = 7801 #Iron with 1.0 % C 
SteelC1_Specific_heat_at_constant_pressure = 0.473 
SteelC1_Thermal_Conductivity = 43 
SteelC1_Thrmal_Diffusivity = 1.172 * 10**-5 
SteelC15_Density = 7753 #Iron with 1.5 % C 
SteelC15_Specific_heat_at_constant_pressure = 0.486 
SteelC15_Thermal_Conductivity = 36 
SteelC15_Thrmal_Diffusivity = 0.970 * 10**-5 
Nickelsteel20_Density = 7933 #Iron with 20 % Ni 
Nickelsteel20_Specific_heat_at_constant_pressure = 0.460 
Nickelsteel20_Thermal_Conductivity = 19 
Nickelsteel20_Thrmal_Diffusivity = 0.526 * 10**-5 
Nickelsteel40_Density = 8169 #Iron with 40 % Ni 
Nickelsteel40_Specific_heat_at_constant_pressure = 0.460 
Nickelsteel40_Thermal_Conductivity = 10 
Nickelsteel40_Thrmal_Diffusivity = 0.279 * 10**-5 
Nickelsteel80_Density = 8618 #Iron with 80 % Ni 
Nickelsteel80_Specific_heat_at_constant_pressure = 0.460 
Nickelsteel80_Thermal_Conductivity = 35 
Nickelsteel80_Thrmal_Diffusivity = 0.872 * 10**-5 
Chromesteel1_Density = 7865 #Iron with 1 % Cr 
Chromesteel1_Specific_heat_at_constant_pressure = 0.460 
Chromesteel1_Thermal_Conductivity = 61 
Chromesteel1_Thrmal_Diffusivity = 1.665 * 10**-5 
Chromesteel5_Density = 7833 #Iron with 5 % Cr 
Chromesteel5_Specific_heat_at_constant_pressure = 0.460 
Chromesteel5_Thermal_Conductivity = 40 
Chromesteel5_Thrmal_Diffusivity = 1.110 * 10**-5 
Chromesteel20_Density = 7689 #Iron with 20 % Cr 
Chromesteel20_Specific_heat_at_constant_pressure = 0.460 
Chromesteel20_Thermal_Conductivity = 22 
Chromesteel20_Thrmal_Diffusivity = 0.635 * 10**-5 
Tungstensteel1_Density = 7913 #Iron with 1 % W 
Tungstensteel1_Specific_heat_at_constant_pressure = 0.448 
Tungstensteel1_Thermal_Conductivity = 66 
Tungstensteel1_Thrmal_Diffusivity = 1.858 * 10**-5 
Tungstensteel5_Density = 8073 #Iron with 5 % W 
Tungstensteel5_Specific_heat_at_constant_pressure = 0.435 
Tungstensteel5_Thermal_Conductivity = 54 
Tungstensteel5_Thrmal_Diffusivity = 1.525 * 10**-5 
Tungstensteel10_Density = 8314 #Iron with 10 % W 
Tungstensteel10_Specific_heat_at_constant_pressure = 0.419 
Tungstensteel10_Thermal_Conductivity = 48 
Tungstensteel10_Thrmal_Diffusivity = 1.391 * 10**-5 
Copper_Density = 8954 
Copper_Specific_heat_at_constant_pressure = 0.3831 
Copper_Thermal_Conductivity = 386 
Copper_Thrmal_Diffusivity = 11.234 * 10**-5 
Aluminiumbronze_Density = 8666 #95 % Cu , 5 % Al  
Aluminiumbronze_Specific_heat_at_constant_pressure = 0.410 
Aluminiumbronze_Thermal_Conductivity = 83 
Aluminiumbronze_Thrmal_Diffusivity = 2.330 * 10**-5 
Magnesium_Density = 1746 
Magnesium_Specific_heat_at_constant_pressure = 1.0130 
Magnesium_Thermal_Conductivity = 171 
Magnesium_Thrmal_Diffusivity = 9.708 * 10**-5 
Molybdenum_Density = 10220 
Molybdenum_Specific_heat_at_constant_pressure = 0.2510 
Molybdenum_Thermal_Conductivity = 123 
Molybdenum_Thrmal_Diffusivity = 4.790 * 10**-5 
Nickel_Density = 8906 
Nickel_Specific_heat_at_constant_pressure = 0.4459 
Nickel_Thermal_Conductivity = 90 
Nickel_Thrmal_Diffusivity = 2.266 * 10**-5 
Silver_Density = 10524 
Silver_Specific_heat_at_constant_pressure = 0.2340 
Silver_Thermal_Conductivity = 419 
Silver_Thrmal_Diffusivity = 17.004 * 10**-5 
Tin_Density = 7034 
Tin_Specific_heat_at_constant_pressure = 0.2265 
Tin_Thermal_Conductivity = 64 
Tin_Thrmal_Diffusivity = 3.884 * 10**-5 
Tungsten_Density = 19350 
Tungsten_Specific_heat_at_constant_pressure = 0.1344 
Tungsten_Thermal_Conductivity = 163 
Tungsten_Thrmal_Diffusivity = 6.271 * 10**-5 
Zinc_Density = 7144 
Zinc_Specific_heat_at_constant_pressure = 0.3843 
Zinc_Thermal_Conductivity = 112.2 
Zinc_Thrmal_Diffusivity = 4.106 * 10**-5 

#nonmetals 

Acoustictile_Thermal_Conductivity = 0.06 #temperature=30  
Acoustictile_Density = 290 
Acoustictile_Specific_heat = 1.3 
Acoustictile_Thermal_Diffusivity = 1.6 * 10**-7 
Aluminiumoxide_Sapphire_Thermal_Conductivity = 46 #temperature=30  
Aluminiumoxide_Sapphire_Density = 3970 
Aluminiumoxide_Sapphire_Specific_heat = 0.76 
Aluminiumoxide_Sapphire_Thermal_Diffusivity = 150 * 10**-7 
Aluminiumoxide_polycrystalline_Thermal_Conductivity = 36 #temperature=30  
Aluminiumoxide_polycrystalline_Density = 3970 
Aluminiumoxide_polycrystalline_Specific_heat = 0.76 
Aluminiumoxide_polycrystalline_Thermal_Diffusivity = 120 * 10**-7 
Asphalt_Thermal_Conductivity = 0.75 #temperature=20-55 
Bakelite_Thermal_Conductivity = 0.23 #temperature=30  
Bakelite_Density = 1200 
Bakelite_Specific_heat = 1.6 
Bakelite_Thrmal_Diffusivity = 1.2 * 10**-7 
Buildingbrick_Common_Thermal_Conductivity = 0.69 #temperature=20  
Bakelite_Density = 1600 
Bakelite_Specific_heat = 0.84 
Bakelite_Thrmal_Diffusivity = 5.2 * 10**-7 
Cement_Portland_Thermal_Conductivity = 0.29 #temperature=23  
Cement_Portland_Anthracite_Density = 1500 
Cement_Mortar_Thermal_Conductivity = 1.16 #temperature=23  
Coal_Anthracite_Thermal_Conductivity = 0.26 #temperature=30  
Coal_Anthracite_Density = 1300 
Coal_Anthracite_Specific_heat = 1.25 
Coal_Anthracite_Thrmal_Diffusivity = 1.6 * 10**-7 
Concrete_Cinder_Conductivity = 0.76 #temperature=23  
Glass_Window_Thermal_Conductivity = 0.78 #temperature=20  
Glass_Window_Density = 2700 
Glass_Window_Specific_heat = 0.84 
Glass_Window_Thermal_Diffusivity = 3.4 * 10**-7 
Glass_Corosilicate_Thermal_Conductivity = 1.09 #temperature=30-75  
Glass_Corosilicate_Density = 2200 
Graphite_Pyrolitic_Paralleltolayers_Thermal_Conductivity = 1900 #temperature=30  
Graphite_Pyrolitic_Paralleltolayers_Density = 2200 
Graphite_Pyrolitic_Paralleltolayers_Specific_heat = 0.71 
Graphite_Pyrolitic_Paralleltolayers_Thermal_Diffusivity = 12200 * 10**-7 
Graphite_Pyrolitic_Perpendiculartolayers_Thermal_Conductivity = 5.6 #temperature=30  
Graphite_Pyrolitic_Perpendiculartolayers_Density = 2200 
Graphite_Pyrolitic_Perpendiculartolayers_Specific_heat = 0.71 
Graphite_Pyrolitic_Perpendiculartolayers_Thermal_Diffusivity = 36 * 10**-7 
Gypsumboard_Thermal_Conductivity = 0.16 #temperature=30  
Lexan_Thermal_Conductivity = 0.2 #temperature=30  
Lexan_Density = 1200 
Lexan_Specific_heat = 1.3 
Lexan_Thermal_Diffusivity = 1.3 * 10**-7 
Nylon_Particleboard_Lowdensity_Thermal_Conductivity = 0.079 #temperature=30  
Nylon_Particleboard_Lowdensity_Density = 590 
Nylon_Particleboard_Lowdensity_Specific_heat = 1.3 
Nylon_Particleboard_Lowdensity_Thermal_Diffusivity = 1.0 * 10**-7 
Nylon_Particleboard_Highdensity_Thermal_Conductivity = 0.17 #temperature=30  
Nylon_Particleboard_Highdensity_Density = 1000 
Nylon_Particleboard_Highdensity_Specific_heat = 1.3 
Nylon_Particleboard_Highdensity_Thermal_Diffusivity = 1.3 * 10**-7 
Phenolic_Thermal_Conductivity = 0.03 #temperature=30  
Phenolic_Density = 1400 
Phenolic_Specific_heat = 1.6 
Phenolic_Thermal_Diffusivity = 0.13 * 10**-7 
Plaster_Gypsum_Thermal_Conductivity = 0.48 #temperature=20  
Plaster_Gypsum_Density = 1440 
Plaster_Gypsum_Specific_heat = 0.84 
Plaster_Gypsum_Thermal_Diffusivity = 4.0 * 10**-7 

















