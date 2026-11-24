def configure_simulation():
    
    import parameters as p
    
    from cc3d.core.XMLUtils import ElementCC3D
    
    CompuCell3DElmnt=ElementCC3D("CompuCell3D",{"Revision":"0","Version":"4.6"})
    
    MetadataElmnt=CompuCell3DElmnt.ElementCC3D("Metadata")
    
    # Basic properties simulation
    MetadataElmnt.ElementCC3D("NumberOfProcessors",{},"1")
    MetadataElmnt.ElementCC3D("DebugOutputFrequency",{},"20")
    # MetadataElmnt.ElementCC3D("NonParallelModule",{"Name":"Potts"})
    
    PottsElmnt=CompuCell3DElmnt.ElementCC3D("Potts")
    
    # Basic properties of CPM (GGH) algorithm
    PottsElmnt.ElementCC3D("Dimensions",{"x":p.Lx,"y":p.Ly,"z":p.Lz})
    PottsElmnt.ElementCC3D("Boundary_x",{},"Periodic")
    PottsElmnt.ElementCC3D("Boundary_y",{},"Periodic")
    PottsElmnt.ElementCC3D("Steps",{},p.Total_MCS)
    PottsElmnt.ElementCC3D("Temperature",{},p.Temperature_Cold)
    PottsElmnt.ElementCC3D("NeighborOrder",{},"1")
    PottsElmnt.ElementCC3D("RandomSeed",{},"12345") #adição de seed fixa para reprodutibilidade
    
    
    PluginElmnt=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"CellType"})
    
    # Listing all cell types in the simulation
    PluginElmnt.ElementCC3D("CellType",{"TypeId":"0","TypeName":"Medium"})
    PluginElmnt.ElementCC3D("CellType",{"TypeId":"1","TypeName":"MATERIAL"})
    PluginElmnt.ElementCC3D("CellType",{"TypeId":"2","TypeName":"PORE"})
    
    CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"Volume"})
    
    PluginElmnt_1=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"CenterOfMass"})
    
    # Module tracking center of mass of each cell
    
    PluginElmnt_2=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"NeighborTracker"})
    
    # Module tracking neighboring cells of each cell
    
    PluginElmnt_3=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"PixelTracker"})
    
    # Module tracking pixels of each cell
    
    PluginElmnt_4=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"BoundaryPixelTracker"})
    
    # Module tracking boundary pixels of each cell
    PluginElmnt_4.ElementCC3D("NeighborOrder",{},"1")
    
    PluginElmnt_5=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"Contact"})
    # Specification of adhesion energies
    PluginElmnt_5.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Medium"},p.J_Medium_Medium)
    PluginElmnt_5.ElementCC3D("Energy",{"Type1":"Medium","Type2":"MATERIAL"},p.J_Medium_Material)
    PluginElmnt_5.ElementCC3D("Energy",{"Type1":"Medium","Type2":"PORE"},p.J_Medium_Pore)
    PluginElmnt_5.ElementCC3D("Energy",{"Type1":"MATERIAL","Type2":"MATERIAL"},p.J_Material_Material)
    PluginElmnt_5.ElementCC3D("Energy",{"Type1":"MATERIAL","Type2":"PORE"},p.J_Material_Pore)
    PluginElmnt_5.ElementCC3D("Energy",{"Type1":"PORE","Type2":"PORE"},p.J_Pore_Pore)
    PluginElmnt_5.ElementCC3D("NeighborOrder",{},p.NgbOrder)
    
    PluginElmnt_6=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"MomentOfInertia"})

    PluginElmnt_7=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"SurfaceTracker"})

    
    SteppableElmnt=CompuCell3DElmnt.ElementCC3D("Steppable",{"Type":"UniformInitializer"})
    
    # Initial layout of cells in the form of rectangular slab
    RegionElmnt=SteppableElmnt.ElementCC3D("Region")
    RegionElmnt.ElementCC3D("BoxMin",{"x":"0","y":"0","z":"0"})
    RegionElmnt.ElementCC3D("BoxMax",{"x":p.Lx,"y":p.Ly,"z":p.Initial_Sample_Height})
    RegionElmnt.ElementCC3D("Gap",{},"0")
    RegionElmnt.ElementCC3D("Width",{},p.Block_EdgeSize)
    RegionElmnt.ElementCC3D("Types",{},"MATERIAL")


        
    CompuCellSetup.setSimulationXMLDescription(CompuCell3DElmnt)

# CompuCell uses this to configure what runs and in what frequency
from cc3d import CompuCellSetup
        
configure_simulation()

from SemiconductorFoamSteppables import Nucleation
CompuCellSetup.register_steppable(steppable=Nucleation(frequency=1))
     
from SemiconductorFoamSteppables import FilmSetup
CompuCellSetup.register_steppable(steppable=FilmSetup(frequency=1))

# O benchmark curto para automaticamente após BENCHMARK_MCS. Para executar a
# simulação completa, altere BENCHMARK_MODE para False em parameters.py.
import parameters as p
if p.BENCHMARK_MODE:
    from SemiconductorFoamSteppables import ShortRunBenchmarkSteppable
    CompuCellSetup.register_steppable(
        steppable=ShortRunBenchmarkSteppable(frequency=1)
    )

CompuCellSetup.run()