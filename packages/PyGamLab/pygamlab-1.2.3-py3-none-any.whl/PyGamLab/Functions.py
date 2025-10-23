'''
Functions.py ==>
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


#import-----------------------------------------
import math
import statistics
import random
import numpy as np
import pandas as pd
import matplotlib as plt
from scipy.integrate import quad







def Activation_Energy(k,k0,T):
    """
    Calculates the activation energy (Ea) using the Arrhenius equation.

    Parameters
    ----------
    k : float
        The rate constant at temperature T.
    k0 : float
        The pre-exponential factor (frequency factor).
    T : float
        The temperature in Kelvin.

    Returns
    -------
    float
        The activation energy (Ea) in Joules per mole (J/mol).
    """
    
    K=math.log(k)
    R=8.3144598

    K0=math.log(k0)
    Ea=(K0-K)*R*T
    return Ea 





def Atomic_Packing_Factor(radius , crystal_structure):
    
    '''
    Parameters
    ----------
    
    crystal_structure: Type of the crystal (Fccc , Bcc or ...)
    radiuse (float): Atomic Atomic radius in crystal structure (nm)
    
    Returns:
    Atomic packing factor for SC , BCC , FCC
    
    '''

    if crystal_structure.upper() == "SC":
        volume = (4/3) * math.pi * radius ** 3
        cell_volume = radius * 2 
        APF = volume / cell_volume ** 3
        
    elif crystal_structure.upper() == "BCC":
        volume = (4/3) * math.pi * radius ** 3
        cell_volume = 4 * radius * math.sqrt(3) / 2
        APF = volume / cell_volume ** 3 
        
    elif crystal_structure.upper() == "FCC":
        volume = (4/3) * math.pi * radius ** 3
        cell_volume = 16 * radius / math.sqrt(2)
        APF = volume / cell_volume ** 3
        
    else:
        print("Invalid crystal structure. Please enter SC , BCC or FCC")
        return None
    
    return APF






def Activity_Coef(wB,wC,wD,eBB,eCB,eDB):
    '''
           
    Parameters
    ----------
    wB  : float
          Weight percent of B     
    wC  : float
          Weight percent of C       
    wD  : float
          Weight percent of D       
    eBB : float
          Interaction coefficient of B and B       
    eCB : float
          Interaction coefficient of C and B       
    eDB : float
          Interaction coefficient of D and B       
    
    Returns
    -------
    fB : float
          Activity coefficient of B

    '''
    
    fB=math.e**(eBB*wB+eCB*wC+eDB*wD)
    
    return fB




def Arithmetic_Sequence(start_num,common_difference,n):
    '''
    An arithmetic sequence is an ordered set of numbers that have a common difference between each consecutive term.
    Parameters
    ----------
    start_num : int
        the first term in the sequence.
    common_difference : int
        the common difference between terms.
    n : int
        number of terms.

    Returns
    -------
    a_n	:int
    	the nᵗʰ term in the sequence

    '''
    a_n = start_num + ((n - 1)*common_difference)
    return a_n



def Aeroscope_Stress_Concentration(max_stress, nominal_stresss):
    """
    Calculates the stress concentration factor.

    Parameters
    ----------
    max_stress : float
        The maximum stress experienced by the material.
    nominal_stresss : float
        The nominal stress applied to the material.

    Returns
    -------
    float
        The stress concentration factor (K).
    """
    K = max_stress / nominal_stresss
    return K


def Archimedes_Principle(density_fluid, volume_displaced, gravitational_acceleration):
    """
    Calculates the buoyant force acting on an object submerged in a fluid, based on Archimedes' principle.

    Parameters
    ----------
    density_fluid : float
        The density of the fluid in which the object is submerged (e.g., kg/m^3).
    volume_displaced : float
        The volume of the fluid displaced by the object (e.g., m^3).
    gravitational_acceleration : float
        The acceleration due to gravity (e.g., m/s^2).

    Returns
    -------
    float
        The buoyant force acting on the object (e.g., in Newtons).
    """
    return density_fluid * volume_displaced * gravitational_acceleration

def Atomic_Percentage(n_1,n_2,n_3,n_4,Entry,output,m_1,m_2,m_3,m_4,M_1,M_2,M_3,M_4,w_1,w_2,w_3,w_4):
    '''
    Parameters
    ----------
    n_1 : float
        The number of moles of the first atom.
    n_2 : float
        The number of moles of the second atom.
    n_3 : float
        The number of moles of the third atom.
    n_4 : float
        The number of moles of the fourth atom.
    Entry : str
        what type of entery you have?
    output : str
        The atomic percentage is based on which atom?
    m_1 : float
        The mass of the first atom.
    m_2 : float
        The mass of the second atom.
    m_3 : float
        The mass of the third atom.
    m_4 : float
        The mass of the fourth atom.
    M_1 : float
        The atomic mass of the first atom.
    M_2 : float
        The atomic mass of the second atom.
    M_3 : float
        The atomic mass of the third atom.
    M_4 : float
        The atomic mass of the fourth atom.
    w_1 : float
        The weight percentage of the first atom.
    w_2 : float
        The weight percentage of the second atom.
    w_3 : float
        The weight percentage of the third atom.
    w_4 : float
        The weight percentage of the fourth atom.

    Returns
    -------
    float
        It will return the atomic percentage based on the given inputs.
    '''
    if Entry=='mole':
        if output=='AP_1': #atomic percent for first atom
            AP_1=(n_1)/(n_1+n_2+n_3+n_4)
            return AP_1
        elif output=='AP_2': #atomic percent for second atom
            AP_2=(n_2)/(n_1+n_2+n_3+n_4)
            return AP_2
        elif output=='AP_3': #atomic percent for third atom
            AP_3=(n_3)/(n_1+n_2+n_3+n_4)
            return AP_3
        elif output=='Ap_4': #atomic percent for fourth atom
            AP_4=(n_4)/(n_1+n_2+n_3+n_4)
            return AP_4
    if Entry=='mass':
        if output=='AP_1':
            AP_1=(m_1/M_1)/((m_1/M_1)+(m_2/M_2)+(m_3/M_3)+(m_4/M_4))
            return AP_1
        if output=='AP_2':
            AP_2=(m_2/M_2)/((m_1/M_1)+(m_2/M_2)+(m_3/M_3)+(m_4/M_4))
            return AP_2
        if output=='AP_3':
            AP_3=(m_3/M_3)/((m_1/M_1)+(m_2/M_2)+(m_3/M_3)+(m_4/M_4))
            return AP_3
        if output=='AP_4':
            AP_4=(m_4/M_4)/((m_1/M_1)+(m_2/M_2)+(m_3/M_3)+(m_4/M_4))
            return AP_4
    if Entry=='weight':
        if output=='AP_1':
            AP_1=(w_1/M_1)/((w_1/M_1)+(w_2/M_2)+(w_3/M_3)+(w_4/M_4))
            return AP_1
        if output=='AP_2':
            AP_2=(w_2/M_2)/((w_1/M_1)+(w_2/M_2)+(w_3/M_3)+(w_4/M_4))
            return AP_2
        if output=='AP_3':
            AP_3=(w_3/M_3)/((w_1/M_1)+(w_2/M_2)+(w_3/M_3)+(w_4/M_4))
            return AP_3
        if output=='AP_4':
            AP_4=(w_4/M_4)/((w_1/M_1)+(w_2/M_2)+(w_3/M_3)+(w_4/M_4))
            return AP_4




def Austenite_Martensite_VC(C):
    '''
    This function calaculates the volume change of a unit cell in Austenite to Marteniste transformation.

    Parameters
    ----------
    C : float
        C is the percentage of carbon in chemical composition of steel.

    Returns
    -------
    VC : float
        VC is the percentage of volume change of a unit cell in Austenite to Marteniste transformation.

    '''
    a0 = 3.548 + (0.044 * C)    #Austenite lattice parameter
    V0 = (a0 ** 3) / 2          #Volume of Austenite unit cell (FCC)
    a = 2.861 - (0.013 * C)     #Martensite lattice parameter
    c = 2.861 + (0.116 * C)     #Martensite lattice parameter
    V=c * (a ** 2)              #Volume of Martensite unit cell (BCT)
    Delta_V = V - V0 
    VC = (Delta_V / V0) * 100
    return VC




'''
def BMI_Calculation(W,H):
    '''
    
    This function calculates body mass index
    Parameters
    ----------
    W : float
        Weight in kilograms
    H : float
        height in meters

    Returns
    float
    BMI_Calculation

    '''
    return(W/H**2)
'''




def Biomaterial_Degredation_Rate(W1,W2,T):
    '''
    This function calculates the degradation  rate of biomaterials
    
    Parameters
    ----------
    W1 : int
        initial mass
    W2 : int
        final mass
    T : int
        time of degredation

    Returns
    int
   Biomaterial_Degredation_Rate

    '''
    return((W1-W2)/W1*100/T)     




def Burning_Rate(L, t):
    """
    Calculates the burning rate according to the ASTM D3801 UL-94 test.

    Parameters
    ----------
    L : float
        The burning length in millimeters (mm).
    t : float
        The burning time in seconds (sec).

    Returns
    -------
    float
        The burning rate in millimeters per minute (mm/min).
    """
    V = (60 * L) / t
    return V




def Boyles_Law(initial_volume, initial_pressure, final_volume):
    """
    Calculates the final pressure based on Boyle's Law (assuming constant temperature).

    Parameters
    ----------
    initial_volume : float
        The initial volume of the gas.
    initial_pressure : float
        The initial pressure of the gas.
    final_volume : float
        The final volume of the gas.

    Returns
    -------
    float
        The final pressure of the gas.
    """
    return (initial_pressure * initial_volume) / final_volume


def Boltzmann_Distribution(energy, temperature, boltzmann_constant):
    """
    Calculates the probability of a particle being in a specific energy state according to the Boltzmann distribution.

    Parameters
    ----------
    energy : float
        The energy of the specific state.
    temperature : float
        The temperature of the system in Kelvin.
    boltzmann_constant : float
        The Boltzmann constant (approximately 1.380649 × 10^-23 J/K).

    Returns
    -------
    float
        The probability of the particle being in the specified energy state.
    """
    return math.exp(-energy / (boltzmann_constant * temperature))


def Bragg_Law (h,k,l,a,y):
    '''
    This function calculate the diffraction angle of a incidence wavelenght through a crytal special plate

    Parameters
    ----------
    h : int
        x direction of the plate.
    k : int
        y direction of the plate.
    l : int
        z direction of the plate.
    a : float
        Unit Cell.
    y : float
       incidence wavelenght.

    '''
    square_sin_teta=(((y**2)*((h**2)+(k**2)+(l**2))))/4*a**2
    teta=math.asin((square_sin_teta)**1/2)
    
    return teta*180/math.pi






def Beer_Lambert_Law (a,l,I0):
    '''
    This function caclculate the output light intensity when a light pass through a material
    Parameters
    ----------
    a : float
        absorption coefficient.
    l : float
        length.
    I0 : float
        incomming light intensity.

    Returns
    -------
    I : float
        output light intensity.

    '''
    I=I0*(10**(-a*l))
    return I
    



def Binomial_Probability(n,k,p):
    """
    

    Parameters
    ----------
    p :float
        ehtemal voghoo beyn 0ta 1
    n:int
        tedad dafat azmayesh
    K:int
        tedad dafaat bord

    return ehtemal rokh dadan pishamad dar fazaye do pishamadi(bord,shekast)
     ba tedad n azmayesh va tedad k  bord


    """
    q=1-p
    return p**k*q**(n-k)



def Bouyancy_Force(d, V):
    """
    Calculates the buoyant force acting on an object submerged in a fluid.

    Parameters
    ----------
    d : float
        The density of the fluid (e.g., in kg/m^3).
    V : float
        The volume of the fluid displaced by the object (e.g., in m^3).

    Returns
    -------
    float
        The buoyant force in Newtons (N).
    """
    g = 9.81  # Acceleration due to gravity (m/s^2)
    F_b = d * g * V
    return F_b




def Brinell_Hardness_Calculation (d1,d2,D,p): 
    
    '''
    this function is utilized for calculating Brinell hardness.
    characterizes the indentation hardness of materials through the
    scale of penetration of an indenter, loaded on a material test-piece. 
    It is one of several definitions of hardness in materials science.
    In this method, steel ball indentor is used.
    
     Parameters
     ----------- 
            1. d1: float
            d1 represents diameter of impress of indentor.
            
            2. d2 : float
            d2 represents diameter of impress of indentor
            
            3. D : float
            diameter of indenter
            
            3. p : int
            applied load 
     
            Returns --> BHN (Brinell Hardness Number)
    '''
    
    d = (d1+d2)/2
    BHN = (2*p)/(3.14*D)(D-(math.sqrt(D**2 - d**2)))

    return BHN


def Calculate_Hardness_From_Young_And_Poisson(E, nu):
    """
    Estimate Vickers hardness (HV) from Young’s modulus and Poisson’s ratio.

    Parameters
    ----------
    E : float
        Young’s modulus (GPa).
    nu : float
        Poisson’s ratio (dimensionless).

    Returns
    -------
    float
        Estimated Vickers hardness (HV) in GPa.
    """
    hardness = 0.151 * E / (1 - 2 * nu)
    return round(hardness, 2)



def Calculate_Debye_Temperature(velocity, atomic_mass, density, n_atoms):
    """
    Estimate the Debye temperature (θ_D) of a solid material.

    Parameters
    ----------
    velocity : float
        Average sound velocity in m/s.
    atomic_mass : float
        Atomic mass of the element (in g/mol).
    density : float
        Density of the material (in kg/m^3).
    n_atoms : int
        Number of atoms per formula unit.

    Returns
    -------
    float
        Debye temperature in Kelvin (K).
    """
    kB = 1.380649e-23  # J/K
    h = 6.62607015e-34  # J·s
    NA = 6.02214076e23  # 1/mol

    m = atomic_mass / 1000 / NA  # convert to kg/atom
    V = m / density              # volume per atom

    theta_D = (h / kB) * velocity * ((6 * np.pi**2 * n_atoms / V)**(1/3))
    return round(theta_D, 2)




def Corrosion_Rate(W,D,A,t):
    '''
    

    Parameters
    ----------
    W : int or float
        The change in weight of specimen (mg)      
    D : int or float
        The density of specimen (g/cm^3)      
    A : int or float
        The surface area of specimen (in^2)      
    t : int or float
        The time(h)

    Returns
    -------
    CR : int or float
         The corrosion rate (mpy)

    '''
    
    CR=534.6*W/(D*A*t)
    return CR




def Calculate_ECB(chi, Ee, Eg):
    
    '''
    This function calculates the conduction band edge energy (ECB) of a semiconductor using Mulliken electronegativity theory.

    Parameters
    ----------
    chi : float
        The absolute electronegativity of the semiconductor (eV), calculated as the geometric mean of the absolute electronegativity
        of the constituent elements. For ZnO, chi=sqrt(chi_Zn*chi_O)=5.79 eV.
        
    Ee : float
        The energy of free electrons on the standard hydrogen electrode (SHE) scale (eV). For standard scale, Ee=4.5 eV.
    
    Eg : float
        The bandgap energy of the semiconductor (eV). For ZnO, Eg=3.23 eV.

    Returns
    -------
    ECB : float
        The conduction band edge energy (eV).

    '''
    
    ECB=chi-Ee+0.5*Eg
   
    return (ECB)






def Circle_Area(radius):
    '''
    

    Parameters
    ----------
    radius : int
        radius of circle.

    Returns
    -------
    circle_area:int
        area of circle.

    '''
    circle_area=(radius**2)*math.pi
    return circle_area



    
def Circle_Perimeter(radius):
    '''
    

    Parameters
    ----------
    radius : int
        radius of circle.

    Returns
    -------
    circle_perimeter: int
        perimeter of circle.

    '''
    circle_perimeter=2*math.pi*radius
    return circle_perimeter
    




def Coulombs_Law(charge1, charge2, distance):
    """
    Calculates the electrostatic force between two point charges using Coulomb's Law.

    Parameters
    ----------
    charge1 : float
        The magnitude of the first charge (in Coulombs).
    charge2 : float
        The magnitude of the second charge (in Coulombs).
    distance : float
        The distance between the two charges (in meters).

    Returns
    -------
    float
        The electrostatic force between the charges (in Newtons).
    """
    k_constant = 8.9875e9  # Coulomb's constant (N·m^2/C^2)
    return k_constant * (charge1 * charge2) / distance**2




def Convert_Gas_Constant(gas_constant , from_unit , to_unit):
    """
    Converts the gas constant from one unit to another.

    Parameters
    ----------
    gas_constant : float
        The value of the gas constant in the initial unit.
    from_unit : str
        The initial unit of the gas constant (e.g., "J/mol.K", "cal/mol.K", "atm.L/mol.K", "cm^3.atm/mol.K").
    to_unit : str
        The desired unit for the gas constant (e.g., "J/mol.K", "cal/mol.K", "atm.L/mol.K", "cm^3.atm/mol.K").

    Returns
    -------
    float or str
        The converted value of the gas constant in the desired unit, or "Invalid" if the units are not recognized.
    """
    
    conversion_factors = {
        "J/mol.K": {
            "J/mol.K": 1 ,
            "cal/mol.K": 0.239 , 
            "atm.L/mol.K": 8.314 , 
            "cm^3.atm/mol.K": 82.057 , 
        } , 
        "cal/mol.K": {
            "J/mol.K": 4.184 ,
            "cal/mol.K": 1 , 
            "atm.L/mol.K": 24.205 ,
            "cm^3/mol.K": 239.006 , 
        } ,
        "atm.L/mol.K": {
            "J/mol.K": 0.0821 ,
            "cal/mol.K": 0.042 , 
            "atm.L/mol.K": 1 ,
            "cm^3/mol.K": 10 
        } , 
        "cm^3/mol.K": {
            "J/mol.K": 0.001987 ,
            "cal/mol.K": 0.0042 , 
            "atm.L/mol.K": 0.1 ,
            "cm^3/mol.K": 1
        }
    }

    if from_unit in conversion_factors and to_unit in conversion_factors[from_unit]:
        conversion_factors = conversion_factors[from_unit][to_unit]
        converted_value = gas_constant * conversion_factors
        
        return converted_value
    
    else:
        return "Invalid"





def Carnot_Efficiency(T_c , T_h): 
    
    '''
    Parameters
    ----------
    
    T_hot (float): Hot source temperature (Kelvin)
    T_cold (float): Cold source temperature (Kelvin)
    
    Returns:
    float : Efficiency of the cycle 
    
   '''
    try:
        if T_h <= 0 or T_c <=0:
            raise ValueError("Temperature must be +!")
        efficiency = 1 - (T_c / T_h)
        return efficiency 
        
    except ValueError as e:
        print(f"ERROR: {e}")







def Contact_Angle(num1,num2,num3):
    '''
    

    Parameters
    ----------
    num1 : float
        a solid and atmospher surface tenssion.
    num2 : float
        a liquid and atmospher surface tension.
    num3 : float
        a solid and liquid boundary tension.

    Returns
    degrees

    '''
    
    costeta= (num1-num3)/num2
    teta = math.acos(costeta)
    teta_degree= teta*180/math.pi
    return teta_degree







def Copolymer_Type(Copolymer, Polymer_num=2):
    '''
    Copolymer: str
    Unit types are shown by charachters which are seperated by a space
    Example: 'polymer_A polymer_A polymer_B polymer_A polymer_A polymer_B'
    
    Polymer_num: int
    It represents the number of polymers in this structure which could be 2 or 3
    default = 2
    '''
    valid = [2, 3]
    if Polymer_num not in valid:
        raise ValueError('Polymer_num should be 2 or 3')
    
    co_list = Copolymer.split()
    change = []
    unique = 0
    unique_list = []
    for i in range(1,len(co_list)):
        if co_list[i-1] not in unique_list:
            unique_list.append(co_list[i-1])
            unique += 1
        if co_list[i] != co_list[i-1]:
            change.append(True)
        else:
            change.append(False)
            
    if change.count(True) == 0:
        print('Error: It is not a copolymer') 
    elif Polymer_num != unique:
        print('Error: The number of unique units in the copolymer is not compatible with the Polymer_num entered')
    elif Polymer_num == 2:
        if change.count(False) == 0:
            copolymer_type = 'Alternative'
            print(copolymer_type)
        elif change.count(True)==1:
            copolymer_type = 'Block'
            print(copolymer_type)
        else:
            copolymer_type = 'Random'
            print(copolymer_type)
        return copolymer_type
      
      


'''
def Cost_Indicators(ac, ev):
    """
    Calculates the Cost Variance (CV) and Cost Performance Index (CPI).

    Parameters
    ----------
    ac : float
        The Actual Cost of Work Performed (ACWP).
    ev : float
        The Earned Value (EV).

    Returns
    -------
    tuple
        A tuple containing the Cost Variance (cv) and Cost Performance Index (cpi).
    """
    cv = ev - ac
    cpi = ev / ac
    return cv, cpi
'''

def Crystal_Percent(H, W, H100):
    """
    Calculates the percentage of crystallinity in a polymer.

    Parameters
    ----------
    H : float
        The enthalpy of the polymer in milliJoules (mJ).
    W : float
        The weight of the polymer in milligrams (mg).
    H100 : float
        The enthalpy for a 100% crystalline polymer in Joules per gram (J/g).

    Returns
    -------
    float
        The crystallinity of the polymer in percent (%).
    """
    Xc = ((H / W) / (H100 * 1000 / 1000)) * 100  # Convert H100 to mJ/mg
    return Xc



def Calculate_Pipe_Heat_Transfer(mu,muW,rho,Cp,Pr,K,u,d,l,Tw,Tb1):
    '''
    Parameters
    ----------
    mu : float
        Fluid dynamic viscosity (pa.s).
    muW : float
        Dynamic viscosity at wall temperature (pa.s).
    rho : float
        fluid density (kg/m³).
    Cp : float
        DESCRIPTION.
    Pr : float
        Prantel number.
    K : flout
        Thermal conductivity(W/m.K).
    u : float
       fluid velocity (m/s).
    d : float
        Pipe diameter (m).
    L : float
        Pipe length (m).
    Tw : float
        Pipe wall temperature.
    Tb1 : float
        Average fluid temperature().

    Returns
    Reynolds number, Nusselt number, convective heat transfer coefficient, total heat transfer, and outlet temperature.
    -------
    None.

    '''

    
    Re=(rho*u*d)/mu
    if Re<2000:
        print('flow type laminar')
        if (Re*Pr*(d/l))>10:
            Nu=1.86*(Re*Pr)**(1/3)*(d/l)**(1/3)*(mu/muW)**0.14#####برای لوله های طویل صادق نیست(1) .
        else:
            Nu=3.66####برای لوله های طویل و دمای ثابت در جداره لوله 
    elif 2500<Re<(1.25*(10**5)) and 1.5<Pr<100:
        print('flow type Turbulent')
        if Tw>Tb1:
            n=0.4
        else:
            n=0.3
        Nu=(0.023*(Re**0.8)*(Pr**n))##(2)
    else:
        return None
    h = (Nu * K) / d
    A=3.14*d*l
    Tb2 =Tb1+(h*A*(Tw-Tb1))/(rho*Cp*u) 
    Q=((rho*A*u)*Cp*(Tb2-Tb1))
    return {Re,Nu,h,Q,Tb2}   






def Cohen(m,r,/):
    '''
  Cohen equation is used to predict the yield stress of a polymeric blend  containing a rubbery dispersion phase. 

    Parameters
    ----------
    m : int or float
        The yield stress of polymeric matrix, N/m^2 or Pa or ...
    r : float
        Volume fraction of rubbery phase, 0<r<1.

    Returns
    -------
    b : int or float
    The yield stress of polymeric blend, N/m^2 or Pa or ...

    '''
    a=(1-1.21*math.pow(r,(2/3)))
    b=m*a
    return b
    
       


 
def Critical_Diameter(d,r,/):
    '''
    This equation predicts the critical diameter of rubber particles toughening a polymeric matrix.
    Parameters
    ----------
    d : int or float
        critical distance between rubbery particles, angstrom or mm or nm or .....
    r : float
        Volume fraction of rubbery phase, 0<r<1.

    Returns
    -------
    dc : int or float
    the critical diameter of rubber particles

    '''
    a=6*math.pow(r,(1/3))
    b=a-1
    c=3.14/b
    dc=d/c
    return dc





def Component(a,b):
    '''

    Parameters
    ----------
    a : list
        multi-dimensional vector
    b : list
        multi-dimensional vector

    Returns
    -------
   c : float
       The component of b on a

    '''
    ab=0
    aa=0
    for i in range(0,len(a)):
           ab=ab+a[i]*b[i]
           aa=aa+a[i]*a[i]
    aas=math.sqrt(aa)
    c=(ab/aas)
    return c





def Change_In_Pressure_Of_a_Mercury_OR_Water_Column_Manometer(Type_Of_Fluid, h, g=9.81):
    """
    Calculates the change in pressure in Pascals (Pa) for a mercury or water column manometer.

    Parameters
    ----------
    Type_Of_Fluid : str
        The type of fluid in the manometer ('water' or 'mercury'). Case-insensitive.
    h : float
        The height difference in the manometer column in meters (m).
    g : float, optional
        The acceleration due to gravity in meters per second squared (m/s^2). Defaults to 9.81.

    Returns
    -------
    float
        The change in pressure (Delta_P) in Pascals (Pa).

    Raises
    ------
    ValueError
        If the Type_Of_Fluid is not 'water' or 'mercury'.
    """
    if Type_Of_Fluid.upper() == 'WATER':
        Delta_P = 1000 * h * g  # Density of water ≈ 1000 kg/m^3
        return Delta_P

    elif Type_Of_Fluid.upper() == 'MERCURY':
        Delta_P = 13600 * h * g  # Density of mercury ≈ 13600 kg/m^3
        return Delta_P

    else:
        raise ValueError("Invalid Type of Fluid. Choose 'water' or 'mercury'.")
        
        



def Concentration_Calculator (CA1, unit_CA1, CA2, unit_CA2, Q1, unit_Q1, Q2, unit_Q2):
    '''
    Parameters
    ----------
    CA1 : float
        Concentratoion of the first flow
    unit_CA1: str
        Unit of concentratoion of the first flow
    CA2 : float
        DESCRIPTION.Concentratoion of the second flow
    unit_CA2: str
        Unit of concentratoion of the second flow
    Q1 : float
        Molar volume of the first flow
    unit_Q1: str
        Unit of molar volume of the first flow
    Q2 : float
        Molar volume of the second flow
    unit_Q2: str
        Unit of molar volume of the second flow

    Returns
    -------
    Flowrate and concentration of the output flow
    '''
    
    if unit_CA1== 'mole/lit':
        CA1= CA1*1000
    elif unit_CA1== 'mole/ml':
        CA1= CA1*1000000
        
    if unit_CA2== 'mole/lit':
        CA2= CA2*1000
    elif unit_CA2== 'mole/ml':
        CA2= CA2*1000000
        
    if unit_Q1== 'lit':
        Q1= Q1/1000
    elif unit_Q1== 'ml' or unit_Q1== 'cc':
        Q1= Q1/1000000 
        
    if unit_Q2== 'lit':
            Q2= Q2/1000
    elif unit_Q2== 'ml' or unit_Q2== 'cc':
            Q2= Q2/1000000 
            
    V_out = Q1+Q2
    C_out= (CA1*Q1 + CA2*Q2)/V_out
    return V_out
    return C_out





def Convective_Heat_Transfer_Internal_Flow_Dittus_Boelter(Re, Pr, fluid_thermal_conductivity, hydraulic_diameter, delta_T, length, heating=True):
    """
    Calculates the convective heat transfer rate for fully developed turbulent
    flow inside a smooth circular tube using the Dittus-Boelter correlation.
    This is a widely used empirical correlation in heat exchanger design and
    thermal analysis of internal flows.

    Parameters
    ----------
    Re : float
        The Reynolds number of the flow (dimensionless, Re > 10000 for turbulent flow).
    Pr : float
        The Prandtl number of the fluid (dimensionless).
    fluid_thermal_conductivity : float
        The thermal conductivity of the fluid (in W/(m*K)).
    hydraulic_diameter : float
        The hydraulic diameter of the tube (in meters). For a circular tube,
        this is simply the inner diameter.
    delta_T : float
        The temperature difference between the surface and the bulk fluid
        (in Kelvin).
    length : float
        The length of the tube over which heat transfer occurs (in meters).
    heating : bool, optional
        A boolean indicating whether the fluid is being heated (True) or cooled (False).
        This affects the exponent of the Prandtl number. Defaults to True (heating).

    Returns
    -------
    float
        The convective heat transfer rate (in Watts).
    """
    if Re <= 10000:
        raise ValueError("Reynolds number must be greater than 10000 for turbulent flow.")
    if Pr < 0.6 or Pr > 100:
        raise ValueError("Prandtl number must be in the range [0.6, 100].")

    n = 0.4 if heating else 0.3
    Nu = 0.023 * (Re**0.8) * (Pr**n)  # Nusselt number
    h = (Nu * fluid_thermal_conductivity) / hydraulic_diameter  # Convective heat transfer coefficient
    area = math.pi * hydraulic_diameter * length  # Heat transfer area
    q_conv = h * area * delta_T
    return q_conv



def Density(m, V):
    '''
    It's the formula for obtaining density.
    
    Parameters:
    ----------
    m : float
        Mass
    
    V: float
        volume
    '''
    den = m / V       
    return den




def Drag_Force(Velocity, Fluid_Coefficent, Fluid_Density, cross_sectional_area):
    """
    Calculates the drag force acting on an object moving through a fluid.

    Parameters
    ----------
    Velocity : float
        The velocity of the object relative to the fluid (e.g., in m/s).
    Fluid_Coefficent : float
        The drag coefficient (dimensionless).
    Fluid_Density : float
        The density of the fluid (e.g., in kg/m^3).
    cross_sectional_area : float
        The cross-sectional area of the object perpendicular to the direction of motion (e.g., in m^2).

    Returns
    -------
    float
        The drag force acting on the object (e.g., in Newtons).
    """
    D = 0.5 * (Velocity**2) * (Fluid_Density) * (Fluid_Coefficent) * (cross_sectional_area)
    return D
    




def Degradation_Percentage(C0,Ct):
    
    '''
    This function calculates the degradation percentage of a pollutant solution in a photocatalytic process.

    Parameters
    ----------
    C0: float
        Initial concentration of the pollutant solution (mg/L)
    
    Ct: float
        Concentration of the pollutant solution at a certain time interval (mg/L)

    Returns
    -------
    Percentage: float
        The degradation percentage (%) of the pollutant solution.

    '''
   
    Percentage=(1-(Ct/ C0))*100
    
    return (Percentage)





def Darcys_Law(flow_rate, permeability, area, pressure_difference):
    """
    Calculates the value related to Darcy's Law for flow through a porous medium.
    Note: The formula provided returns the difference, not a direct calculation of a single variable.

    Parameters
    ----------
    flow_rate : float
        The volumetric flow rate of the fluid through the medium.
    permeability : float
        The permeability of the porous medium.
    area : float
        The cross-sectional area through which the fluid is flowing.
    pressure_difference : float
        The pressure difference across the porous medium.

    Returns
    -------
    float
        The result of the expression: (permeability * area * pressure_difference) - flow_rate.
        To solve for a specific variable, rearrange this equation.
    """
    return permeability * area * pressure_difference - flow_rate


def Doppler_Effect(observed_frequency, source_frequency, velocity_observer, velocity_source, speed_of_sound):
    """
    Calculates the observed frequency of a wave due to the Doppler effect.

    Parameters
    ----------
    observed_frequency : float
        The frequency of the wave as perceived by the observer.
    source_frequency : float
        The frequency of the wave emitted by the source.
    velocity_observer : float
        The velocity of the observer relative to the medium (positive if moving towards the source).
    velocity_source : float
        The velocity of the source relative to the medium (positive if moving away from the observer).
    speed_of_sound : float
        The speed of the wave in the medium.

    Returns
    -------
    float
        The calculated observed frequency.
    """
    return source_frequency * ((speed_of_sound + velocity_observer) / (speed_of_sound - velocity_source))


def Diffusivity(MA, MB, T, rAB, K, εAB, f, Pt=1.013*10**5):
    """
    Calculates the binary gas-phase diffusivity using a modified Chapman-Enskog equation.
    Note: The formula seems to have a sign issue based on typical diffusivity calculations.

    Parameters
    ----------
    MA : str
        The chemical symbol or identifier for gas A (must be a key in the 'M' dictionary).
    MB : str
        The chemical symbol or identifier for gas B (must be a key in the 'M' dictionary).
    T : float
        The temperature in Kelvin (K).
    rAB : float
        The average collision diameter between molecules A and B (in Angstroms, Å).
    K : float
        A dimensionless collision integral parameter (related to the Lennard-Jones potential).
    εAB : float
        The Lennard-Jones energy parameter for the pair A-B (in Kelvin, K).
    f : float
        A correction factor (dimensionless).
    Pt : float, optional
        The total pressure in Pascals (Pa). Defaults to 1.013 * 10**5 (1 atm).

    Returns
    -------
    float or str
        The binary gas-phase diffusivity (DAB) in m^2/s, or "Invalid inputs" if MA or MB are not recognized.
    """
    M = {
        'Carbon' '(C)': 0.01201,  # kg/kmol
        'Hydrogen' '(H)': 0.001008,  # kg/kmol
        'Chlorine' '(Cl)': 0.03545,  # kg/kmol
        'Bromine' '(Br)': 0.07990,  # kg/kmol
        'Iodine' '(I)': 0.12690,  # kg/kmol
        'Sulfur' '(S)': 0.03207,  # kg/kmol
        'Nitrogen' '(N)': 0.01401,  # kg/kmol
        'H2': 0.002016,  # kg/kmol
        'O2': 0.03200,  # kg/kmol
        'N2': 0.02802,  # kg/kmol
        'Air': 28.97,  # kg/kmol for dry air
        'CO': 0.02801,  # kg/kmol
        'CO2': 0.04401,  # kg/kmol
        'SO2': 0.06407,  # kg/kmol
        'NO': 0.03001,  # kg/kmol
        'N2O': 0.04402,  # kg/kmol
        'Oxygen': 0.03200,  # kg/kmol
        'NH3': 0.01703,  # kg/kmol
        'H2O': 0.01802,  # kg/kmol
        'H2S': 0.03408,  # kg/kmol
        'COS': 0.06007,  # kg/kmol
        'Cl2': 0.07090,  # kg/kmol
        'Br2': 0.15980,  # kg/kmol
        'I2': 0.25380,  # kg/kmol
        'C3H6O': 0.05808  # kg/kmol
    }

    if MA in M and MB in M:
        AB = float(((((((1 / M[MA]) ** 0.5 + (1 / M[MB]) ** 0.5) * 0.249) - 1.084) * (10 ** -4)) * T ** (3 / 2)) * ((1 / M[MA]) ** 0.5 + (1 / M[MB]) ** 0.5))
        DAB = float((AB / (((rAB ** 2) * Pt) * ((K * T / εAB) * f))) * 1e-10)  # Converted from m^2/s * Pa * K to m^2/s, and likely needs a sign correction
        return DAB
    else:
        return "Invalid inputs"


def Diffusion_in_Gases(Diffusion_Type, Diffusivity, Separate_Panels_Distance, Pressure_in_Panel_A, Pressure_in_Panel_B, PressureBM, Gas_Constant, Total_Pressure=1.013*10**5):
    """
    Calculates the molar flux (N_A) for diffusion in gases under different conditions.

    Parameters
    ----------
    Diffusion_Type : str
        The type of diffusion: 'Two_way_equimolal_diffusion' or 'one-way_diffusion'.
    Diffusivity : str
        A key representing the gas pair for which the diffusivity is known (e.g., 'H2_CH4').
    Separate_Panels_Distance : float
        The distance between the two panels or points of measurement (in meters, m).
    Pressure_in_Panel_A : float
        The partial pressure of component A at point 1 (in Pascals, Pa).
    Pressure_in_Panel_B : float
        The partial pressure of component A at point 2 (in Pascals, Pa).
    PressureBM : float
        The log mean pressure of the non-diffusing component B (in Pascals, Pa) - used for one-way diffusion.
    Gas_Constant : float
        The ideal gas constant (in J/(mol·K)).
    Total_Pressure : float, optional
        The total pressure of the system (in Pascals, Pa). Defaults to 1.013 * 10**5.

    Returns
    -------
    float
        The molar flux of component A (N_A) in mol/(m^2·s).
    """
    DAB_values = {'H2-CH4': 6.25e-5,  # m^2/s
                  'O2-N2': 1.81e-5,
                  'CO-O2': 1.85e-5,
                  'CO2-O2': 1.39e-5,
                  'Air-NH3': 1.98e-5,
                  'Air-H2O': 2.58e-5,
                  'Air-ethanol': 1.02e-5,
                  'Air-ethyl-acetate': 0.87e-5,
                  'Air-aniline': 0.74e-5,
                  'Air-chlorobenzene': 0.74e-5,
                  'Air-toluene': 0.86e-5}

    Temp_values = {'H2-CH4': 273.15,  # Kelvin
                   'O2-N2': 273.15,
                   'CO-O2': 273.15,
                   'CO2-O2': 273.15,
                   'Air-NH3': 273.15,
                   'Air-H2O': 299.05,
                   'Air-ethanol': 299.05,
                   'Air-ethyl-acetate': 274.2,
                   'Air-aniline': 299.05,
                   'Air-chlorobenzene': 299.05,
                   'Air-toluene': 299.05}

    diffusivity_key = Diffusivity.replace('_', '-')

    if Diffusion_Type == 'Two_way_equimolal_diffusion':
        if diffusivity_key in DAB_values and diffusivity_key in Temp_values:
            NA_Two = (DAB_values[diffusivity_key] / (Gas_Constant * Temp_values[diffusivity_key] * Separate_Panels_Distance)) * (Pressure_in_Panel_A - Pressure_in_Panel_B)
            return NA_Two
        else:
            return "Invalid Diffusivity key for Two-way equimolal diffusion"
    elif Diffusion_Type == 'one-way_diffusion':
        if diffusivity_key in DAB_values and diffusivity_key in Temp_values:
            NA_One = ((DAB_values[diffusivity_key] * Total_Pressure) / (Gas_Constant * Temp_values[diffusivity_key] * Separate_Panels_Distance * PressureBM)) * (Pressure_in_Panel_A - Pressure_in_Panel_B)
            return NA_One
        else:
            return "Invalid Diffusivity key for One-way diffusion"
    else:
        return "Invalid Diffusion Type"
    
    





def Defect_Density(Beta,Theta,K=0.9,Landa=1.5406):
    '''
    
    Parameters
    ----------
    Beta : Float
        Full width at half maximum (FWHM).
    Theta : Float
        Bragg's Diffraction Angle.
    K : Float, optional
        Scherrer Constant. The default = 0.9.
    Landa : Float, optional
        X-ray Wavelength. The default = 1.5406.
    

    Returns
    -------
    D : Float
        Crystallite size (nm)
    Delta : Float
        Density of defect for crystallite structures from XED crystallography calculated from reverse the Scherrer Equation.

    '''
    Theta=math.radians(Theta)
    D=(K*Landa)/(Beta*math.cos(Theta))
    Delta=1/(D**2)
    return D,Delta




def Diffusion_Coefficient_Calculator(Peak_Current,A,C,Scan_Rate,n,is_reversible):
    '''
    

    Parameters
    ----------
    Peak_Current : Float
        Peak of current (A).
    A : Float
        Electrode area (cm**2).
    C : Float
        Concentration of electroactive species (mol/L).
    Scan_Rate : Float
    (mV/s)
    n : int
    number of transfered electron
    is_reversible: bool
        Type of reaction. 'True' is reversible, 'False' is irreversible

    Returns
    -------
    Diffusion Coefficient calculates from Randles-Sevcik aquation. type:float

    '''
    
    if is_reversible.upper()=='TRUE':
        Diffusion_Coefficient=(Peak_Current/((2.65*10**5)*(n**(3/2))*A*C*(Scan_Rate**(1/2))))**2
        
    elif is_reversible.upper()=='FALSE':
        Diffusion_Coefficient=(Peak_Current/(0.446*(n**(3/2))*A*C*(Scan_Rate**(1/2))))**2
        
    else:
        raise TypeError ('Please enter a valid answer (yes or not)') 
    
    return(Diffusion_Coefficient)



def Distance(x,y,z,a,b,c,d):
    '''
    The formula of the distance between a point and a plane in
    three-dimensional space is as follows:
        D=(abs(a*x+b*y+c*z+d))/sqrt(a**2+b**2+c**2)

    Parameters
    ----------
    x : int
        The x-axis component.
    y : int
        The y-axis component.
    z : int
        The z-axis component.
    a : int
        The coefficient of x in the plane equation.
    b : int
        The coefficient of y in the plane equation.
    c : int
        The coefficient of z in the plane equation.
    d : int
        The constant in the plane equation.

    Returns
    -------
    D : float
        The distance of point-to-plane
        
   Example : Distnace between (1,-2,4) and the plane 13*x-6*y-5*z+3=0
             is    0.527 

    '''
    if a==b==c==0:
        return None
    else:
        tt=abs(a*x+b*y+c*z+d)
        ss=math.sqrt(a**2+b**2+c**2)
        D=tt/ss
        return D



def Debye_Temperature_Heat_Capacity(T, TD):
    """
    Calculates the dimensionless heat capacity according to the Debye model,
    a solid-state physics model that approximates the contribution of phonons
    (lattice vibrations) to the specific heat of a solid.

    Parameters
    ----------
    T : float
        The absolute temperature in Kelvin (K).
    TD : float
        The Debye temperature of the material in Kelvin (K), a characteristic
        temperature related to the material's lattice vibrations.

    Returns
    -------
    float
        The dimensionless heat capacity (Cv / (9 * n * k_B)), where n is the
        number of atoms and k_B is the Boltzmann constant. To get the actual
        heat capacity, this value needs to be multiplied by 9 * n * k_B.
    """
    if T == 0:
        return 0
    x = TD / T
    integral_result = 0
    n = 100  # Number of integration steps
    dx = x / n
    for i in range(1, n + 1):
        xi = i * dx
        integral_result += (xi**4 * math.exp(xi)) / ((math.exp(xi) - 1)**2) * dx
    return (3 / x**3) * integral_result





def Error_Function(z):
    '''
    

    Parameters
    ----------
    z : int or float
        Error function argument

    Returns
    -------
    erf : float
        error function value

    '''
    erf=0
    if z<0:
        z=-z
    t=0
    d=0.00001
    while t<z:
        f1=math.e**(-t**2)
        f2=math.e**(-(t+d)**2)
        erf=erf+(2/(math.pi**0.5))*((f1+f2)*d/2)
        t=t+d
        
    erf=int(erf*1000000)/1000000
    return erf
     


def Encapsulation_Efficiency(W1,W2 ):
    '''
This function calculates the percentage of drug loaded in the carrier during drug delivery

    Parameters
    ----------
    W1 : float
        weight of free drug
    W2 : float
        weight of total drug

    Returns
    float
    Encapsulation_Efficiency
        

    '''
                
    return 1-(W1/W2)*100





def Entropy_Change(heat_transfer, temperature):
    """
    Calculates the change in entropy of a system.

    Parameters
    ----------
    heat_transfer : float
        The amount of heat transferred to or from the system (in Joules).
    temperature : float
        The absolute temperature at which the heat transfer occurs (in Kelvin).

    Returns
    -------
    float
        The change in entropy (in Joules per Kelvin).
    """
    return heat_transfer / temperature




def Elastic_Potential_Energy(spring_constant, displacement):
    """
    Calculates the elastic potential energy stored in a spring.

    Parameters
    ----------
    spring_constant : float
        The spring constant (in Newtons per meter).
    displacement : float
        The displacement of the spring from its equilibrium position (in meters).

    Returns
    -------
    float
        The elastic potential energy stored in the spring (in Joules).
    """
    return 0.5 * spring_constant * displacement**2


def Electrical_Resistance(v,i):
    '''
    Parameters
    ----------
    This function receives the variables i, v and returns the variable R
    v : int
        Voltage or potential difference between two points
    i : int
        I is the electric current that passes through a circuit
    R : It represents electrical resistance.

    Returns
    -------
    '''
    R =v/i
    return R





def Euler_Diff_Solver(a , b, xf , h , x0 =0 ,y0 =0 ):
    '''
    This function solve linear differential equation of the following form: 
        yprim = dy/dx = f(x,y) = a*x^2 + b*x
    by the Euler's method that is a numerical method for 
    approximating differential equations.    

    Parameters
    ----------
    a : float
        Polynomial coefficient..
    b : float
        Polynomial coefficient.
    xf : float
        Independent variable's final value.
    h : float
        Step size.        
    x0 : float, optional
        Independent variable's initial value. The default is 0.
    y0 : float, optional
        Initial function value at x0 (y0 = y(x0)). The default is 0.

    Raises
    ------
    TypeError
        The quadratic coefficient of the equation should not be zero.

    Returns
    -------
    y : float
        Returns function value at desired point (xf) or y(xf).

    '''
    
    if a == 0:
        raise TypeError('The coefficient a should not be zero')
        return
    varL =  xf - x0
    varLL = int(varL/h)
    for i in range(varLL):
        y = Euler_Method(a,b,x0,y0,h)
        y0 = y
        x0 = x0 +h
    return y   
   
    



def Euler_Method(a,b, h, x0,y0):
    
    '''
    Euler's method law: y = y0 + h *yprim 

    Parameters
    ----------
    a : float
        Polynomial coefficient.
    b : float
        polynomial coefficient.
    x0 : float
        Initial value.
    y0 = y(x0) : float
        function value.
    h : float
        Step size.

    Returns
    -------
    This function returns function value (y) at specific value (x).

    '''
    var1 = x0;
    yprim = a*(var1**2)+b*var1;
    y = y0 + h *yprim # Euler's method
    return y








def First_Row_Pascal_Triangle(k):
    """
    Calculates the factorial of a non-negative integer k, which corresponds to the (k+1)-th row's first and last element in Pascal's Triangle (if rows start from 0).

    Parameters
    ----------
    k : int
        A non-negative integer.

    Returns
    -------
    int
        The factorial of k (k!).
    """
    result = 1
    for i in range(1, k + 1):
        result *= i
    return result




def Fibonachi_Sequence(N):
    """
    Generates a Fibonacci sequence up to the N-th term.

    Parameters
    ----------
    N : int
        The number of Fibonacci numbers to generate. Must be a positive integer.

    Returns
    -------
    list
        A list containing the first N Fibonacci numbers.
    """
    if not isinstance(N, int) or N <= 0:
        raise ValueError("N must be a positive integer.")
    fibo = [0, 1]
    if N <= 2:
        return fibo[:N]
    first = 0
    second = 1
    for i in range(2, N):
        new = first + second
        fibo.append(new)
        first = second
        second = new
    return fibo




def Factorial(a):
    '''
    The product of all positive integers less than or equal to a given positive integer.

    Parameters
    ----------
    a : int
       

    Returns
    -------
    factorial: int
      the product of all positive integers less than or equal to a given positive integer .

    '''
    if a==0:
        return 1
    else:
        i=1
        factorial=a
        while a!=i:
            factorial=factorial*(a-i)
            i=i+1
        return factorial





def Fabric_GSM(Warp,Weft,Warp_Count_Nm,Weft_Count_Nm,Shrinkage_Percent=5):
   '''
    This function calculates weight fabric in GSM unit.

    Parameters
    ----------
    Warp : int or float
        The number of warps in 1 cm.
    Weft : int or float
        The number of wefts in 1 cm.
    Warp_Count_Nm : int or float
        Warp yarn metric count.
    Weft_Count_Nm : int or float
        Weft yarn metric count.
    Shrinkage_Percent : int or float, optional
        The percentage difference in the length of woven and non-woven yarn. The default is 5.
    Fabric_GSM : int or float
        Result.

    '''
   Fabric_weight= ((Warp*100)/Warp_Count_Nm )+ ((Weft*100)/Weft_Count_Nm )
   Fabric_GSM= Fabric_weight * (1+(Shrinkage_Percent/100))
   return Fabric_GSM




def Fabric_Drape_Coefficient(fabric_weight,fabric_thickness,bending_length):
    '''
    This function estimates the drape coefficient of fabric according to 3 factors:

    Parameters
    ----------
    fabric_weight : int or float
        weight of fabric.  
    fabric_thickness : int or float
        thickness of fabric. 
    bending_length : int or float
        the length difference. 
    Drape_Coefficient : int or float
        Result.

    '''
    Drape_Coefficient = (fabric_weight*bending_length)/(fabric_thickness**2)
    return Drape_Coefficient





def Fabric_Porosity(air_volume,total_volume):
    '''
    

    Parameters
    ----------
    air_volume : int
        enter the volume of pores in fabric in mm^3.
    total_volume : int
        Enter the total volume of fabric in mm^3.
    Returns
    -------
    Fabric_porosity : int
        This function calculates the fabric porosity in mm^3.

    '''
    FP=total_volume-air_volume
    return FP





def Fabric_weight(density,area):
    '''
    

    Parameters
    ----------
    density : int
        enter the density of fabric in g/mm^2.
    area : int
        Enter the area of fabric in mm^2.
    Returns
    -------
    Fabric_weight : int
        This function calculates the fabric weight in g.

    '''
    FW=density*area
    return FW






def Faradays_Law(induced_emf, time, magnetic_flux):
    """
    Calculates a value based on Faraday's Law of induction.
    Note: The provided formula returns the difference, not a direct calculation of a single variable.

    Parameters
    ----------
    induced_emf : float
        The induced electromotive force (in Volts).
    time : float
        The time interval over which the change in magnetic flux occurs (in seconds).
    magnetic_flux : float
        The change in magnetic flux (in Webers).

    Returns
    -------
    float
        The result of the expression: induced_emf - (time * magnetic_flux).
        To solve for a specific variable, rearrange this equation based on Faraday's Law:
        induced_emf = - d(magnetic_flux) / dt (the negative rate of change of magnetic flux).
    """
    return induced_emf - time * magnetic_flux


def Filler_Weight(M, FR1, FR2, FR3):
    """
    Calculates the weight percentages of three fillers in a polymer matrix.

    Parameters
    ----------
    M : float
        The weight of the polymer matrix in grams (gr).
    FR1 : float
        The weight of the first flame retardant in grams (gr).
    FR2 : float
        The weight of the second flame retardant in grams (gr).
    FR3 : float
        The weight of the third flame retardant in grams (gr).

    Returns
    -------
    tuple
        A tuple containing three lists, representing the weight percentages of FR1, FR2, and FR3, respectively.
    """
    total_weight = FR1 + FR2 + FR3 + M
    a = [FR1 / total_weight]  # FR1 weight %
    b = [FR2 / total_weight]  # FR2 weight %
    c = [FR3 / total_weight]  # FR3 weight %
    return a, b, c





def Fick_Sec_Thin(Thickness,Diffusion_coefficient,Time,Thin_layer_Consistency,Position,Thin_Layer_Metal,Second_metal):
    '''
    Fick's second law predicts how diffusion causes the concentration to change with respect to time.
    In the case where a thin film of a different metal is placed between two thick films of another metal,
    and due to heat and a certain time, the amount of penetration of the first metal into the second metal will be investigated.
    Parameters
    ----------
    Thickness : float 
        The thickness of the thin layer metal is used. use cm for input
    Diffusion_coefficient : float
        It shows the diffusion coefficient of the metal placed in the middle compared to the metal on its side. use cm^2/seconds for input
    Time : float
        It shows the duration of the diffusion check. use seconds for input
    Thin_layer_Consistency : float
        It shows the initial concentration of thin metal. use gr/cm^3 for input
    Position :  float
        Indicates the location required to check the concentration. use cm for input
    Thin_Layer_Metal : str
        What is the material of the thin layer used?
    Second_metal : str
        What is the metal material in which the primary metal should penetrate?.

    Returns
    -------
    C_x_t : float
        It shows the concentration of the metal separated from the thin layer and moved in a certain time in the desired location. output will be gr/cm^3
    '''
    pi=3.14
    if Thin_Layer_Metal=='Cu'and Second_metal=='Ni':
        Diffusion_coefficient=0.2698 # @Temprature=1000 K
    if Thin_Layer_Metal=='Cr'and Second_metal=='Ni':
        Diffusion_coefficient=0.0299 # @Temprature=1000 K
    C_x_t=((Thickness*Thin_layer_Consistency)/(2*(pi*Diffusion_coefficient*Time)**(0.5)))*math.exp((-(Position)**2)/(4*Diffusion_coefficient*Time))
    return C_x_t





def Final_Temp_Irreversible_Adiabatic(Initial_temperature,External_pressure,Internal_pressure,C_V,C_P,R,Unit_of_measurement,Number_of_gas_atoms):
    '''
    Parameters
    ----------
  Initial_temperature : float
      Initial temperature of an ideal gas.
  External_pressure : float
      The pressure that enters the system from the environment.
  Internal_pressure : float
      The pressure that enters the system wall from the inside.
  C_V : float
      The ideal gas constant-pressure specific heat.
  C_P : float
      The ideal gas constant-pressure specific heat..
  R : float
      The molar gas constant or ideal gas constant.
  Unit_of_measurement : str
      DESCRIPTION.
  Number_of_gas_atoms : str
      DESCRIPTION.

  Returns
  -------
  Final_Temp : float
      Outputs the final temperature if the system operates adiabatically irreversible.
    '''
    if Unit_of_measurement=='Jouls':
        R=8.314
        if Number_of_gas_atoms=='one':
            C_V=1.5*R
            C_P=2.5*R
        if Number_of_gas_atoms=='two':
            C_V=2.5*R
            C_P=3.5*R
        if Number_of_gas_atoms=='multi':
            C_V=3.5*R
            C_P=4.5*R
    elif Unit_of_measurement=='Calories':
        R=1.98
        if Number_of_gas_atoms=='one':
            C_V=1.5*R
            C_P=2.5*R
        if Number_of_gas_atoms=='two':
            C_V=2.5*R
            C_P=3.5*R
        if Number_of_gas_atoms=='multi':
            C_V=3.5*R
            C_P=4.5*R   
    Final_Temp=Initial_temperature*((C_V+(External_pressure/Internal_pressure)*R)/C_P)
    return Final_Temp





def Fracture_Toughness(s, c, location):
    
    '''
    this function calculates fracture toughness 
    based on applied stress, crack length, and location
    
     fracture toghness formula:      
         K1C =  a*s* (math.sqrt(3.14* c))
         
    where:

        K1C is the fracture toughness,
        a is a geometric factor,
        s is the applied stress,
        c is the crack length.

         
    Parameters
    ----------- 
    1. s: int ---> (MPa)
       applied stress 
       
    2. c: float ---> (m) 
       crack length
       
    3. location: str
       represents the location of crack

    Returns --> K1C (fracture toughness)
    
    '''
    
    if location == 'surface' or 'side':
        a = 1.12
        K1C =  a*s* (math.sqrt(3.14* c))
        
    elif location == 'centeral':
        a = 1
        c = c/2
        K1C =  a*s* (math.sqrt(3.14* c))
        
        
    return K1C




def Faraday_Corrosion(current_density, time, atomic_weight, density, valence):
    """
     calculate penetration depth from corrosion
    current_density: A/m²
    time:hour
    atomic_weight: g/mol
    density: g/cm³
    valence
    """
    K = 3.27e-4  #μm/(A/m²·h)
    faraday=(K * current_density * time * atomic_weight / (density * valence))
    return faraday
	




def Friction_Law(mass,angle,/,MOTCS,moving):
    '''
    This function calculates the friction force on the object by taking the mass of the desired object, the material of the two contact surfaces, the angle of the contact surface with the horizon and the movement state of the object.
    
    Parameters
    ----------
    mass : int
        The mass of the desired object (KG).
    angle : int
        The angle of the contact surface with respect to the horizon (RAD).
    MOTCS : str
        Material of two contact surfaces.
        The contact surfaces considered :
        STEEL ON STEEL
        STEEL ON ALUMINUM
        STEEL ON COPPER
        COPPER ON CAST IRON
        COPPER ON GLASS
        GLASS ON GLASS
        RUBBER ON DRY CONCRETE
        RUBBER ON WET CONCRETE
        TEFLON ON TEFLON
    moving : str
        Is the desired object moving? (YES OR NO).

    Returns
    -------
    F : float
        Frictional force applied to the target object (N).

    '''
    m=moving.upper()
    M=MOTCS.upper()
    if m=='YES':     
        if M=='STEEL ON STEEL':
            F=mass*9.81*math.cos(angle)*0.57
        if M=='STEEL ON ALUMINUM':
            F=mass*9.81*math.cos(angle)*0.47
        if M=='STEEL ON COPPER': 
            F=mass*9.81*math.cos(angle)*0.36
        if M=='COPPER ON CAST IRON':
            F=mass*9.81*math.cos(angle)*0.29
        if M=='COPPER ON GLASS':
            F=mass*9.81*math.cos(angle)*0.53
        if M=='GLASS ON GLASS':
            F=mass*9.81*math.cos(angle)*0.40
        if M=='RUBBER ON DRY CONCRETE':  
            F=mass*9.81*math.cos(angle)*0.8
        if M=='RUBBER ON WET CONCRETE':   
            F=mass*9.81*math.cos(angle)*0.25
        if M=='TEFLON ON TEFLON':   
            F=mass*9.81*math.cos(angle)*0.04
        return F
    if m=='NO':
        if M=='STEEL ON STEEL':
            F=mass*9.81*math.cos(angle)*0.74
        if M=='STEEL ON ALUMINUM':
            F=mass*9.81*math.cos(angle)*0.61
        if M=='STEEL ON COPPER': 
            F=mass*9.81*math.cos(angle)*0.53
        if M=='COPPER ON CAST IRON':
            F=mass*9.81*math.cos(angle)*1.05
        if M=='COPPER ON GLASS':
           F=mass*9.81*math.cos(angle)*0.68
        if M=='GLASS ON GLASS':
           F=mass*9.81*math.cos(angle)*0.94
        if M=='RUBBER ON DRY CONCRETE':  
           F=mass*9.81*math.cos(angle)*1
        if M=='RUBBER ON WET CONCRETE':   
           F=mass*9.81*math.cos(angle)*0.3
        if M=='TEFLON ON TEFLON':   
           F=mass*9.81*math.cos(angle)*0.04
        return F







def Geometric_Sequence(first_variable,second_variable):
    '''
    This function obtains the result of a geometric progression

    Parameters
    ----------
    first_variable : int
        The value of the first variable.
    second_variable : int
       The value of the second variable.

    Returns
    -------
    int
        gives the result of the geometric exponential function.

    '''
    if second_variable>1:
       m=(first_variable*(Geometric_Sequence(first_variable,second_variable-1)))/2 
       
    else:
        
        return 1
    return m 




def Gauss_l=Law(electric_field, surface_area, electric_flux):
    """
    Calculates a value related to Gauss's Law for electricity.
    Note: The provided formula returns the difference, not a direct calculation of a single variable.

    Parameters
    ----------
    electric_field : float
        The magnitude of the electric field (e.g., in N/C).
    surface_area : float
        The area of the closed surface through which the electric field passes (e.g., in m^2).
    electric_flux : float
        The electric flux through the closed surface (e.g., in N·m^2/C).

    Returns
    -------
    float
        The result of the expression: (electric_field * surface_area) - electric_flux.
        According to Gauss's Law, the electric flux through a closed surface is proportional to the enclosed electric charge:
        electric_flux = enclosed_charge / permittivity_of_free_space.
        For a uniform electric field perpendicular to a surface, electric_flux = electric_field * surface_area.
        To solve for a specific variable, rearrange the appropriate form of Gauss's Law.
    """
    return electric_field * surface_area - electric_flux




def Gibs_Free_Energy(H0,T,S0):
    '''
    Parameters
    ----------
    H0 : float
        Enthalpy of material in the pressure of 1atm in pure state. The number should be in terms of joul or kilojoul. It must have the same unit as entropy.
    T : float
        Temperature of material. The temperature should be in terms of Kelvin.
    S0 : float
        Entropy of material. The number should be in terms of joul or kilojoul. It must have the same unit as enthalpy.

    Returns
    -------
    G : float
        This function give us the amount of Gibs free energy of the material at the pressure of 1atm. The terms of this function is joul or kilojoul.

    '''
    G0=H0-T*S0
    return G0





def Gravitational_Force(G,FT):
    '''
    Parameters
    ----------
    G : float
        The gravitational force is a force that attracts any two objects with mass.
    FT : float
        The force of gravity varies with latitude and increases from about 9.780 m/s2 at the Equator to about 9.832 m/s2 at the poles.

    Returns
    -------
    F : float
        The force of gravity is also called as Newton's law of gravitation. Mathematically, F = GMmr2.
        where F = force of gravity, G = gravitational constant, M = mass of one object, m = mass of other object, r = distance between two objects.

    '''
    if FT=='Force of gravity total':
        F=G*((5.972*(10**24)*1.989*(10**30))/((1.496*(10**11))**2))
        return F
    



def Gravitational_Force_Formula(g,m_mars,m_sun,r_mars_sun):
    '''
    

    Parameters
    ----------
    g : float
        The gravitational force is a force that attracts any two objects with mass.
    m_mars : float
        Mars' mass is 6.42 x 1023 kilograms, about 10 times less than Earth.
        This affects the force of gravity. Gravity on Mars is 38 percent of Earth's gravity,
        so a 100-pound person on Earth would weigh 38 pounds on Mars
    m_sun : float
        The sun has a mass of 1.9891x1030 kg = 4.384x1030 lb = 2.192x1027 tons, or a mass 333,000 times that of the Earth.
        The radius of the Sun is 696,265,000 meters = 696,265 km = 432,639 mi or a radius 109 times that of the Earth.
    r_mars_sun : float
        Mars is about 128 million miles (206 million km) from the sun,
        and at its farthest distance (aphelion) Mars is about 154 million miles (249 million km) from the sun.

    Returns
    -------
    F2 : float
        The force of gravity is also called as Newton's law of gravitation.
        Mathematically, F = GMmr2.
        where F = force of gravity, G = gravitational constant, M = mass of one object, m = mass of other object, r = distance between two objects.

    '''
    if g=='gravity':
       F2=g*((m_mars*m_sun)/r_mars_sun**2)
       return F2






def Heat_Transfer_Rate (Thermal_conductivity,area, tempreture_difference):
    '''
    This function is used to calculate heat transfer rate by using thermal conductivity, area of transformation, and tempreture of to sides of transformation.
    In this formula, heat transfer rate is in Btu/(hr*square ft*F), area is in square ft, and tempreture difference is in F.

'''
    Heat_Transfer_Rate=Thermal_conductivity*area*tempreture_difference
    return Heat_Transfer_Rate




  
def Half_Inhibitory_Concentration(A1,A2,A3):
    '''
This function determines the drug’s efficacy in biological process inhibition     

    Parameters
    ----------
    A1 : int
        absorbance of the experimental wells 
    A2 : int
        absorbance of the control wells
    A3 : int
        absorbance of the blank wells

    Returns
     float
        Half _Inhibitory_Concentration 

    '''
    return 1-(A1-A3/A2-A3)*100





def Hall_Petch(d_grain, sigma0, k):
    """
    calculate yield strengh with grain size in Hall Petch
    k(float) = MPa·√m Hall Petch constant
    d_grain  = size of grain according to meter
    """
    hall=(sigma0 + k / (d_grain**0.5))
    return hall






def Hall_Petch_Relationship(grain_size, yield_strength_boundary, k_hp):
    """
    Calculates the yield strength of a polycrystalline material based on its
    grain size using the Hall-Petch relationship. This fundamental concept
    in materials science explains how reducing grain size generally increases
    the strength of a material by increasing the number of grain boundaries
    that impede dislocation motion.

    Parameters
    ----------
    grain_size : float
        The average grain size of the polycrystalline material (typically in micrometers or millimeters).
    yield_strength_boundary : float
        The yield strength of a single crystal of the material (or a material with infinitely large grains), representing the intrinsic strength (in MPa or equivalent units).
    k_hp : float
        The Hall-Petch coefficient, a material-specific constant that reflects the strength of grain boundaries in impeding dislocation motion (in MPa * sqrt(length unit)).

    Returns
    -------
    float
        The yield strength of the polycrystalline material (in the same units as yield_strength_boundary).
    """
    return yield_strength_boundary + k_hp / math.sqrt(grain_size)





def Hooke(strain, young_modulus):
    """
    Calculates stress using Hooke's Law for elastic materials under uniaxial loading.

    Parameters
    ----------
    strain : float
        The dimensionless strain (change in length divided by original length).
    young_modulus : float
        The Young's modulus (elastic modulus) of the material (in Pascals or equivalent units).

    Returns
    -------
    float
        The stress experienced by the material (in Pascals or equivalent units).
    """
    stress = young_modulus * strain
    return stress


def Heat_Transfer(thermal_conductivity, area, temperature_difference, thickness):
    """
    Calculates the rate of heat transfer through a material by conduction using Fourier's Law.

    Parameters
    ----------
    thermal_conductivity : float
        The thermal conductivity of the material (e.g., in W/(m·K)).
    area : float
        The cross-sectional area through which heat is transferred (e.g., in m^2).
    temperature_difference : float
        The temperature difference across the thickness of the material (e.g., in Kelvin).
    thickness : float
        The thickness of the material through which heat is transferred (e.g., in meters).

    Returns
    -------
    float
        The rate of heat transfer (in Watts).
    """
    return thermal_conductivity * area * temperature_difference / thickness


def Hookes_Law(spring_constant, displacement):
    """
    Calculates the force exerted by a spring according to Hooke's Law.

    Parameters
    ----------
    spring_constant : float
        The spring constant (in Newtons per meter).
    displacement : float
        The displacement of the spring from its equilibrium position (in meters).

    Returns
    -------
    float
        The force exerted by the spring (in Newtons).
    """
    return spring_constant * displacement


def Hadamard_Product(matrix1, matrix2):
    """
    Calculates the Hadamard product (element-wise product) of two matrices.

    Parameters
    ----------
    matrix1 : numpy.ndarray
        The first matrix.
    matrix2 : numpy.ndarray
        The second matrix.
        Note: The dimensions of matrix1 and matrix2 must be the same for element-wise multiplication.

    Returns
    -------
    numpy.ndarray
        The Hadamard product of the two matrices.
    """
    return np.multiply(matrix1, matrix2)




def Heat_Capacity (m,c,T1,T2):
    '''
    This function caclulate the amount of heat capacity of a mass
    Parameters
    ----------
    m : Float
        mass.
    c : float
        specific heat coefficient.
    T1 : float
        primary temperature.
    T2 : float
        secondary temperature.

    '''
    Q=m*c*(T2-T1)
    if Q<0:
        str='The mentioned material has lost heat'
    if Q==0:
        str='The mentioned material,s heat has not changed'
    if Q>0:
        str='The mentioned material has gained heat'
    return Q,str





def HeatـTransferـCoefficient(k,A,t1,t2,d):
    '''
    

    Parameters
    ----------
    This function receives the variables k, A, t1,t2,d and returns the variable Q
    Q : int
        It indicates the rate of heat transfer.
    k : int
        Heat transfer coefficient
    A : int
        is the heat transfer coefficient.
    t1 : int
        The area of ​​the surface from which heat is transferred.
    t2 : int
        Initial temperature
    d : int
        Secondary temperature

    '''
    Q=k*A*(t2-t1/d)
    return Q




def Hardness_vickers(F,d):
    '''
    Parameters
    ----------
    F : float
        Applied force in terms of kilogram.
    d : float
        Medium diameter of indentor effect in terms of milimeter.

    Returns
    -------
    HV : Vickers hardness
        This function give us the amount of hardness of material that evaluated by vickers hardness tester. The terms of this is Kg/mm2.

    '''
    HV=1.854*F/(d**2)
    return HV





def Heat_Exchanger_Transfer(U,Th1,Th2,Tc1,Tc2,C,dot_m):
    '''
    

    Parameters
    ----------
    U : float
        Overall heat transfer coefficient.
    Th1 : float
        Hot fluid inlet temperature.
    Th2 : float
        Hot fluid outlet temperature.
    Tc1 : float
        Cold fluid inlet temperature.
    Tc2 : float
        Cold fluid outlet temperature.
    C : float
        Special heat.
    dot_m : float
        Debbie Jeremy.
        

    Returns(delta_T_LMTD,Q,A)
    -------
    None.
    

    '''
    
    delta_T_LMTD=((Th1-Tc2)-(Th2-Tc1))/math.log((Th1-Tc2)/(Th2-Tc1))##Logarithmic mean temperature

    Q=dot_m*C*(Tc2-Tc1)

    A=Q/(U*delta_T_LMTD)###The heat exchange surface used
    return delta_T_LMTD,A,Q




def Ideal_Gas_low_with_unit(R = "(L.atm) / (K.mol)", V = 1, n = 1, T = 0):
    
    '''
    It calculate the Pressure of ideal gas.
    
    Parameters:
    ----------
    P : float
        Pressure
        
    V : float
        The amount of Volume 
        
    n : float 
    
    The amount of substance
    
    T : float
        Temperature
    
    R : float
        ideal gas constant
        
    '''
    # V in Litr, Pressure in atm, n in mol.
    if R == "(L * atm) / (K * mol)":
        P = (n * T * 0.082057) / V
        return P
    
    if R == " J / (K.mol)":
        P = (n * T * 8.314472) / V
        return P
    
    if R == "((m**3).atm) / (K.mol)":
        P = (n * T * 8.205745 * (10 **(-5))) / V
        return P
    
    if R == "(L.kPa) / (K.mol)":
        P = (n * T * 8.314472) / V
        return P
    
    if R == "(((m**3).Pa) / (K.mol))":
        P = (n * T * 8.314472) / V
        return P
    
    if R == "((cm ** 3).atm) / (K.mol)":
        P = (n * T * 82.05745) / V
        return P
    
    if R == "(L.mbar) / (K.mol)":
        P = (n * T * 83.14472) / V
        return P
    
    if R == "((m**3).bar) / (K.mol)":
        P = (n * T * (8.314472 * (10**(-5)))) / V
        return P





def Ideal_Gas_Law(pressure, volume, temperature):
    """
    Calculates a value based on the Ideal Gas Law.
    Note: The provided formula returns the difference, not a direct calculation of the number of moles.

    Parameters
    ----------
    pressure : float
        The pressure of the gas (in Pascals).
    volume : float
        The volume of the gas (in cubic meters).
    temperature : float
        The temperature of the gas (in Kelvin).

    Returns
    -------
    float
        The result of the expression: (pressure * volume) - (gas_constant * temperature).
        According to the Ideal Gas Law: pressure * volume = number_of_moles * gas_constant * temperature.
        To solve for a specific variable (like the number of moles), rearrange this equation.
    """
    gas_constant = 8.314  # Ideal gas constant (J/(mol·K))
    return pressure * volume - gas_constant * temperature


def Ideal_Diode_Equation(current, saturation_current, thermal_voltage):
    """
    Calculates a value based on the Ideal Diode Equation (Shockley diode equation).
    Note: The provided formula returns the difference, not a direct calculation of the voltage across the diode.

    Parameters
    ----------
    current : float
        The current flowing through the diode (in Amperes).
    saturation_current : float
        The reverse saturation current of the diode (in Amperes).
    thermal_voltage : float
        The thermal voltage (Vt = kT/q), typically around 26 mV at room temperature (in Volts).

    Returns
    -------
    float
        The result of the expression: current - (saturation_current * (math.exp(current / thermal_voltage) - 1)).
        The standard form of the Ideal Diode Equation is:
        current = saturation_current * (exp(voltage / thermal_voltage) - 1).
        To solve for the voltage across the diode, rearrange this standard equation.
    """
    return current - saturation_current * (math.exp(current / thermal_voltage) - 1)


'''
def Income_Tax(a):
    """
    

    Parameters
    ----------
    a : float
         daramad fard dar yek mah

    Returns maliyat bar daramad fard dar yek mah dar iran
    -------


    """
    return (a-10000000)*0.09

'''

def Incompressible_Fluids_Pressure(d, h):
    """
    Calculates the pressure at a certain depth in an incompressible fluid.

    Parameters
    ----------
    d : float
        The density of the incompressible fluid (in kg/m^3).
    h : float
        The depth below the surface of the fluid (in meters).

    Returns
    -------
    float
        The absolute pressure (P) at the specified depth in Pascals (Pa).
    """
    P_0 = 101325  # Atmospheric pressure at sea level (Pa)
    g = 9.81  # Acceleration due to gravity (m/s^2)
    P = d * g * h + P_0
    return P


def Insertion_Sort(non_sorted_list):
    """
    Sorts a list of elements in-place using the Insertion Sort algorithm.

    Parameters
    ----------
    non_sorted_list : list
        The list of elements to be sorted.

    Returns
    -------
    list
        The sorted list (the original list is modified in-place).
    """
    for i in range(1, len(non_sorted_list)):
        key = non_sorted_list[i]
        j = i - 1
        while j >= 0 and key < non_sorted_list[j]:
            non_sorted_list[j + 1] = non_sorted_list[j]
            j -= 1
        non_sorted_list[j + 1] = key
    print(non_sorted_list)
    return non_sorted_list






def Indeterminate_degree_of_truss(m,j):
    ''' 
    This function calculates the degree of indeterminacy of the truss by taking 'm' number of truss members and 'j' number of nodes.
    
    Parameters
    ----------
    m : int
        Number of members truss.
    j : int
        Number truss node members.

    Returns
    -------
    n : float
        The indeterminate degree of truss.
        
        if n=0 : The truss is determinate.
        if n>0 : The truss is statically unstable.
        if n<0 : The truss is indeterminate.
        
    '''
    Equations=2*j
    Unknowns=3+m
    if (Equations==Unknowns):
        n=0
    if Equations>Unknowns:
        n=Equations-Unknowns
    if Equations<Unknowns:
        n=Equations-Unknowns
    return n





def Kinetic_Energy(mass, velocity):
    """
    Calculates the kinetic energy of an object.

    Parameters
    ----------
    mass : float
        The mass of the object (in kilograms).
    velocity : float
        The velocity of the object (in meters per second).

    Returns
    -------
    float
        The kinetic energy of the object (in Joules).
    """
    return 0.5 * mass * velocity**2


def Lorentz_Force(charge, velocity, magnetic_field):
    """
    Calculates the magnetic force component of the Lorentz force acting on a moving charged particle.

    Parameters
    ----------
    charge : float
        The electric charge of the particle (in Coulombs).
    velocity : numpy.ndarray
        A 3D vector representing the velocity of the particle (in meters per second).
    magnetic_field : numpy.ndarray
        A 3D vector representing the magnetic field (in Teslas).

    Returns
    -------
    numpy.ndarray
        A 3D vector representing the magnetic force acting on the particle (in Newtons).
    """
    return charge * np.cross(velocity, magnetic_field)



def Lorentz_Lorenz_Constant(n,ro):
    
    ''' n(float)=  refrective index
    ro(float)=density g/cm3 or kg/m3
    
    
    Retuen:
        
        R=(float)
        constant related to light properties of materials(polymers, plstics,...)
    
    '''
    R=float((n**2-1)/(n**2+2)/ro)
    return R





def Latice_Parameter(structure, r):
    
    '''
    this function calculates Latice parameter based on crystal structure.
    
    Parametrs
    ----------
    1. structure : str
    structure includes crystal structures such as FCC, BCC, SC, HCP, and DC.
    
    FCC: face centered cubic
    BCC: body centered cubic
    SC:  simple cubic
    HCP: hexagonal close pack
    DC:  diamond cubic
    
    2. r: float ---> (nm)
    r represents atomic radius.

    Returns --> latice parameter (a)
        
    '''
    
    
    
    if structure == 'FCC' or  'face centered cubic':
        a = (4*r)/math.sqrt(2)
        
    elif structure == 'BCC' or  'body centered cubic':
        a = (4*r)/math.sqrt(3)
     
    elif structure == 'SC' or  'simple cubic':
        a = 2*r  
     
    elif structure == 'HCP' or  'hexagonal close pack':
        a = 2*r  
                            
    elif structure == 'DC 'or  'diamond cubic':
        a = (8*r)/math.sqrt(3)                        
    
    return a  





def Lattice_Parameter(r,structure):
    '''
    Parameters
    ----------
    r : float
        r is atomic radius of material. It is in terms of angestrom.
    structure : str
        Structure of material is face center cubic or body center cubic.

    Returns
    -------
    a : float
        a is lattice parameter of material in unit cell. It is in terms of angestrom.

    '''
    if structure=='fcc':
        a=4*r/(2**0.5)
    if structure=='bcc':
        a=4*r/(3**0.5)
    return a
	





def Lennard_Jones_Potential(r, sigma, epsilon):
    """
    Calculates the Lennard-Jones potential energy between two non-bonding atoms
    or molecules as a function of the distance 'r' between them. This potential
    models the balance between short-range repulsive forces (Pauli repulsion)
    and long-range attractive forces (van der Waals forces).

    Parameters
    ----------
    r : float
        The distance between the two atoms or molecules (in Angstroms or other length units).
    sigma : float
        The distance at which the potential energy is zero (related to the size of the particles).
    epsilon : float
        The depth of the potential well, representing the strength of the attraction.

    Returns
    -------
    float
        The Lennard-Jones potential energy (in energy units like Joules or electronvolts, depending on the units of epsilon).
    """
    term1 = (sigma / r)**12
    term2 = (sigma / r)**6
    return 4 * epsilon * (term1 - term2)





def Mandaliof_Properties(E):
    '''
    

    Parameters
    ----------
    E : string
        The chemical symbol of the Element

    Returns
    -------
    Nothing

    '''
    PT=['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn',
        'Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Xe','Cs','Ba','La','Ce','Pr',
        'Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn','Fr','Ra',
        'Ac','Th','Pa','U','Np','Pu','Am','Cm','Bk','Cf','Es','Fm','Md','No','Lr','Rf','Db','Sg','Bh','Hs','Mt','Ds','Rg','Cn','Nh','Fl','Mc','Lv','Ts','Og']
    loc=PT.index(E)
    Column=[1,18,1,2,13,14,15,16,17,18,1,2,13,14,15,16,17,18,1,2,3,4,5,6,7,8,9,10,11,12,13,14,
        15,16,17,18,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,1,2,3,3,3,3,3,3,3,3,
        3,3,3,3,3,3,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,1,2,3,3,3,3,3,3,3,3,
        3,3,3,3,3,3,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
    Row=[1,1,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,5,5,5,5,5,5,5,5,5,5,5,5,
         5,5,5,5,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,7,7,7,7,7,7,7,7,7,7,
         7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7]
    R=[31,28,128,112,84,76,71,66,57,58,166,141,121,111,107,105,102,106,203,176,170,160,153,139,139,132,152,124,132,122,122,120,
        119,120,120,116,220,195,190,175,164,154,147,146,142,139,145,144,142,139,139,138,139,140,244,215,207,204,203,201,199,198,198,196,
        194,192,192,189,190,187,187,175,170,162,151,144,141,136,136,132,145,146,148,140,150,150,260,221,215,206,200,186,190,187,180,169,
        168,'N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A']
    A_W=[1.008,4.003,6.94,9.012,10.81,12.01,14.007,15.999,18.998,20.180,22.990,24.305,26.981,28.085,30.974,32.06,35.45,39.948,39.098,40.078,44.956,47.867,50.941,51.996,54.938,55.845,58.933,58.693,63.546,65.38,69.723,72.63,
        74.922,78.971,79.904,83.798,85.468,87.62,88.906,91.224,92.906,95.95,98,101.07,102.906,106.42,107.868,112.414,114.818,118.71,121.76,127.6,126.904,131.293,132.905,137.327,138.905,140.116,140.908,144.242,145,150.36,151.964,157.25,
        158.925,162.5,164.930,167.259,168.934,173.045,174.967,178.49,180.948,183.84,186.207,190.23,192.217,195.084,196.967,200.592,204.38,207.2,208.980,209,210,222,223,226,227,232.038,231.036,238.029,237,244,243,247,
        247,251,252,257,258,259,262,267,270,269,270,270,278,281,281,285,286,289,289,293,293,294]
    T_m=[-259.14,'N/A',180.54,1287,2075,3550,-210.1,-218.3,-219.6,-248.59,97.72,650,660.32,1414,44.2,115.21,-101.5,-189.3,63.38,842,1541,1668,1910,1907,1246,1538,1495,1455,1084.62,419.53,29.76,938.3,
        817,221,-7.3,-157.36,39.31,777,1526,1855,2477,2623,2157,2334,1961,1554.9,961.78,321.07,156.6,231.93,630.63,449.51,113.7,-111.8,28.44,727,920,798,931,1021,1100,1072,822,1313,
        1356,1412,1474,1497,1545,819,1663,2233,3017,3422,3186,3033,2466,1768.3,1064.18,-38.83,304,327.46,271.3,254,302,-71,20.9,700,1050,1750,1572,1135,644,640,1176,1345,
        1050,900,860,1500,830,830,1600,'N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A']
    T_b=[-252.87,-268.93,1342,2470,4000,4027,-195.79,-182.9,-188.12,-246.08,883,1090,2519,2900,280.5,444.72,-34.04,-185.8,759,1484,2830,3287,3407,2671,2061,2861,2927,2913,2562,907,2204,2820,
        614,685,59,-153.22,688,1382,3345,4409,4744,4639,4265,4150,3695,2963,2162,767,2072,2602,1587,988,184.3,-108,671,1870,3464,3360,3290,3100,3000,1803,1527,3250,
        3230,2567,2700,2868,1950,1196,3402,4603,5458,5555,5596,5012,4428,3825,2856,356.73,1473,1749,1564,962,350,-61.7,650,1737,3200,4820,4000,3900,4000,3230,2011,3110,
        'N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A']
    Name=['Hydrogen','Helium','Lithium','Beryllium','Boron','Carbon','Nitrogen','Oxygen','Fluorine','Neon','Sodium','Magnesium','Aluminum','Silicon','Phosphorus','Sulfur','Chlorine','Argon','Potassium','Calcium','Scandium','Titanium','Vanadium','Chromium','Manganese','Iron','Cobalt','Nickel','Copper','Zinc','Gallium','Germanium',
        'Arsenic','Selenium','Bromine','Krypton','Rubidium','Strontium','Yttrium','Zirconium','Niobium','Molybdenum','Technetium','Ruthenium','Rhodium','Palladium','Silver','Cadmium','Indium','Tin','Antimony','Tellurium','Iodine','Xenon','Caesium','Barium','Lanthanum','Cerium','Praseodymium','Neodymium','Promethium','Samarium','Europium','Gadolinium',
        'Terbium','Dysprosium','Holmium','Erbium','Thulium','Ytterbium','Lutetium','Hafnium','Tantalum','Tungsten','Rhenium','Osmium','Iridium','Platinum','Gold','Mercury','Thallium','Lead','Bismuth','Polonium','Astatine','Radon','Francium','Radium','Actinium','Thorium','Protactinium','Uranium','Neptunium','Plutonium','Americium','Curium',
        'Berkelium','Californium','Einsteinium','Fermium','Mendelevium','Nobelium','Lawrencium','Rutherfordium','Dubnium','Seaborgium','Bohrium','Hassium','Meitnerium','Darmstadtium','Roentgenium','Copernicium','Nihonium','Flerovium','Moscovium','Livermorium','Tennessine','Oganesson']
    
    if loc>95:
        P='Solid'
    elif loc==1:
        P='Gas'
    else:
        if 25<T_m[loc]:
            P='Solid'
        elif T_m[loc]<25<T_b[loc]:
            P='Liquid'
        else:
            P='Gas' 
    print('The properties of the element you are looking for are:\n\n\nFull name:                  ',Name[loc],'\nLocation in Periodic Table:  Row=',Row[loc],'  Column=',Column[loc],
          '\nAtomic number:              ',loc+1,'\nAtomic weight:              ',A_W[loc],' g/mol\nAtomic radius:              ',R[loc],' pm\nMelting temperature:        ',T_m[loc],end='')
    if loc==32:
        print(' (Above 28 atm)',end='')
    print('\nBoiling temperature:        ',T_b[loc],' \nStandard phase:             ',P)





def Mtt_Test(C1,C2):
    '''
 This function measures the metabolic activity of the cell
    
    Parameters
    ----------
    C1 : int
        viable cells 
    C2 : int
        total cells

    Returns
    float
        Mtt_Test

    '''
        
    
    return (C1/C2)*100
    


def Mass_Energy_Equivalence(mass):
    """
    Calculates the energy equivalent of a given mass using Einstein's mass-energy equivalence principle (E=mc^2).

    Parameters
    ----------
    mass : float
        The mass (in kilograms).

    Returns
    -------
    float
        The equivalent energy (in Joules).
    """
    speed_of_light = 3e8  # Speed of light in m/s
    return mass * speed_of_light**2


def Maxwells_Equations(electric_field, magnetic_field, charge_density, current_density):
    """
    Represents a simplified form of two of Maxwell's equations: Gauss's law for electricity and Ampère-Maxwell's law.
    Note: This function assumes that the `div()` and `curl()` methods are defined for the input field objects and returns a tuple representing the differences from zero as stated by the laws in a vacuum (no free charges or currents). For the full equations in media, permittivity and permeability would need to be considered.

    Parameters
    ----------
    electric_field : object
        An object representing the electric field, assumed to have a `div()` method.
    magnetic_field : object
        An object representing the magnetic field, assumed to have a `curl()` method.
    charge_density : float
        The electric charge density (in Coulombs per cubic meter).
    current_density : object
        An object representing the current density, assumed to be involved in Ampère-Maxwell's law.

    Returns
    -------
    tuple
        A tuple containing two values:
        - The result of the divergence of the electric field minus the charge density (related to Gauss's law).
        - The result of the curl of the magnetic field minus the current density (related to Ampère-Maxwell's law, neglecting the displacement current term for simplicity as per the input).
    """
    # This is a symbolic representation. Actual implementation would depend on how electric and magnetic fields are represented.
    return electric_field.div() - charge_density, magnetic_field.curl() - current_density


     
def Mc_Cabe(F,Zf,Xd,Xw,R,alpha,q):
    '''This function is used for Mc-Cabe calculation in Distillation Towers
    F : Feed Rate
    Zf : volatile composition in Feed
    Xd : volatile composition in Distillate
    Xw : volatile composition in Waste
    R : Reflux
    alpha : Volatility coefficient
    q : the quantity of liquid in feed
    Returns the number of tray'''
    W=F*(Xd-Zf)/(Xd-Xw)
    D=F-W
    L_first=R*D
    G_first=(R+1)*D
    L_second=L_first+q*F
    G_second=G_first-(1-q)*F  
    # Rmin Calculation
    guess=0
    n=0
    while n<10000:
        if q==0:
            Left=np.array([Zf/(1-Zf)])
            Right=np.array([alpha*((Xd*(q-1)+Zf*(guess+1))/(((1-Xd)*(q-1))+(1-Zf)*(guess+1)))])
        else:
            Left=np.array([((Xd*q+Zf*guess)/((1-Xd)*q+(1-Zf)*guess))])
            Right=np.array([alpha*((Xd*(q-1)+Zf*(guess+1))/(((1-Xd)*(q-1))+(1-Zf)*(guess+1)))])
        if Left-Right<0:
            Rmin=guess
        else:
            guess=guess+0.001            
        n=n+1
        
    # Nmin Calculation
    Nmin=np.ceil(math.log((Xd*(1-Xw))/(Xw*(1-Xd)),10)/(math.log(alpha,10))-1)
    
    # N Calculation
    # 1st Operating Line
    x=np.array([])
    for i in range(0,101,1):
        a=np.array([i/100])
        x=np.concatenate((x,a))
        
    yeq=np.array([])
    for i in range(0,101,1):
        b=np.array([(alpha*(i/100))/((alpha-1)*(i/100)+1)])
        yeq=np.concatenate((yeq,b))
        
    y_first=np.array([])
    for i in range(0,101,1):
        c=np.array([(((R*(i/100))/(R+1))+((Xd)/(R+1)))])
        y_first=np.concatenate((y_first,c))
        
    y_second=np.array([])
    for i in range(0,101,1):
        d=np.array([L_second*(i/100)/G_second-W*Xw/G_second])
        y_second=np.concatenate((y_second,d))
        
    xfeed=np.array([])
    for i in range(0,101,1):
        if q==1:
            e=np.array([Zf])
            xfeed=np.concatenate((xfeed,e))
        else:
            e=np.array([i/100])
            xfeed=np.concatenate((xfeed,e))
    
    yfeed=np.array([])
    for i in range(0,101,1):
        if q==1:
            m=np.array([i/100])
            yfeed=np.concatenate((yfeed,m))
        else:
            f=np.array([((q*(i/100))/(q-1))-(Zf/(q-1))])
            yfeed=np.concatenate((yfeed,f))
            
        if q==1:
         xcrosspoint=Zf
         ycrosspoint=(L_first*xcrosspoint)/(G_first)+Xd/(R+1)
        else:       
         xcrosspoint=((Zf/(q-1))+(Xd/(R+1)))/((q/(q-1))-(L_first/G_first))
         ycrosspoint=(q*xcrosspoint)/(q-1)-(Zf/(q-1))
    
    Xopt=[]
    x=Xd
    for i in range(0,100):
        if ycrosspoint<x:
            xopt=x/(alpha+x-alpha*x)
            x=(L_first*xopt/G_first)+(Xd/(R+1))
            Xopt=Xopt+[xopt]
            Nfeed=len(Xopt)
        elif x>Xw:
            xopt=x/(alpha+x-alpha*x)
            x=(L_second*xopt/G_second)-W*Xw/G_second
            Xopt=Xopt+[xopt]
        else:
            N=len(Xopt)-1
    return print('Nmin=',Nmin,'     Rmin=',Rmin,'     N=',N,'     NFeed=',Nfeed,'     W=',W,'     D=',D)





def Mass_Transfer_Intensity(result_1, size_of_the_surface):
    """
    Calculates the Mass Transfer Intensity (MTI).

    Parameters
    ----------
    result_1 : float
        A mass transfer related result (the units of this parameter will determine the units of MTI).
    size_of_the_surface : float
        The size (area) of the surface where mass transfer occurs (in square meters, m^2).

    Returns
    -------
    float
        The Mass Transfer Intensity (MTI_ἠ). The units will be the units of result_1 multiplied by square meters.
    """
    MTI_ἠ = float(result_1 * size_of_the_surface)
    return MTI_ἠ




def Mass_Of_Rubber_In_Internal_Mixer(filler_percentage, type_of_rotors, V):
    """
    Estimates the mass of rubber in an internal mixer based on filler percentage, rotor type, and mixer volume.

    Parameters
    ----------
    filler_percentage : float
        The percentage of filler in the rubber compound.
    type_of_rotors : str
        The type of rotors in the internal mixer ('tangential' or 'intermix'). Case-sensitive.
    V : float
        The volume of the internal mixer. The unit of volume will determine the unit of the returned mass (assuming a consistent density factor).

    Returns
    -------
    float
        The estimated mass of rubber in the internal mixer. The unit will depend on the unit of V.
    """
    if filler_percentage > 65:
        if type_of_rotors == 'tangential':
            M = 1.3 * 0.8 * V
            return M
        elif type_of_rotors == 'intermix':
            M = 1.3 * 0.6 * V
            return M
    elif filler_percentage <= 65:
        if type_of_rotors == 'tangential':
            M = 1 * 0.8 * V
            return M
        elif type_of_rotors == 'intermix':
            M = 1 * 0.6 * V
            return M
    return None  # Return None if the rotor type is not recognized




def Miner_Rule_Fatigue(n,N):
    '''
    

    Parameters
    ----------
    n : list
        number of cycles at stress level 

    N : list
        number of cycles to failure at stress level

    Returns
    -------
    sigma : float

    '''
    sigma=0
    for i in range(0,len(n)):
        for j in range(0,len(N)):
            if i==j:
                sigma=sigma+(n[i]/N[j])
    
    if sigma<1:
        print("There is no fatigue yet")
    elif sigma>=1:
        print("Failure occurs at least according to Miner's rule")
                    
    return sigma




def Nanoparticle_Surface_Area(Shape,Diameter=0,a=0):
    """
    Calculating the surface area of nanoparticle by determinig the shape
    
    Parameters
    ----------
    Shape:str
    (sphere,cube or tetrahedron)
    
    Diameter : int
    DESCRIPTION. The default is 0.
    (it is needed for spherical nanoparticles)
    unit(nm)
       
    a : int
    dimention
    unit(nm)
    DESCRIPTION. The default is 0.
    (it is needed for cubic or tetragonal nanoparticles)
    unit(nm)
    
    Returns
    -------
    Nanoparticle_Surface_Area : int
    unit(nm^2) 

    """
    if Shape=='sphere':
        Nanoparticle_Surface_Area=math.pi*(Diameter**2)
        print(Nanoparticle_Surface_Area)
        return Nanoparticle_Surface_Area
    elif Shape=='cube':
        Nanoparticle_Surface_Area=6*(a**2)
        print(Nanoparticle_Surface_Area)
        return Nanoparticle_Surface_Area
    elif Shape=='tetrahedron':
        Nanoparticle_Surface_Area=(3**0.5)*(a**2)
        print(Nanoparticle_Surface_Area)
        return Nanoparticle_Surface_Area
    else: 
        print('please retry and enter the needed parameters corectly')





def Nanoparticle_Aspect_Ratio(lenght=1,width=1,height=1):
    """
    Calculating the Nanoparticle_Aspect_Ratio 

    Parameters
    ----------
    lenght : int
        lenght of a nanoparticle
        DESCRIPTION. The default is 1.
        unit(nm)
    width : int
        width of a nanoparticle
        DESCRIPTION. The default is 1.
        unit(nm)
    height : int
       height of a nanoparticle
       DESCRIPTION. The default is 1.
       unit(nm)

    Returns
    -------
    Nanoparticle_Aspect_Ratio : float
        the ratio of maximum dimention of a nanoparticle to minimum dimention of it.

    """
    maximum=max(lenght,width,height)
    minimum=min(lenght,width,height)
    Nanoparticle_Aspect_Ratio=maximum/minimum
    print('Nanoparticle_Aspect_Ratio=',Nanoparticle_Aspect_Ratio)
    return Nanoparticle_Aspect_Ratio




def Nanoparticle_Volume(Shape,Diameter=0,a=0):
    """
    Calculating the Volume of a nanoparticle by determinig the shape
    
    Parameters
    ----------
    Shape:str
    (sphere,cube or tetrahedron)
    
    Diameter : int
    DESCRIPTION. The default is 0.
    (it is needed for spherical nanoparticles)
    unit(nm)
       
    a : int
    dimention
    unit(nm)
    DESCRIPTION. The default is 0.
    (it is needed for cubic or tetragonal nanoparticles)
    unit(nm)
    
    Returns
    -------
    Nanoparticle_Volume : int
    unit(nm^3) 

    """
    if Shape=='sphere':
        Nanoparticle_Volume=math.pi*((Diameter**3)/6)
        print(Nanoparticle_Volume)
        return Nanoparticle_Volume
    elif Shape=='cube':
        Nanoparticle_Volume=a**3
        print(Nanoparticle_Volume)
        return Nanoparticle_Volume
    elif Shape=='tetrahedron':
        Nanoparticle_Volume=(2**0.5)*(a**3)/12
        print(Nanoparticle_Volume)
        return Nanoparticle_Volume
    else: 
        print('please retry and enter the needed parameters corectly')



def newtons_second_law(force, mass, acceleration):
    """
    Calculates a value based on Newton's second law of motion.
    Note: The provided formula returns the difference, not a direct calculation of a single variable.

    Parameters
    ----------
    force : float
        The net force acting on the object (in Newtons).
    mass : float
        The mass of the object (in kilograms).
    acceleration : float
        The acceleration of the object (in meters per second squared).

    Returns
    -------
    float
        The result of the expression: force - (mass * acceleration).
        According to Newton's second law: force = mass * acceleration.
        To solve for a specific variable, rearrange this equation.
    """
    return force - mass * acceleration


def Ohms_Law(voltage, current, resistance):
    """
    Calculates a value based on Ohm's law.
    Note: The provided formula returns the difference, not a direct calculation of a single variable.

    Parameters
    ----------
    voltage : float
        The voltage across the conductor (in Volts).
    current : float
        The current flowing through the conductor (in Amperes).
    resistance : float
        The resistance of the conductor (in Ohms).

    Returns
    -------
    float
        The result of the expression: voltage - (current * resistance).
        According to Ohm's law: voltage = current * resistance.
        To solve for a specific variable, rearrange this equation.
    """
    return voltage - current * resistance


def Poisson(transverse_strain, axial_strain):
    """
    Calculates Poisson's ratio of a material under axial stress.

    Parameters
    ----------
    transverse_strain : float
        The strain in the direction perpendicular to the applied force (dimensionless).
    axial_strain : float
        The strain in the direction of the applied force (dimensionless).

    Returns
    -------
    float
        Poisson's ratio (v), a dimensionless material property.
    """
    v = -(transverse_strain / axial_strain)
    return v


def pH_Which(pH):
    """
    Determines if a solution is acidic, neutral, or basic based on its pH value and prints the result.

    Parameters
    ----------
    pH : float
        The pH value of the solution.

    Returns
    -------
    None
        This function prints the classification of the solution and does not return a value.
    """
    if pH < 7:
        print('This solution is acidic')
    elif pH == 7:
        print('This solution is neutral')
    elif pH > 7:
        print('This solution is basic')
        
        
        
        


def Principal_Stress(Sx,Sy,Sz,Txy,Tyz,Txz):
    '''
    make sure stress value is less than 1000       
    Parameters
    ----------
    Sx  : (int or float)
          Normal stress along x       
    Sy  : (int or float)
          Normal stress along y       
    Sz  : (int or float)
          Normal stress along z       
    Txy : (int or float)
          Shear stress along xy       
    Tyz : (int or float)
          Shear stress along yz       
    Txz : (int or float)
          Shear stress along xz       
    Returns
    -------
    S_P : [S1,S2,S3]
          Principal stresses

    '''
    
      
    a=1
    b=Sx+Sy+Sz
    c=Sx*Sy+Sy*Sz+Sx*Sz-Txy**2-Tyz**2-Txz**2
    d=Sx*Sy*Sz+2*Txy*Tyz*Txz-Sx*Tyz**2-Sy*Txz**2-Sz*Txy**2
    
    
    # aS^3-bS^2+cS-d=0

    S_P=[0,0,0]
    #-------------Numerical Calculation---------------
    sp=0
    for i in range(2001):
        x0=-1000+i
        f0=a*x0**3-b*x0**2+c*x0-d
        x1=x0+1
        f1=a*x1**3-b*x1**2+c*x1-d
        if f0>-10 and f0<10:
            S_P[sp]=x0
            if sp==2:
                break
            sp=sp+1
        else:
            if f0*f1<0:
                while i>-1:
                    x=(x0+x1)/2
                    f=a*x**3-b*x**2+c*x-d
                    if f>-10 and f<10:
                        S_P[sp]=x
                        if sp==2:
                            break
                        sp=sp+1
                        break
                    elif f0*f<0:
                        x1=x
                        f1=f
                    else:
                        x0=x
                        f0=f
            else:
                continue
                        
    
    return S_P





def Pythagorean(side1,side2):
    '''
    It should be an orthogonal triangle and this function gives you hypotenuse

    Parameters
    ----------
    side1 : int
        side of "orthogonal triangle".
    side2 : int
        side of "orthogonal triangle".

    Returns
    -------
    hypotenuse: int
       hypotenuse of "orthogonal triangle".

    ''' 
    hypotenuse =((side1**2)+(side2**2))**(1/2)
    return hypotenuse





def Pythagorean_Theorem(a, b):
    """
    Calculates the length of the hypotenuse of a right-angled triangle using the Pythagorean theorem.

    Parameters
    ----------
    a : float
        The length of one of the shorter sides of the triangle.
    b : float
        The length of the other shorter side of the triangle.

    Returns
    -------
    float
        The length of the hypotenuse.
    """
    return math.sqrt(a**2 + b**2)




def Photoelectric_Effect(kinetic_energy, photon_energy, work_function):
    """
    Calculates a value related to the photoelectric effect.
    Note: The provided formula returns the difference, not a direct calculation of a single variable.

    Parameters
    ----------
    kinetic_energy : float
        The kinetic energy of the emitted electron (in Joules or eV).
    photon_energy : float
        The energy of the incident photon (in Joules or eV).
    work_function : float
        The minimum energy required to remove an electron from the surface of the material (in Joules or eV).

    Returns
    -------
    float
        The result of the expression: kinetic_energy - (photon_energy - work_function).
        According to the photoelectric effect equation:
        kinetic_energy_max = photon_energy - work_function.
        To solve for a specific variable, rearrange this equation.
    """
    return kinetic_energy - (photon_energy - work_function)




def is_Pythagorean(a,b,c):
    """
    

    Parameters
    ----------
    a : float
        tool zele aval.
    b : float
        tool zele dovom.
    c : float
        tool zele sevom.

    Returns be ma mige in adad mitoonan mosalas ghaem alazviye tashkil bedan 
    ba "mosalas ghaemalzaviye mishe" va" mosalas ghaemalzaviye nemishe"
    -------

    """
    if a**2==b**2+c**2 or b**2==a**2+c**2 or c**2==a**2+b**2:
        return True
    else:
        return False




def Polygonal_Diameters(n):
    """
    

    Parameters
    ----------
    n : int
        tedad azlae chand zelei(az 2 ta bishtar).

    Returns tedad ghotrhaye chand zelei
    -------

    """
    return((n*(n-3))/2)




def PengRobinson(T = None,P = None,Tc = None,Pc = None,w = None,MW = None,Phases = None):
    """
    PengRobinson.m : calculates the compressibility factor,fugacity coefficient and density
    of a pure compound with the Peng Robinson equation of state (PR EOS)

    Parameters
    ----------
    T : float
        Temperature [=] K
    P : float
        Presure [=] Pa
    Tc : float
        Critical temperature [=] K
    Pc : float
        Critical presure [=] Pa
    w : float
        Accentic factor
    MW : float
        Molar weigth [=] kg/mol.
    Phases : int
        if Phases == 1, then calculates liquid fugacity;
        if Phases == 0 then calculates vapor fugacity

    Returns
    -------
    Z : flout
        Compressibility factor
    fhi : float
        Fugacity coefficient
    density : float
        Density

    """
    R = 8.314
    
    # Reduced variables
    Tr = T / Tc
    
    # Parameters of the EOS for a pure component
    m = 0.37464 + 1.54226 * w - 0.26992 * w ** 2
    alfa = (1 + m * (1 - np.sqrt(Tr))) ** 2
    a = 0.45724 * (R * Tc) ** 2 / Pc * alfa
    b = 0.0778 * R * Tc / Pc
    A = a * P / (R * T) ** 2
    B = b * P / (R * T)
    # Compressibility factor
    Z = np.roots(np.array([1,- (1 - B),(A - 3 * B ** 2 - 2 * B),- (A * B - B ** 2 - B ** 3)]))
    ZR = []
    for i in range(3):
        if type(Z[i])!='complex':
            ZR.append(Z[i])
    
    if Phases == 1:
        Z = np.amin(ZR)
    else:
        Z = np.amax(ZR)
    
    # Fugacity coefficient
    fhi = np.exp(Z - 1 - np.log(Z - B) - A / (2 * B * np.sqrt(2)) * np.log((Z + (1 + np.sqrt(2)) * B) / (Z + (1 - np.sqrt(2)) * B)))
    if True:
        density = P * MW / (Z * R * T)
        result = np.array([Z,fhi,density])
    else:
        'No real solution for "fhi" is available in this phase'
        result = np.array(['N/A','N/A','N/A'])
    

    return result






def Planks_Fix(y,R,r):
    '''
    This formula is used to calculate the wall pressure of bleeding in the veins
    This function receives the variables y, r, R and returns the variable p
    p:It indicates the pressure of the bleeding wall.
    y:Surface coefficient is surface tension
    R:is the inner radius of the vessel.
    r:is the thickness of the vessel wall.
    '''
    p=2*y*R/r
    return p





def Power_Factor(i,v):
    '''
    Parameters
    ----------
    This function receives the variables i, v and returns the variable P
    i : int
        It is an electric current that passes through a circuit
    v : int
        It is an electric current that passes through a circuit
    p : int
        It indicates the power used or produced.
    
    '''
    p=i*v
    return p






def Print_Time(Print_speed,Volume,Printer_efficiency):
    
    ''' volume(float)= usually Cm3
    
    print_speed(float)= and is speed of print usually cm3 per hour)
    
    Printer_efficience(float)= and between 0 -1)
    
    Retuen:
        
        Print_time=(float)
        the time of print in hour 
    
    '''
    Print_time=float(Volume)/(float(Print_speed)*float(Printer_efficiency))
    return Print_time



def Predict_Phase_From_Gibbs(g1, g2, temp):
    """
    Predict which phase is thermodynamically favored at a given temperature.

    Parameters
    ----------
    g1 : callable
        Gibbs free energy function for phase 1: G(T) in J/mol
    g2 : callable
        Gibbs free energy function for phase 2: G(T) in J/mol
    temp : float
        Temperature in Kelvin.

    Returns
    -------
    str
        Name of the stable phase ("Phase 1", "Phase 2", or "Both").
    """
    g1_val = g1(temp)
    g2_val = g2(temp)

    if abs(g1_val - g2_val) < 1e-5:
        return "Both (Coexistence)"
    return "Phase 1" if g1_val < g2_val else "Phase 2"




def Quadratic_Equation(a,b,c):
    '''
    This function find "x" in equation ax^2 + bx + c = 0

    Parameters
    ----------
    a : int
        known number.
    b : int
        known number.
    c : int
        known number.

    Returns
    -------
   The Quadratic Equation mostly have two answers!
    x1 ,x2 : int
       the unknown.

    '''
    if a==0:
        print('Error: This is not a quadratic equation')
    elif ((b**2)-(4*a*c))<0:
        print("Error:this equation doesn't have an answer")
    else:
        x1=(-b+(((b**2)-(4*a*c))**(1/2)))/(2*a)
        x2=(-b-(((b**2)-(4*a*c))**(1/2)))/(2*a)
        if x1==x2:
            return x1
        else:
            return x1,x2
        



def Quantum_Harmonic_Oscillator_Energy(n, hbar, omega):
    """
    Calculates the energy levels of a quantum harmonic oscillator, a fundamental
    model in quantum mechanics that describes systems undergoing oscillatory
    motion, such as vibrations of atoms in a molecule or lattice.

    Parameters
    ----------
    n : int
        The quantum number of the energy level (n = 0, 1, 2, ...). n=0 is the
        ground state, and higher values represent excited states.
    hbar : float
        The reduced Planck constant (h / 2π).
    omega : float
        The angular frequency of the oscillator (in radians per second).

    Returns
    -------
    float
        The energy of the n-th quantum energy level of the harmonic oscillator (in Joules or electronvolts, depending on the units of hbar and omega).
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("The quantum number 'n' must be a non-negative integer.")
    return (n + 0.5) * hbar * omega



def Rectangle_Area(length,width):
    '''
    This function calculate the area of square too!

    Parameters
    ----------
    length : int
        length of rectangle.
    width : int
        width of rectangle.

    Returns
    -------
    rectangle_area: int
      area of rectangle.

    '''
    rectangle_area=length*width
    return rectangle_area




    
def Rolling_Parameters_Calculator (roller_radius, flow_stress, sample_width, 
                                   wanted_thickness_reduction, coefficient_of_friction = None) :
    '''
    

    Parameters
    ----------
    roller_radius : float
        roller radius in term of meter.
    
    flow_stress : float
        flow stress of your sample in term of Pascal.
   
    sample_width : float
        sample width in meter.
   
    wanted_thickness_reduction : float
        wanted thickness reduciton (delta h) in terms of meter.
    
    coefficient_of_friction : floea, optional
        coefficient of friction between the roller and your sample. 
        notice :
            
            if you give nothing for friction of coefficeint, function assumed that this
            coefficient is 0.2 and didnt include the role of friction in the rolling force formula. (* 1.2) 
            but if you enter a value for this, function include the role of friction in the process 
            and multiplies the rolling force by 1.2

    Returns
    -------
    delta_h_max : float
       the maximum thickness reduction that can be reached in terms of meter.
    
    h_min : float
        minimum thickness that can be reached in terms of meters.
    
    rolling_force : float
        the required force for rolling in terms of Newton.
        
        
        
    ### important : this function give all output in scientific notation.

    '''
    
    
    
    if coefficient_of_friction == None :
        
        # calculating delta h max (assumed frcition coefficient 0.2)
        delta_h_max = "{:e}".format((0.2 ** 2) * roller_radius)
        
        # calculating h min (assumed friction coefficient 0.2)
        h_min = "{:e}".format(0.35 * 0.2 * roller_radius * flow_stress)
    else :
        
        # calculatin delta h max with given friction coefficient
        delta_h_max = "{:e}".format((coefficient_of_friction ** 2) * roller_radius)
        
        # calculaitin h min with given friction coefficeint         
        h_min = "{:e}".format(0.35 * coefficient_of_friction * roller_radius * flow_stress)
        
    if coefficient_of_friction == None :
        
        # calculating rolling force (assumed as a ideal process without friction)
        rolling_force = "{:e}".format(sample_width * flow_stress * (math.sqrt(roller_radius*wanted_thickness_reduction)))
    else :
        
        # calculatin rolling force (assumed as a real process with friction)
        rolling_force = "{:e}".format(sample_width * flow_stress * (math.sqrt(roller_radius*wanted_thickness_reduction)) * 1.2)
        
    
    return delta_h_max, h_min, rolling_force




def Rectangle_Perimeter(length,width):
    '''
    This function calculate the perimeter of square too!  

    Parameters
    ----------
    length : int
        length of rectangle.
    width : int
        width of rectangle.

    Returns
    -------
    rectangle_perimeter: int
       

    '''
    rectangle_perimeter=2*(length+width)
    return rectangle_perimeter



def Root_Degree2(a, b, c):
    """
    Calculates the real roots of a quadratic equation of the form ax^2 + bx + c = 0.

    Parameters
    ----------
    a : float
        The coefficient of the x^2 term.
    b : float
        The coefficient of the x term.
    c : float
        The constant term.

    Returns
    -------
    tuple or None
        A tuple containing two real roots (may be equal if delta == 0),
        or None if no real roots exist.
    """
    delta = b**2 - 4 * a * c

    if delta > 0:
        x1 = (-b + math.sqrt(delta)) / (2 * a)
        x2 = (-b - math.sqrt(delta)) / (2 * a)
        return x1, x2
    elif delta == 0:
        x = -b / (2 * a)
        return x, x  # Still return a tuple for consistency
    else:
        return None

def Rayleigh_Scattering(intensity, wavelength, particle_size):
    """
    Calculates a value related to the intensity of Rayleigh scattering.
    Note: The provided formula returns the difference, not the scattered intensity.

    Parameters
    ----------
    intensity : float
        The initial intensity of the incident light.
    wavelength : float
        The wavelength of the incident light.
    particle_size : float
        The size of the scattering particles.

    Returns
    -------
    float
        The result of the expression: intensity - (particle_size / wavelength)**4.
        The intensity of Rayleigh scattering is actually proportional to (1/wavelength)^4 and the size of the particle.
        The provided formula doesn't directly represent the scattered intensity.
    """
    return intensity - (particle_size / wavelength)**4


def Rydberg_Formula(wavelength, rydberg_constant, principal_quantum_number):
    """
    Calculates a value related to the Rydberg formula for the wavelengths of spectral lines of hydrogen-like atoms.
    Note: The provided formula returns the difference, not the inverse of the wavelength.

    Parameters
    ----------
    wavelength : float
        The wavelength of the emitted photon.
    rydberg_constant : float
        The Rydberg constant for the atom.
    principal_quantum_number : float
        The principal quantum number of the energy level.

    Returns
    -------
    float
        The result of the expression: (1 / wavelength) - (rydberg_constant * principal_quantum_number**2).
        The standard Rydberg formula is: 1/wavelength = Rydberg_constant * (1/n1^2 - 1/n2^2), where n1 and n2 are principal quantum numbers.
    """
    return 1 / wavelength - rydberg_constant * principal_quantum_number**2


def Reynolds_Number_Pipe(d, u, vis, D_H):
    """
    Calculates the Reynolds number for flow in a pipe.

    Parameters
    ----------
    d : float
        The density of the fluid (e.g., in kg/m^3).
    u : float
        The average velocity of the fluid (e.g., in m/s).
    vis : float
        The dynamic viscosity of the fluid (e.g., in Pa·s).
    D_H : float
        The hydraulic diameter of the pipe (e.g., in meters).

    Returns
    -------
    float
        The Reynolds number (Re), a dimensionless quantity.
    """
    Re = (d * u * D_H) / vis
    return Re






def Rejection(CF, CP):
    """
    Calculates the rejection rate (%) of a membrane based on pollutant concentrations.

    Parameters
    ----------
    CF : float
        The pollutant concentration in the feed solution (g/l).
    CP : float
        The pollutant concentration in the permeate solution (g/l).

    Returns
    -------
    float
        The membrane rejection rate in percent (%).
    """
    Rej = (1 - (CP / CF)) * 100
    return Rej


def Shear_Rate(Q, p, r, n):
    """
    Calculates the shear rate for a power-law fluid flowing in a pipe.
    Note: The variable 'p' is unusual in standard shear rate formulas for pipe flow. Assuming it might be pi.

    Parameters
    ----------
    Q : float
        The volumetric flow rate (e.g., in m^3/s).
    p : float
        Likely intended to be pi (π ≈ 3.14159).
    r : float
        The radius of the pipe (e.g., in meters).
    n : float
        The flow behavior index for a power-law fluid (dimensionless).

    Returns
    -------
    float
        The shear rate (γ̇) at the pipe wall (e.g., in s^-1).
    """
    y = (Q / (p * r**3)) * (3 + 1/n)
    return y


def Shear_Stress(F, A):
    """
    Calculates the shear stress acting on a surface.

    Parameters
    ----------
    F : float
        The shear force acting parallel to the surface (e.g., in Newtons).
    A : float
        The area of the surface over which the shear force acts (e.g., in square meters).

    Returns
    -------
    float
        The shear stress (τ) (e.g., in Pascals).
    """
    T = F / A
    return T





def Stress_Intensity_Factor(stress, crack_length, crack_type):
    '''
    Calculate the stress intensity factor (K) based on the type of crack.
    K = crack_type * stress * (sqrt(pi * crack_length))
    Parameters
    ----------
    stress : float
        applied stress (sigma).
    crack_length : float
        lenght of the crack (a).
    crack_type : str
        there are 3 types of crack 'surface', 'circular', 'internal'.

    Returns: float
        Stress intensity factor (K).

    '''
    if crack_type == 'surface': #ضریب شدت تنش سطحی
        K = 1.12 * stress * (3.1415 ** 0.5) * (crack_length ** 0.5)
        
    elif crack_type == 'circular': #ضریب شدت تنش برای ترک سکه ای
        K = (2/3.1415) * stress * (3.1415 ** 0.5) * (crack_length ** 0.5) 
        
    elif crack_type == 'internal': #ضریب شدت تنش برای ترک داخلی
        K = 1 * stress * (3.1415 ** 0.5) * (crack_length ** 0.5)
    else:
        raise ValueError("Invalid crack type. Choose from 'surface', 'circular', or 'internal'.")
        
    return K






def Solidification_Front_Composition (partition_coefficient, alloy_composition, solid_fraction, law_type = 'lever'):
    '''
    

    Parameters
    ----------
    partition_coefficient : float
        a non-dimensional value that describe the scope of liquidus line.
    
    alloy_composition : float
        initial composition of your alloy in terms of Wt % of left element in phase diagram.
    
    solid_fraction : float
        how much of your alloy solidified.
    
    law_type : str, optional
        you can choose two different model for solidification. lever and scheil.
        The default is 'lever'.

    Returns
    -------
    solid_front_massfraction : float 
        solid mass fraction in solidification front in terms of Wt % of left element in phase diagram.
    
    liquid_front_conc : float
        liquid mass fraction in solidification front in terms of Wt % of left element in phase diagram .
        
        
    notice :
            
        This function round answers to two decimals.
    '''
    
    
    
    if law_type.strip().lower() == 'lever' :
    # calculate base on lever rule
    
        solid_front_massfraction = round((partition_coefficient * alloy_composition * (1 
                     + (solid_fraction * (partition_coefficient - 1))) ** -1), 2)
    else :
    # calculate base on scheil rule
    
        solid_front_massfraction = round(( partition_coefficient * alloy_composition * (1 
                    - solid_fraction) ** (partition_coefficient - 1)), 2)
    # calcute liquid front mass fraction
    
    liquid_front_massfraction = round((solid_front_massfraction / partition_coefficient), 2 )
    
    return solid_front_massfraction, liquid_front_massfraction





def Sphere_Area (R):
    S = 4 * math.pi * R**2
    return S



def Sphere_Volume(radius):
    '''
    

    Parameters
    ----------
    radius : int
        radius of sphere.

    Returns
    -------
    sphere_volume: int
        volume of sphere.

    '''
    sphere_volume=(4*(radius**3)*math.pi)/3
    return sphere_volume





    
    
def Sphere_Surface_Area(radius):
    '''
    

    Parameters
    ----------
    radius : int
        radius of sphere.

    Returns
    -------
    sphere_surface_area: int
        surface area of sphere .

    '''
    sphere_surface_area=(4*math.pi*(radius**2))
    return sphere_surface_area
    
    
    
    
    
    
def Sample_Size_Calculation(N,e):
    '''
    
This  function estimates the number of evaluable subjects required for achieving desired statistical significance for a given hypothesis. 

    Parameters
    ----------
    N : int
        population of the study 
    e : float
        margin error

    Returns
    int
      Sample_Size_Calculation

    '''
    return((N)/(1+N)*(e**2))
    
    
      



def Stress(strain,young_modulus):
    '''
    #The Young's modulus (E) is a property of the material that tells us how easily it can stretch and deform 
    and is defined as the ratio of tensile stress (σ=S) to tensile strain (ε=Ts)

    Parameters
    ----------
    strain : tensile strain (ε)
    
    young_modulus : Modulus of Elasticity (N/m2)

    Returns
    -------
    S : tensile stress (σ)

    '''
       
    S=strain*young_modulus
    return S





def Standard_Deviation(a):
    '''
    This function calculates the standard deviation of a list of numbers.

    Parameters
    ----------
    a : list
        a is a list of numbers.

    Returns
    -------
    SD : float
        SD is the standard deviation of a list of numbers.

    '''
    E = 0
    F = 0
    
    for i in a:
        E = E + i       #sum of numbers
    M = E / len(a)      #Mean
    
    for i in a:
        D = (i - M) ** 2
        F = F + D
    SD2 = (F / (len(a) - 1))
    SD = math.sqrt(SD2)
    return SD




def Solubility (a,b,c,T, T_unit, T_end):
    '''
     Parameters
    ----------
    a : float
        Constant.
    b : float
        Constant.
    c : float
        Constant.
    T : float
        Temperature.
    T_unit:str
        Unit of temperature.
    T_end: float
        Final temperature

    Returns
    -------
    Determination solubility at different temperatures upto solubility< 1
    '''

    if T_unit=='C':
        T_unit=T_unit+273.15
    elif T_unit=='F':
        T_unit= ((T_unit-32)/1.8)+273.15
    elif T_unit=='R':
        T_unit=T_unit*5/9
        
  
    for T in range (T,T_end):
        S=a*T**2+b*T+c
        if S<1:
            continue
        else:
            break
    return S








def Trapezium_Area(Base1,Base2,Height):

    '''
	Parameters
    ----------
    Base1 : int
       base of trapezium
    
    Base2 : int
       base of trapezium
      
    Height : int
       height of trapezium

    Returns
    -------
    Area : int
        Area of trapezium
    '''
    Area=((Base1+Base2)*Height)/2
    return Area





def Trapezium_Perimeter(Base1,Base2,Side1,Side2):
    '''
    Parameters
    ----------
    Base1 : int
       base of trapezium.
    
    Base2 : int
        base of trapezium.
    
    Side1 : int
        side of trapezium.
    
    Side2 : int
        side of trapezium.

    Returns
    -------
    Perimeter : int
       perimeter of trapezium

    '''
    Perimeter=Base1+Base2+Side1+Side2
    return Perimeter



def Tensile_Strength (f,a):
    
    '''
    Parameters
    ----------
    f : int
       force required to break
       
    a : int
       cross sectional area
    -------
    c : int
       Tensile_Strength
    '''
    c=f/a
    return c








def Triangle_Environment (first_side,second_side,third_side):
    '''
    This function gets the perimeter of the triangle

    Parameters
    ----------
    first_side : float
        The size of the first side.
    second_side : float
       The size of the second side.
    third_side : float
        The size of the third side.

    Returns
    -------
    Environment : float
       The output is the perimeter of the triangle.

    '''
    
    Environment=first_side+second_side+third_side
    return Environment
   





def Triangle_Area(Height,rule):
    '''
    This function obtains the area of ​​the triangle

    Parameters
    ----------
    Height : float
        The size of the height of the triangle.
    rule : float
        The size of the base of the triangle is.

    Returns
    -------
    area : float
        The output is the area of ​​the triangle.

    '''
    area=(Height*rule)/2
    return (area) 




def TB(P,N):
    '''
    This function is used for bubble temp calculation in mixed solution
    P : pressure (mmhg)
    N : number of component
    Returns bubble temp
    '''
    Material=['0=Aceton','1=Acetonitrile','2=Acrylonitrile','3=Ammonia','4=Aniline','5=Benzalehyde','6=Benzene','7=n-Butane','8=n-Butanol','9=iso-Butane','10=iso-Butanol','11=Butylacetate','12=Carbondisulphide','13=Carbontetrachloride','14=Chlorobenzene','15=Chloroform','16=Cyclohexane','17=Cyclohexanol','18=Cyclohexanone','19=Cyclopentane','20=Dioxane','21=Dichloromethane','22=Diethylether','23=Diethylamine','24=Ethanol','25=Ethylacetate','26=Ethylbenzene','27=Ethylamine','28=Formicacid','29=Furfural','30=n-Hexane','31=n-Heptane','32=Methanol','33=Methylacetate','34=Nitrobenzene','35=Nitrogen','36=n-Octane','37=Oxygen','38=Octanol','39=n-Pentane','40=Phenol','41=n-Propanol','42=iso_Propanol','43=Propane','44=Pyridine','45=Styrene','46=Tetrahydrofuran','47=Toluene','48=Trichloroethylene','49=Triethylamine','50=o-Xylene','51=p-Xylene','52=Water']
    A=[16.39112,16.90395,15.92847,17.51202,16.67784,6.73163,15.9037,15.68151,17.62995,15.77506,18.02933,16.4145,15.77889,15.8434,16.4,16.017,15.7794,19.23534,16.40517,15.8602,17.1151,17.0635,16.5414,15.73382,18.68233,16.35578,16.04305,7.3862,15.9938,15.14517,15.9155,15.877,18.61042,16.58646,16.42172,15.3673,15.9635,15.06244,7.18653,15.8365,15.9614,17.8349,20.4463,15.7277,16.152,15.94618,16.11023,16.00531,15.01158,15.7212,7.00154,6.99052,18.5882]
    B=[2787.5,3413.1,2782.21,2363.24,3858.22,1369.46,2789.01,2154.9,3367.12,2133.24,3413.34,3293.66,2585.12,2790.78,3485.35,2696.25,2778,5200.53,3677.63,2589.2,3579.78,3053.08,2847.72,2434.73,3667.7,2866.6,3291.66,1137.3,2982.45,2760.09,2738.42,2911.32,3392.57,2839.21,3485.35,648.59,3128.75,674.59,1515.427,2477.07,3183.67,3310.4,4628.95,1872.82,3124.45,3270.26,2768.37,3090.78,2345.48,2674.7,1476.393,1453.43,3984.92]
    C=[229.67,250.48,222,250.54,200,177.081,220.79,238.74,188.7,245,199.97,210.75,236.46,226.46,224.87,226.24,223.14,251.7,212.7,231.36,240.35,252.6,253,212,226.1,217.9,213.8,235.85,218,162.8,226.2,226.65,230,228,224.84,270.02,209.85,263.07,156.767,233.21,159.5,198.5,252.64,250,212.66,206,226.3,219.14,192.73,205,213.872,215.307,233.43]

    x=[]
    T=[]
    a=[]
    b=[]
    c=[]
    d=len(Material)
    Index=[]
    guess=0
    p=[]
    U=0

    print(Material)
    for i in range(0,N):
        I=[int(input('enter component index='))] 
        Index=Index+I
    i=0
    for e in range(0,d):
        if i==N:
            break
        elif Index[i]==e:
            a=a+[[A[e]]]
            b=b+[[B[e]]]
            c=c+[[C[e]]]
            i=i+1
        else:
            e=e+1
    for i in range(0,N):
        X=[float(input('enter component mole fraction='))] 
        x=x+X
    for i in range(0,N):
        t=[(B[Index[i]]/((A[Index[i]])-math.log(P,math.e))-C[Index[i]])]
        T=T+t
    n=0
    while n<100000:
        if int(U)==int(P):
            TBP=guess
        else:
            guess=guess+0.01
            p=[]
            for i in range(0,N):        
                pr=[math.exp(A[Index[i]]-((B[Index[i]])/((C[Index[i]])+guess)))]
                p=p+pr
                U=0
            for i in range(0,N):           
                u=p[i]*x[i]
                U=u+U
        n=n+1
    return TBP
  




def TD(P,N):
    '''
    This function is used for dew temp calculation in mixed solution
    P : pressure (mmhg)
    N : number of component
    Returns bubble temp
    '''
    Material=['0=Aceton','1=Acetonitrile','2=Acrylonitrile','3=Ammonia','4=Aniline','5=Benzalehyde','6=Benzene','7=n-Butane','8=n-Butanol','9=iso-Butane','10=iso-Butanol','11=Butylacetate','12=Carbondisulphide','13=Carbontetrachloride','14=Chlorobenzene','15=Chloroform','16=Cyclohexane','17=Cyclohexanol','18=Cyclohexanone','19=Cyclopentane','20=Dioxane','21=Dichloromethane','22=Diethylether','23=Diethylamine','24=Ethanol','25=Ethylacetate','26=Ethylbenzene','27=Ethylamine','28=Formicacid','29=Furfural','30=n-Hexane','31=n-Heptane','32=Methanol','33=Methylacetate','34=Nitrobenzene','35=Nitrogen','36=n-Octane','37=Oxygen','38=Octanol','39=n-Pentane','40=Phenol','41=n-Propanol','42=iso_Propanol','43=Propane','44=Pyridine','45=Styrene','46=Tetrahydrofuran','47=Toluene','48=Trichloroethylene','49=Triethylamine','50=o-Xylene','51=p-Xylene','52=Water']
    A=[16.39112,16.90395,15.92847,17.51202,16.67784,6.73163,15.9037,15.68151,17.62995,15.77506,18.02933,16.4145,15.77889,15.8434,16.4,16.017,15.7794,19.23534,16.40517,15.8602,17.1151,17.0635,16.5414,15.73382,18.68233,16.35578,16.04305,7.3862,15.9938,15.14517,15.9155,15.877,18.61042,16.58646,16.42172,15.3673,15.9635,15.06244,7.18653,15.8365,15.9614,17.8349,20.4463,15.7277,16.152,15.94618,16.11023,16.00531,15.01158,15.7212,7.00154,6.99052,18.5882]
    B=[2787.5,3413.1,2782.21,2363.24,3858.22,1369.46,2789.01,2154.9,3367.12,2133.24,3413.34,3293.66,2585.12,2790.78,3485.35,2696.25,2778,5200.53,3677.63,2589.2,3579.78,3053.08,2847.72,2434.73,3667.7,2866.6,3291.66,1137.3,2982.45,2760.09,2738.42,2911.32,3392.57,2839.21,3485.35,648.59,3128.75,674.59,1515.427,2477.07,3183.67,3310.4,4628.95,1872.82,3124.45,3270.26,2768.37,3090.78,2345.48,2674.7,1476.393,1453.43,3984.92]
    C=[229.67,250.48,222,250.54,200,177.081,220.79,238.74,188.7,245,199.97,210.75,236.46,226.46,224.87,226.24,223.14,251.7,212.7,231.36,240.35,252.6,253,212,226.1,217.9,213.8,235.85,218,162.8,226.2,226.65,230,228,224.84,270.02,209.85,263.07,156.767,233.21,159.5,198.5,252.64,250,212.66,206,226.3,219.14,192.73,205,213.872,215.307,233.43]

    x=[]
    T=[]
    a=[]
    b=[]
    c=[]
    d=len(Material)
    Index=[]
    guess=0
    p=[]
    U=0.1

    print(Material)
    for i in range(0,N):
        I=[int(input('enter component index='))] 
        Index=Index+I
    i=0
    for e in range(0,d):
        if i==N:
            break
        elif Index[i]==e:
            a=a+[[A[e]]]
            b=b+[[B[e]]]
            c=c+[[C[e]]]
            i=i+1
        else:
            e=e+1
    for i in range(0,N):
        X=[float(input('enter component mole fraction='))] 
        x=x+X
    for i in range(0,N):
        t=[(B[Index[i]]/((A[Index[i]])-math.log(P,math.e))-C[Index[i]])]
        T=T+t
    n=0
    while n<100000:
        if int(1/U)==int(P):
            TDP=guess
        else:
            guess=guess+0.01
            p=[]
            for i in range(0,N):        
                pr=[math.exp(A[Index[i]]-((B[Index[i]])/((C[Index[i]])+guess)))]
                p=p+pr
                U=0
            for i in range(0,N):           
                u=x[i]/p[i]
                U=u+U
        n=n+1
    return TDP







def Tresca_Yield_For_Principal_Stresses(c,hardness,sigma_1,sigma_2,sigma_3,/):
    '''
    

     Parameters
     ----------
     c : float
         C is a coefficient that is between 0.3 and 0.4 depending on the type of material.
     hardness : float
         brinell and vickers hardness.
     sigma_y : float
         Uniaxial tensile yield strength of material.(Mpa)
     sigma_1 : float
         Principal Stresses.
     sigma_2 : float
         Principal Stresses.
     sigma_3 : float
         Principal Stresses.

     Returns
     -------
     Tresca : float
         Tresca Yield(Mpa)

    '''
    sigma_y = c*hardness 
    
    Max=max(sigma_1,sigma_2,sigma_3)
    Min=min(sigma_1,sigma_2,sigma_3)
    
    Tresca=Max-Min
    
    if Tresca < sigma_y :
        print("It is in the elastic area")
    elif Tresca==sigma_y :
        print("It is on the verge of plastic deformation")
    
    elif Tresca > sigma_y :
        print("Plastic deformation has occurred")
        
    return Tresca
        






def Tresca_Yield_For_Biaxial_Tension(c,hardness,sigma_xx,sigma_yy,tau_xy,/):
    '''
    

    Parameters
    ----------
    c : float
        C is a coefficient that is between 0.3 and 0.4 depending on the type of material.
    hardness : float
        brinell and vickers hardness.
    sigma_y : float
        Uniaxial tensile yield strength of material.(Mpa)
    sigma_y : float
        Uniaxial tensile yield strength of material
    sigma_xx : float
        
    sigma_yy : float
        
    tau_xy : float
        

    Returns
    -------
    Tresca : TYPE
        DESCRIPTION.

    '''

    sigma_y = c*hardness
    sigma_max=(sigma_xx + sigma_yy)/2 + math.sqrt(((sigma_xx-sigma_yy)/2)**2 + tau_xy**2)
    sigma_min=(sigma_xx + sigma_yy)/2 - math.sqrt(((sigma_xx-sigma_yy)/2)**2 + tau_xy**2)

    Tresca=sigma_max-sigma_min
    
    if Tresca < sigma_y :
        print("It is in the elastic area")
    elif Tresca==sigma_y :
        print("It is on the verge of plastic deformation")
    elif Tresca > sigma_y :
        print("Deformation is plastic")
            
    return Tresca
    





def Total_Solidification_Time_of_Casting(volume,surface_area,Cm,n,/):
    '''
    

    Parameters
    ----------
    volume : float
        DESCRIPTION.
    surface_area : float
        DESCRIPTION.
    Cm : float
        It's amount varies depending on the type of material
    n : float
        It's amount varies depending on the type of material but is 
        usually equal to 2
        
    Returns
    -------
    Total_Solidification_Time : float

    '''

    
    Total_Solidification_Time = Cm*((volume/surface_area)**2)
    return Total_Solidification_Time


def Transient_Heat_Conduction_Semi_Infinite_Solid(T_s, T_i, alpha, x, t):
    """
    Calculates the temperature at a depth 'x' and time 't' in a semi-infinite
    solid initially at a uniform temperature 'T_i', whose surface temperature
    is suddenly changed to 'T_s'. This solution is derived from the heat
    diffusion equation and is applicable when the solid is thick enough that
    the temperature change has not yet reached the opposite boundary.

    Parameters
    ----------
    T_s : float
        The constant surface temperature applied at t=0.
    T_i : float
        The initial uniform temperature of the solid.
    alpha : float
        The thermal diffusivity of the solid material (in m^2/s).
    x : float
        The depth from the surface where the temperature is to be calculated (in meters).
    t : float
        The time elapsed since the surface temperature change (in seconds).

    Returns
    -------
    float
        The temperature at depth 'x' and time 't' (in the same units as T_s and T_i).
    """
    if t <= 0:
        return T_i
    eta = x / (2 * math.sqrt(alpha * t))
    erf_eta = math.erf(eta)
    return T_s + (T_i - T_s) * erf_eta



def Velocity_Equation(V1,V2,a):
    """
    

    Parameters
    ----------
    V1 : float
        sorat avaliye moteharek.
    V2 : float
        sorat nahayi moteharek.
    a : floar
        shetab moteharek dar harekat ba shetab sabet.

    Returns mizan jabejayi dar harekat ba shetab sabet
    -------
   

    """
    return (V2**2-V1**2)/2*a






def Vicker_Hardness_Calculation (d1,d2,p): 
    
    '''
    this function is utilized for calculating Vickers hardness.
    in this method, pyramid shape indentor is used.
    
    Parameters
    -----------
    1. d1: float
    d1 represents diameter of impress of indentor.
    
    2. d2 : float
    d2 represents diameter of impress of indentor
    
    3. p : int
    applied load 
    
    Returns --> VHN (Vickers Hardness Number)
    '''
    
    d= (d1+d2)/2
    VHN = (1.854*p)/(d**2)

    return VHN






def Voltage_Standing_Wave_Ratio(Vmax,Vmin):
    '''
    Parameters
    ----------
    Vmax: float
          the highest voltage measured in transition line
    Vmin: float
              the lowest voltage measured in transition line
    Returns
    -------
    Row: float
         its the domain of reflection coefficient of transition line
    '''
    s=Vmax/Vmin
    Row=(s-1)/(s+1)
    return Row




def Young_Modulus(stress, strain):
    """
    Calculates Young's modulus (elastic modulus) of a material under uniaxial tension or compression.

    Parameters
    ----------
    stress : float
        The stress experienced by the material (force per unit area, e.g., in Pascals).
    strain : float
        The dimensionless strain (change in length divided by original length).

    Returns
    -------
    float
        The Young's modulus (E) of the material (in Pascals or equivalent units).
    """
    E = stress / strain
    return E



def Wavelength_Frequency_Relation(speed_of_light, wavelength, frequency):
    """
    Calculates a value based on the relationship between the speed of light, wavelength, and frequency of an electromagnetic wave.
    Note: The provided formula returns the difference, not a direct calculation of one of the variables.

    Parameters
    ----------
    speed_of_light : float
        The speed of light in the medium (e.g., approximately 3e8 m/s in a vacuum).
    wavelength : float
        The wavelength of the electromagnetic wave (e.g., in meters).
    frequency : float
        The frequency of the electromagnetic wave (e.g., in Hertz).

    Returns
    -------
    float
        The result of the expression: speed_of_light - (wavelength * frequency).
        The actual relationship is: speed_of_light = wavelength * frequency.
        To solve for a specific variable, rearrange this equation.
    """
    return speed_of_light - wavelength * frequency




def Wear_Rate(V,F,S):
    '''
    Parameters
    ----------
    V : float
        lost volume during the wear test in terms of cubic milimeters (mm3)
    F : float
        Applied force in terms of newton.
    S : float
        Sliding distance in terms of meter.

    Returns
    -------
    K : Wear rate
        This function is for claculation of wear rate if material after wear test. It is in terms of (10-6 mm3/N.m) 
        

    '''
    K=V/(F*S)
    return K




def William_Landel_Ferry(T,Tg,/):
    '''
    The WLF equation is a procedure for shifting data for amorphous polymers obtained at elevated temperatures to a reference temperature. 

    Parameters
    ----------
    T : int or float
        Temperature, K or degree celsius, Tg<T<Tg+100..
    Tg : int or float
        Glass Transition Temperature, K or degree celsius.
   
    Returns
    -------
    aT : int or float
    shift factor.

    '''
    b=T-Tg 
    c=-17.44*b
    d=51.6+b
    e=c/d
    aT=math.pow(10,e)
    return aT
        

"""
def Web_Service_Analyze(services,resp_times,exe_CPU_costs,exe_Mem_costs,exe_Disk_costs,exe_Net_costs):
    '''
    

    Parameters
    ----------
    services : list pof str
        the list of services..
    resp_times : list of int
        the list of the responce times of specified web services, measured in millisecond.
    exe_CPU_costs : list of int
        list of the percent of execution costs in case 
        of cpu for specified web services.
    exe_Mem_costs : list of int
        list of the percent of execution costs in case 
        of memory for specified web services.
    exe_Disk_costs : list of int
        list of the percent of execution costs in case
        of disk for specified web services.
    exe_Net_costs : list of int
        list of the percent of execution costs in case
        of network for specified web services.

   Returns
   a list of services with their useful information for easily analyze.

'''
    web_services_analyze_data=[]
    for i in range(len(services)):
        serv_name=services[i]
        resp_time=resp_times[i]
        exe_CPU_cost=exe_CPU_costs[i]
        exe_Mem_cost=exe_Mem_costs[i]
        exe_Disk_cost=exe_Disk_costs[i]
        exe_Net_cost=exe_Net_costs[i]
        
        
        
        if resp_time < 100:
            resp_time_st='Excellent'
        elif resp_time >= 100 and resp_time <= 200:
            resp_time_st='good'
        elif resp_time > 200 and resp_time <= 1000:
            resp_time_st='acceptable'
        elif resp_time > 1000 :
            resp_time_st='very slow'
            
            
        if exe_CPU_cost >= 0 and exe_CPU_cost < 30:
                exe_CPU_cost_st='Low Usage'
        elif exe_CPU_cost >= 30 and exe_CPU_cost <= 70:
                exe_CPU_cost_st='Optimal'
        elif exe_CPU_cost > 70 and exe_CPU_cost <= 85:
               exe_CPU_cost_st='Moderate Pressure'
        elif exe_CPU_cost > 85 and exe_CPU_cost <= 100:
                exe_CPU_cost_st='Critical'
                
        
        if exe_Mem_cost >= 0 and exe_Mem_cost < 50:
                exe_Mem_cost_st='Low Usage'
        elif exe_Mem_cost >= 50 and exe_Mem_cost <= 75:
                exe_Mem_cost_st='Optimal'
        elif exe_Mem_cost > 75 and exe_Mem_cost <= 90:
               exe_Mem_cost_st='Moderate Pressure'
        elif exe_Mem_cost > 90 and exe_Mem_cost <= 100:
                exe_Mem_cost_st='Critical'
                
                
        if exe_Disk_cost >= 0 and exe_Disk_cost < 50:
                exe_Disk_cost_st='Low Usage'
        elif exe_Disk_cost >= 50 and exe_Disk_cost <= 75:
                exe_Disk_cost_st='Optimal'
        elif exe_Disk_cost > 75 and exe_Disk_cost <= 90:
               exe_Disk_cost_st='Moderate Pressure'
        elif exe_Disk_cost > 90 and exe_Disk_cost <= 100: 
                exe_Disk_cost_st='Critical'
                
                
        if exe_Net_cost >= 0 and exe_Net_cost < 50:
                exe_Net_cost_st='Low Usage'
        elif exe_Net_cost >= 50 and exe_Net_cost <= 75:
                exe_Net_cost_st='Optimal'
        elif exe_Net_cost > 75 and exe_Net_cost <= 90:
               exe_Net_cost_st='Moderate Pressure'
        elif exe_Net_cost > 90 and exe_Net_cost <= 100: 
                exe_Net_cost_st='Critical'
                
                
       
        web_services_analyze_data.append(('Service Name: '+ serv_name,'Response Time: '+resp_time_st,'CPU Cost: '+ exe_CPU_cost_st,'Memory Cost: '+ exe_Mem_cost_st,'Disk Cost: '+exe_Disk_cost_st,'Network Cost: '+exe_Net_cost_st))
        
    print(web_services_analyze_data)
    return (web_services_analyze_data)

"""


def Welding_Heat_Input(Efficiency,Voltage,Amperage,Speed): 
    '''
    
    Parameters
    ----------
    Efficiency : float
        Efficiency is the proportion of useful inserted heat to the total inserted heat into the weldment.
    Voltage : float
        Voltage is the electrical potential of the welding arc (V).
    Amperage : float
        Amperage is the amount of electrical current in welding (A).
    Speed : float
        Speed is the velocity of the welding tool (cm/min).

    Returns
    -------
    Heat_Input is the useful heat inserted into the weldment.

    '''
   
    Heat_Input=Efficiency*Voltage*Amperage/Speed
    return Heat_Input




def Welding_Deposition_Rate(Deposited_Metal_Mass,Welding_Time):
    '''
    
    Parameters
    ----------
    Deposited_Metal_Mass : flaat
        Deposited_Metal_Mass is the amount of deposited metal during welding (kg).
    Welding_Time : float
        Welding_Time is the consumed time for welding (hr).

    Returns
    -------
    Deposition_Rate is the amount of deposited metal per hour during the welding operation.

    '''
    
    Deposition_Rate=Deposited_Metal_Mass/Welding_Time
    return Deposition_Rate




def Uncertainty_Principle(delta_position, delta_momentum, hbar):
    """
    Calculates a value related to the Heisenberg uncertainty principle.
    Note: The provided formula returns the difference, not a direct evaluation of whether the principle is satisfied.

    Parameters
    ----------
    delta_position : float
        The uncertainty in the position of a particle.
    delta_momentum : float
        The uncertainty in the momentum of the particle.
    hbar : float
        The reduced Planck constant (h / 2π).

    Returns
    -------
    float
        The result of the expression: (delta_position * delta_momentum) - (hbar / 2).
        The Heisenberg uncertainty principle states that the product of the uncertainty in position and the uncertainty in momentum must be greater than or equal to hbar / 2:
        delta_position * delta_momentum >= hbar / 2.
        This function calculates the left-hand side minus the right-hand side. A non-negative result indicates that the principle is satisfied (within the limits of equality).
    """
    return delta_position * delta_momentum - hbar / 2



