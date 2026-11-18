'''
Testing to create a file of parameters
'''
import math


# LATTICE PARAMETERS
Initial_Sample_Height = 315

Lx = 80
Ly = 80
Lz = 600


# CONTACT ENERGIES
J_Medium_Medium = 0.0
J_Medium_Material = 5.0
J_Medium_Pore = 10.0
J_Material_Material = 0.0
J_Material_Pore = 3.0
J_Pore_Pore = 10.0
NgbOrder = 4

# TEMPERATURES
Temperature_Cold = 0.001
Temperature_Hot = 5.0

# ION TRACK
Ion_Radius = 5.0
Pore_Max_Number = 15
Cylinder_Height = 2*Ion_Radius # hypothesis

# fixed pore radius
Pore_Radius_Ave = 1.5


# MATERIAL PARAMETERS
Block_EdgeSize = 4
Block_InitialVolume = Block_EdgeSize**3
Material_LambdaVolume_Cold = 1000.0
Material_LambdaVolume_Hot = 5.0
Material_TargetVolume = Block_InitialVolume

# PORE PARAMETERS
Pore_LambdaVolume_Cold = 1000.0
Pore_LambdaVolume_Hot = 10.0
Pore_TargetVolume = int(4.0*math.pi*Pore_Radius_Ave**3.0/3.0 + 0.5) # in the future needs to be particular to each one


###########################################
# FLUENCY CALCULATOR                      #
# ions/cm^2 -> number of ions             #
# considering 1px = 1nm                   #
# Number_Ions = (Fluency/10^(14)) * Lx*Ly #
###########################################

# Choose desired irradiation fluency in ions/cm^2
Fluency = 1.0*10**14 #ions/cm^2
# is equivalent to this number of simulation ions
Number_Ions = (Fluency/10**14) * Lx * Ly

# MCS STUFF
Relax_Time = 100
MCS_Between_Ions = 25
Total_MCS = Number_Ions * MCS_Between_Ions + Relax_Time*2 + 1 # so there will be a time after last ion
DebFreq = 50
