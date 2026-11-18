from cc3d.core.PySteppables import *
from cc3d.CompuCellSetup.CC3DCaller import CC3DCaller
import sys, os
from os import makedirs
#import os.path
from os.path import dirname, join, expanduser
import inspect, time
import numpy as np
import math
import random
from scipy import stats as st


import parameters as p

class FilmSetup(SteppableBasePy):
    def __init__(self, frequency=1):
        SteppableBasePy.__init__(self, frequency)

    def start(self): 
        import parameters as p
        for cell in self.cell_list_by_type(self.MATERIAL):
            cell.targetVolume = p.Material_TargetVolume
            cell.lambdaVolume = p.Material_LambdaVolume_Cold

class Nucleation(SteppableBasePy):


    def __init__(self, frequency=1):

        SteppableBasePy.__init__(self,frequency)
        # It is best to call this function from __init__ of first registered steppable
# Changing output folder
        self.time=time.strftime("%Y_%m_%d_at_%Hh_%Mm_%Ss")
        output_dir='C:\\CompuCell3D\\CC3DWorkspace\\Results\\'+self.time
        self.set_output_dir(output_dir, abs_path=False)
        
    def start(self):
        import parameters as p
        
# Creating output
        resFolder = 'C:\\CompuCell3D\\CC3DWorkspace\\Results\\'
        # rootFolder = join(expanduser('~'), 'CC3DCallerOutput')
        filePath = os.path.abspath(__file__)
        SourceDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        Dir=SourceDir+"\\Results"
#        self.set_output_dir=Dir+"\\"+self.time
        self.set_output_dir(output_dir=Dir+"\\"+self.time, abs_path=False)
        screenDir = self.output_dir
        grid=self.dim.x
        
        pottsXMLData=self.simulator.getCC3DModuleData("Potts")
        #seedElement=pottsXMLData.getFirstElement("RandomSeed")
        #seed=seedElement.getText()
        fluency='{:.2e}'.format(p.Fluency)
        dimbound="3DPBC"
        Name=dimbound+"_F"+str(fluency)+"_H"+str(p.Initial_Sample_Height)+"_G"+str(grid)+"_IR"+str(p.Ion_Radius)
        # Pra acompanhar o número de células e o volume total de cada tipo
        self.routinetrkName=Dir+"\\"+self.time+"_routinetrk_"+Name+".dat"
        file=open(self.routinetrkName,'w') 
        file.write("%s\n" % ("mcs NM NG MV GV "))
        file.close()
        # Pra acompanhar as posições sorteadas de criação de poro 
        self.creationtrkName=Dir+"\\"+self.time+"_creationtrk_"+Name+".dat"
        file=open(self.creationtrkName,'w') 
        file.write("%s\n" % ("mcs PoreIndex PoreX PoreY PoreZ "))
        file.close()
        # Pra acompanhar a espessura do filme 
        self.htrkName=Dir+"\\"+self.time+"_htrk_"+Name+".dat"
        file=open(self.htrkName,'w') 
        file.write("%s\n" % ("mcs H "))
        file.close()
        # Pra poder checar se o random tá random alguma hora
        self.randtrkName=Dir+"\\"+self.time+"_randtrk_"+Name+".dat"
        file=open(self.randtrkName,'w') 
        file.write("%s\n" % ("mcs RandX RandY RandZ "))
        file.close()
        # Não funcionais  
        self.ellipsetrkName=Dir+"\\"+self.time+"_ellipsetrk_"+Name+".dat"
        file=open(self.ellipsetrkName,'w') 
        file.write("%s\n" % ("PoreID PoreVol MajorAx MinorAx MedianAx PoreX PoreY PoreZ"))
        file.close()  
        self.simparamName=Dir+"\\"+self.time+"_simparam_"+Name+".dat"
        file=open(self.simparamName,'w') 
        file.write("%s\n" % ("Simulation Parameters "))
        self.layerstrkName=Dir+"\\"+self.time+"_layerstrk_"+Name+".dat"
        file=open(self.layerstrkName,'w') 
        file.write("%s\n" % ("mcs L0P L0V L1P L1V L2P L2V L3P L3V"))        
        file.close() 
        print("------------------------------------------------------------------------------------------------")
        print("#### resFolder: ",resFolder)
        print("#### filePath:  ",filePath)
        print("#### screenDir: ",screenDir)
        print("#### SourceDir: ",SourceDir)
        print("#### Dir:       ",Dir)
        print("*************** ",self.routinetrkName)
        print("*************** ",self.creationtrkName)
        print("*************** ",self.htrkName)
        print("*************** ",self.randtrkName)
        print("*************** ",self.ellipsetrkName)
        print("*************** ",self.simparamName)
        print("*************** ",self.layerstrkName)
        print("------------------------------------------------------------------------------------------------")

          
        # Gráficos no player
        self.pW1 = self.add_new_plot_window(title='Number of Cells',
                                                 x_axis_title='MCS',
                                                 y_axis_title='Counts', x_scale_type='linear', y_scale_type='linear',
                                                 grid=True)       
        self.pW1.add_plot("Mat", style='Dots', color='blue', size=5)
        self.pW1.add_plot("Pore", style='Dots', color='green', size=5)
        
        self.pW2 = self.add_new_plot_window(title='Total Volumes',
                                                 x_axis_title='MCS',
                                                 y_axis_title='nmÂ³', x_scale_type='linear', y_scale_type='linear',
                                                 grid=True)       
        self.pW2.add_plot("Mat", style='Dots', color='blue', size=5)
        self.pW2.add_plot("Pore", style='Dots', color='green', size=5)        
        
        self.pW3 = self.add_new_plot_window(title='Height',
                                                 x_axis_title='MCS',
                                                 y_axis_title='h', x_scale_type='linear', y_scale_type='linear',
                                                 grid=True)      
        self.pW3.add_plot("H", style='Lines', color='red', size=5)
                
        

        print ("Lattice Dimensions: ", self.dim.x, self.dim.y, self.dim.z)
        print ("Fluency selected: ", '{:.2e}'.format(p.Fluency)) # good way to write in sci notation
        print ("Number of ions for this lattice: ", p.Number_Ions)
        print ("Total MCS expected: ", p.Total_MCS)
        
    
    def in_circle(self, x, y, radius, center_x, center_y, lattice_x, lattice_y):
        # DOES NOT FIND the true distance, but DO FIND if "in circle" or not
        # correction for circles in periodic borders
        dx = min(abs(center_x-x), center_x+lattice_x-x)
        dy = min(abs(center_y-y), center_y+lattice_y-y)
        distance2 = round(dx**2 + dy**2)
        return distance2 <= (radius**2)
    
    # Hipótese antiga antes do "cilindro dentro do cilindro"
    # Antes checava uma esfera próxima do ponto sorteado
    def in_sphere(self, x, y, z, radius, center_x, center_y, center_z, lattice_x, lattice_y):
        dx = min(abs(center_x-x), center_x+lattice_x-x)
        dy = min(abs(center_y-y), center_y+lattice_y-y)
        dz = abs(center_z-z)
        distance2 = round(dx**2 + dy**2 + dz**2)
        return distance2 <= (radius**2)
    
    # Ia criar algo pra organizar os outputs mas deixei assim mesmo
    def outputs(self):
    
        return
        

    def step(self, mcs):
        import parameters as p
        # updating number of cells and total volumes
        if (mcs % 500 == 0):
            Material_Counter = 0
            Material_Volume = 0
            Pore_Counter = 0
            Pore_Volume = 0
            Material_Density = 0
            
            for cell in self.cell_list:
                if(cell.type == self.MATERIAL):
                    Material_Counter += 1
                    Material_Volume += cell.volume
                if(cell.type == self.PORE):
                    Pore_Counter += 1
                    Pore_Volume += cell.volume                 

            self.pW1.add_data_point("Mat", mcs, Material_Counter)
            self.pW1.add_data_point("Pore", mcs, Pore_Counter)
            self.pW2.add_data_point("Mat", mcs, Material_Volume)
            self.pW2.add_data_point("Pore", mcs, Pore_Volume)
            
            file=open(self.routinetrkName,'a')
            file.write("%d %d %d %.2f %.2f\n" % (mcs,Material_Counter,Pore_Counter,Material_Volume,Pore_Volume))
            file.close() 
                                        
            Material_Density = float(Material_Volume/(Material_Volume+Pore_Volume))
        
        if ((mcs >= p.Relax_Time) and (mcs % p.MCS_Between_Ions == 0)):
            Pore_Z_Distribution = np.zeros(self.dim.z)
            Pore_Z_Cummulative = np.zeros(self.dim.z)
            Material_Z_Distribution = np.zeros(self.dim.z)
            Material_Z_Cummulative = np.zeros(self.dim.z)
            
            Total_Material = 0
            Total_Pore = 0
            
            Height_Now = 0
            
            # Update for each z how many material and pore pixels exist (abandonado)
            # Set the cummulative pore and material quantity until each z (abandonado)
            # Set the sample height base on when there is no more pore and material
            for k in range(self.dim.z):
                for i in range (self.dim.x):
                    for j in range (self.dim.y):
                        cell = self.cell_field[i, j, k]
                        if cell:
                            if cell.type == self.MATERIAL:
                                Material_Z_Distribution[k] += 1
                            if cell.type == self.PORE:
                                Pore_Z_Distribution[k] += 1
                Pore_Z_Cummulative[k] = sum(Pore_Z_Distribution[0:k+1])
                Material_Z_Cummulative[k] = sum(Material_Z_Distribution[0:k+1])
                if Material_Z_Distribution[k] or Pore_Z_Distribution[k]:
                    Height_Now = k
                    
            file=open(self.htrkName,'a')
            file.write("%d %d\n" % (mcs,Height_Now))
            file.close()

            self.pW3.add_data_point("H", mcs, Height_Now)

            # Sum all material pixels and pore pixels (abandonado)
            Total_Material = sum(Material_Z_Distribution)
            Total_Pore = sum(Pore_Z_Distribution)
            
            # Protection against division by zero in first time (abandonado)
            if Total_Pore == 0:
                Total_Pore = 1
            
            # Normalize the Cummulatives (abandonado)
            Material_Z_Cummulative = Material_Z_Cummulative/Total_Material
            Pore_Z_Cummulative = Pore_Z_Cummulative/Total_Pore
                         
               
            # Cooling all cells
            for cell in self.cell_list:
                cell.fluctAmpl = p.Temperature_Cold
                if cell.type == self.PORE: cell.lambdaVolume = p.Pore_LambdaVolume_Cold # need to test better
                if cell.type == self.MATERIAL: cell.lambdaVolume = p.Material_LambdaVolume_Cold
            
            # Chooses XY for ion track 
            Ion_X = random.randint(1, self.dim.x)
            Ion_Y = random.randint(1, self.dim.y)
                            
            # Heating cylinder cells (with border protection)
            for k in range(1, Height_Now):
                for i in range (int(Ion_X-p.Ion_Radius), int(Ion_X+p.Ion_Radius+1)):
                    if i < 1:
                        i += p.Lx
                    if i > p.Lx:
                        i -= p.Lx
                    for j in range (int(Ion_Y-p.Ion_Radius), int(Ion_Y+p.Ion_Radius+1)):
                        if j < 1:
                            j += p.Ly
                        if j > p.Ly:
                            j -= p.Ly
                        # NOW I TEST THE VOXEL
                        if self.in_circle(i, j, p.Ion_Radius, Ion_X, Ion_Y, p.Lx, p.Ly):
                            cell = self.cell_field[i, j, k]
                            if cell:
                                cell.fluctAmpl = p.Temperature_Hot
                                if cell.type == self.MATERIAL:
                                    cell.lambdaVolume = p.Material_LambdaVolume_Hot
                                if cell.type == self.PORE:
                                    cell.lambdaVolume = p.Pore_LambdaVolume_Hot
            
            # All pore creation logic
            Creation_Counter = 0 # abandonado
            for Pore in range(p.Pore_Max_Number):
                # Be sure to find a material cell
                while 1:                        
                    # r and theta needed to set pore x,y,z properly
                    Random_Radius = random.random()*p.Ion_Radius
                    Random_Theta = 2*np.pi*random.random()
                    Random_X = Ion_X+Random_Radius*math.cos(Random_Theta)
                    if Random_X < 1:
                        Random_X += p.Lx
                    if Random_X > p.Lx:
                        Random_X -= p.Lx 
                    Random_Y = Ion_Y+Random_Radius*math.sin(Random_Theta)
                    if Random_Y < 1:
                        Random_Y += p.Ly
                    if Random_Y > p.Ly:
                        Random_Y -= p.Ly                     
                    Random_Z = random.randint(1,Height_Now)
                    # Need to test the cell to decide
                    Current_Cell = self.cell_field[Random_X, Random_Y, Random_Z]
                    if Current_Cell:
                        # Only tries in material
                        if Current_Cell.type == self.MATERIAL:
                            break
                
                # print chosen position
                file=open(self.randtrkName,'a')
                file.write("%d %d %d %d\n" % (mcs,Random_X,Random_Y,Random_Z))
                file.close()  
                
                # TIME TO TEST FOR NEAR PORES
                # aqui inicialmente se pensou em fazer uma divisão ponderada 
                # ou seja: poro próximo maior recebe maior fração de volume que um poro próximo menor
                # aí a contabilização seria de quantos voxels estão próximos e de quais poros são
                # mas houve uma simplificação: divisão igual pra todo mundo
                # CARE THE BORDERS Zmin, X AND Y
                Near_Pore_Cells = {} # NOW ITS A DICTIONARY
                Total_Near_Volume = 0.0
                for k in range(max(1, int(Random_Z-p.Ion_Radius)), int(Random_Z+p.Ion_Radius+1)): #Cylinder_Height/2 = Ion_Radius
                    for i in range (int(Ion_X-p.Ion_Radius), int(Ion_X+p.Ion_Radius+1)):
                        if i < 1:
                            i += p.Lx
                        if i > p.Lx:
                            i -= p.Lx
                        for j in range (int(Ion_Y-p.Ion_Radius), int(Ion_Y+p.Ion_Radius+1)):
                            if j < 1:
                                j += p.Ly
                            if j > p.Ly:
                                j -= p.Ly
                            # NOW I TEST THE VOXEL
                            if self.in_circle(i, j, p.Ion_Radius, Ion_X, Ion_Y, p.Lx, p.Ly):
                                cell = self.cell_field[i, j, k]
                                if cell:
                                    if cell.type == self.PORE:
                                        # IF CELL.ID EXISTS IN THE DICT, RETURNS IT VALOR, ELSE RETURNS ZERO
                                        Near_Pore_Cells[cell.id] = Near_Pore_Cells.get(cell.id, 0) + 1 # MAGIC LINE FROM DICTS
                                        Total_Near_Volume += 1.0 # 1 IF TESTING PARTIAL VOLUME

                                            
                                            
                                            

                # NOW WE CREATE OR INCREMENT TARGET VOLUMES
                
                # INCREMENTING EXISTING PORES
                if len(Near_Pore_Cells)!=0:
                    for index in Near_Pore_Cells:
                        cell = self.fetch_cell_by_id(index)
                        cell.targetVolume += p.Pore_TargetVolume/len(Near_Pore_Cells) #divisão aritmética
                        #cell.targetVolume += p.Pore_TargetVolume * Near_Pore_Cells[index]/Total_Near_Volume #divisão ponderada
          
                # CREATING A NEW ONE        
                else:                        
                    Current_Cell.lambdaVolume = 50.0 # way to save the material cell from disappearing
                    New_Cell = self.new_cell(self.PORE)
                    self.cell_field[Random_X, Random_Y, Random_Z] = New_Cell
                    New_Cell.targetVolume = p.Pore_TargetVolume
                    New_Cell.lambdaVolume = p.Pore_LambdaVolume_Hot
                    Creation_Counter += 1 
                    # print position
                    file=open(self.creationtrkName,'a')
                    file.write("%d %d %d %d %d \n" % (mcs,Creation_Counter,Random_X,Random_Y,Random_Z))
                    file.close()    
                                                          

    def finish(self):
        """
        Called after the last MCS to wrap up the simulation
        """
        for cell in self.cell_list:
            if(cell.type == self.PORE):
                axes = self.momentOfInertiaPlugin.getSemiaxes(cell)       
                file=open(self.ellipsetrkName,'a')
                # tem problema com poros que estão nas bordas (começam de um lado e terminam do outro)
                # por isso foi abandonada essa medição automática
                file.write("%d %d %.2f %.2f %.2f %d %d %d\n" % (cell.id,cell.volume,axes[2],axes[0],axes[1],cell.xCOM,cell.yCOM,cell.zCOM))
                file.close()

    def on_stop(self):
        """
        Called if the simulation is stopped before the last MCS
        """
               


