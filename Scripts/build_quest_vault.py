"""Build a self-contained quest map from Task0's existing Blueprint mechanics.

Run inside Unreal Editor Python. Generated content is isolated in /Game/QuestVault.
The five legacy Blueprint casts must first be migrated to BP_Megan.
"""
import unreal
import json
from pathlib import Path

ROOT = '/Game/QuestVault'
MAP = ROOT + '/Maps/L_QuestVault'
LOG = Path(unreal.Paths.project_saved_dir()) / 'QuestBuild'
LOG.mkdir(parents=True, exist_ok=True)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assets = unreal.AssetToolsHelpers.get_asset_tools()
warnings = []
manifest = {}

def vec(x=0, y=0, z=0):
    return unreal.Vector(float(x), float(y), float(z))

def optional(obj, key, value):
    try:
        obj.set_editor_property(key, value)
    except Exception as exc:
        warnings.append(str(key) + ': ' + str(exc))

def material(name, rgb, glow=False):
    path = ROOT + '/Materials/' + name
    existing = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if existing:
        return existing
    mat = assets.create_asset(name, ROOT + '/Materials', unreal.Material, unreal.MaterialFactoryNew())
    color = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant', unreal.LinearColor(*rgb, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.set_editor_property('r', 0.65)
    unreal.MaterialEditingLibrary.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    if glow:
        unreal.MaterialEditingLibrary.connect_material_property(color, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

unreal.EditorAssetLibrary.make_directory(ROOT + '/Maps')
unreal.EditorAssetLibrary.make_directory(ROOT + '/Materials')
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    assert (LOG / 'generated-map.txt').exists(), 'Refusing to replace a map not created by this script'
    assert levels.load_level(MAP)
    for old in actors.get_all_level_actors():
        if not old.get_actor_label().startswith('QV_') and old.get_class().get_name() != 'WorldSettings':
            raise RuntimeError('Unexpected actor in generated map: ' + old.get_actor_label())
    for old in list(actors.get_all_level_actors()):
        if old.get_actor_label().startswith('QV_'):
            actors.destroy_actor(old)
else:
    assert levels.new_level(MAP, is_partitioned_world=False)
    (LOG / 'generated-map.txt').write_text(MAP)

cube_mesh = unreal.load_asset('/Engine/BasicShapes/Cube')
cylinder_mesh = unreal.load_asset('/Engine/BasicShapes/Cylinder')
grid = unreal.load_asset('/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray_02')
mats = {
    'wall': material('M_Vault_Wall', (0.065, 0.10, 0.15)),
    'floor': material('M_Vault_Floor', (0.23, 0.29, 0.34)),
    'edge': material('M_Vault_Trim', (0.40, 0.50, 0.56)),
    'cyan': material('M_Vault_Cyan', (0.025, 0.80, 1.0), True),
    'amber': material('M_Vault_Amber', (1.0, 0.40, 0.025), True),
    'red': material('M_Vault_Danger', (1.0, 0.035, 0.025), True),
    'green': material('M_Vault_Green', (0.08, 1.0, 0.40), True),
    'gold': material('M_Vault_Gold', (0.95, 0.56, 0.10)),
}

def spawn(cls, name, position, yaw=0, folder='Geometry'):
    obj = actors.spawn_actor_from_class(cls, vec(*position), unreal.Rotator(pitch=0, yaw=yaw, roll=0))
    assert obj, name
    obj.set_actor_label('QV_' + name)
    obj.set_folder_path('QuestVault/' + folder)
    manifest[name] = obj.get_name()
    return obj

def block(name, pos, size, mat='wall', folder='Geometry', collision=True):
    obj = spawn(unreal.StaticMeshActor, name, pos, folder=folder)
    comp = obj.static_mesh_component
    comp.set_static_mesh(cube_mesh)
    comp.set_material(0, mats.get(mat, mat) if isinstance(mat, str) else mat)
    obj.set_actor_scale3d(vec(*(s / 100 for s in size)))
    comp.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    return obj

def floor(name, x0, x1, z, width=1200, y=0):
    return block(name, ((x0+x1)/2,y,z-30), (x1-x0,width,60), 'floor')

def text(name, message, pos, size=28, color=(210,240,255), yaw=180):
    obj = spawn(unreal.TextRenderActor, name, pos, yaw, 'Signs')
    comp = obj.get_component_by_class(unreal.TextRenderComponent)
    comp.set_text(message)
    comp.set_world_size(size)
    comp.set_text_render_color(unreal.Color(*color,255))
    comp.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    comp.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return obj

def board(name, message, x, y, z, width=750, height=160, size=28):
    block(name+'_Board', (x,y,z), (12,width,height), 'wall', 'Signs', False)
    text(name+'_Text', message, (x+8 if name=='Controls' else x-8,y,z), size, yaw=0 if name=='Controls' else 180)

def portal(name, x, z, width=340, tint='cyan'):
    gap = width/2
    block(name+'_Left', (x,-(600+gap)/2,z+200), (60,600-gap,400))
    block(name+'_Right', (x,(600+gap)/2,z+200), (60,600-gap,400))
    block(name+'_Header', (x,0,z+375), (60,width,50))
    for y in (-gap,gap):
        block(name+'_Light_'+str(y), (x-33,y,z+175), (8,9,350), tint, collision=False)

def light(name, pos, color=(0.3,0.75,1.0), intensity=450, radius=650):
    obj = spawn(unreal.PointLight, name, pos, folder='Lighting')
    comp = obj.get_component_by_class(unreal.PointLightComponent)
    comp.set_light_color(unreal.LinearColor(*color,1))
    comp.set_intensity(intensity)
    comp.set_attenuation_radius(radius)
    optional(comp,'cast_shadows',False)
    return obj

def blueprint(name, asset_name, pos, yaw=0):
    cls = unreal.EditorAssetLibrary.load_blueprint_class('/Game/ThirdPerson/Blueprints/'+asset_name)
    assert cls, asset_name
    return spawn(cls,name,pos,yaw,'Mechanics')

def component(actor,name):
    for c in actor.get_components_by_class(unreal.SceneComponent):
        if c.get_name()==name:
            return c
    raise RuntimeError(actor.get_actor_label()+' missing component '+name)

def configure_box(c, location, extent):
    c.set_world_scale3d(vec(1,1,1))
    c.set_world_location(vec(*location),False,False)
    c.set_box_extent(vec(*extent),True)
    c.set_collision_profile_name('Trigger')
    c.set_editor_property('generate_overlap_events',True)

def door(name,x,z):
    obj=blueprint(name,'BP_Door',(x,0,z))
    mesh=component(obj,'DoorMesh')
    mesh.set_static_mesh(cube_mesh)
    mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
    mesh.set_relative_location(vec(0,0,155),False,False)
    mesh.set_relative_scale3d(vec(.25,3.2,3.1))
    mesh.set_material(0,mats['edge'])
    mesh.set_collision_profile_name('BlockAll')
    obj.set_editor_property('bIsOpenable',False)
    obj.set_editor_property('DoorOpenOffset',vec(0,350,0))
    configure_box(component(obj,'ProximityTrigger'),(x,0,z+110),(240,240,130))
    component(obj,'PointLight').set_relative_location(vec(-70,0,335),False,False)
    portal(name+'_Frame',x,z)
    return obj

def button(name,x,y,z,number=1,puzzle=None,target=None):
    obj=blueprint(name,'BP_Button',(x,y,z+12))
    mesh=component(obj,'Cube')
    mesh.set_material(0,mats['amber' if puzzle else 'cyan'])
    configure_box(component(obj,'Trigger'),(x,y,z+100),(85,85,105))
    obj.set_editor_property('IsPuzzleButton',puzzle is not None)
    obj.set_editor_property('ButtonNumber',number)
    obj.set_editor_property('PuzzleController',puzzle)
    obj.set_editor_property('TargetDoor',target)
    block(name+'_Base',(x,y,z-4),(160,160,20),'wall','Mechanics')
    text(name+'_Prompt',str(number) if puzzle else 'E - UNLOCK',(x+80,y,z+155),40 if puzzle else 22)
    return obj

def checkpoint(name,x,z,width=1000):
    obj=blueprint(name,'BP_CheckPoint',(x,0,z+100))
    c=obj.get_component_by_class(unreal.BoxComponent)
    configure_box(c,(x,0,z+100),(65,width/2,130))
    block(name+'_Stripe',(x,0,z+2),(70,width,4),'green','Guidance',False)
    text(name+'_Sign','CHECKPOINT',(x+130,-430,z+180),20,(95,255,165))
    return obj

def death(name,x0,x1,z,y=0,width=1200):
    obj=blueprint(name,'BP_DeathTrigger',((x0+x1)/2,y,z))
    c=obj.get_component_by_class(unreal.BoxComponent)
    configure_box(c,((x0+x1)/2,y,z),((x1-x0)/2,width/2,100))
    return obj

def platform(name,pos,offset,size=(400,400,40),speed=.4):
    obj=blueprint(name,'BP_MovingPlatform',pos)
    obj.set_editor_property('TargetOffset',vec(*offset))
    obj.set_editor_property('MoveSpeed',speed)
    mesh=component(obj,'PlatformMesh')
    mesh.set_static_mesh(cube_mesh)
    mesh.set_material(0,mats['amber'])
    mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
    mesh.set_relative_location(vec(0,0,0),False,False)
    mesh.set_relative_scale3d(vec(*(s/100 for s in size)))
    mesh.set_collision_profile_name('BlockAllDynamic')
    configure_box(component(obj,'TriggerBox'),(pos[0],pos[1],pos[2]+size[2]/2+95),(max(65,size[0]/2-160),max(65,size[1]/2-60),110))
    return obj

# Lighting and the existing character / input setup.
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',unreal.EditorAssetLibrary.load_blueprint_class('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode'))
sun=spawn(unreal.DirectionalLight,'Sun',(0,0,4000),folder='Lighting')
sun.set_actor_rotation(unreal.Rotator(pitch=-48,yaw=-35,roll=0),False)
sun.light_component.set_intensity(4.0)
optional(sun.light_component,'atmosphere_sun_light',True)
post=spawn(unreal.PostProcessVolume,'Exposure',(0,0,0),folder='Lighting')
post.set_editor_property('unbound',True)
settings=post.get_editor_property('settings')
settings.set_editor_property('override_auto_exposure_bias',True)
settings.set_editor_property('auto_exposure_bias',-1.5)
settings.set_editor_property('override_bloom_intensity',True)
settings.set_editor_property('bloom_intensity',0.2)
post.set_editor_property('settings',settings)
spawn(unreal.SkyAtmosphere,'Sky',(0,0,0),folder='Lighting')
sky=spawn(unreal.SkyLight,'SkyLight',(0,0,2000),folder='Lighting')
sky.light_component.set_intensity(0.7)
optional(sky.light_component,'real_time_capture',True)
fog=spawn(unreal.ExponentialHeightFog,'Fog',(0,0,-100),folder='Lighting')
optional(fog.get_component_by_class(unreal.ExponentialHeightFogComponent),'fog_density',0.008)
start=spawn(unreal.PlayerStart,'PlayerStart',(-250,0,100),folder='Gameplay')

# Geometry: one continuous industrial complex, with mandatory mechanical routes.
floor('StartFloor',-650,1100,0)
floor('LiftSump',1100,1500,-260,width=420)
floor('UpperApproach',1500,3000,450)
floor('ParkourSump',3000,5200,-170)
floor('PowerRoom',5200,7200,450)
floor('TransitSump',7200,9500,-170)
floor('PuzzleRoom',9400,12600,450)
floor('VaultFloor',12600,14100,450)
floor('HintAlcove',9800,10700,450,width=6200,y=3700)

for name,x0,x1,z in [('Start',-650,1100,0),('Lift',1100,1500,0),('Approach',1500,3000,450),('Parkour',3000,5200,450),('Power',5200,7200,450),('Transit',7200,9500,450),('Puzzle',9500,12600,450),('Vault',12600,14100,450)]:
    for side in (-1,1):
        # Alcove opening is left clear on the north side of the puzzle room.
        if name=='Puzzle' and side==1:
            for a,b in [(9500,9800),(10700,12600)]:
                block(name+'_Wall_'+str(a),((a+b)/2,side*640,z+200),(b-a,80,400))
        else:
            block(name+'_Wall_'+str(side),((x0+x1)/2,side*640,z+200),(x1-x0,80,400))
        block(name+'_BaseTrim_'+str(side),((x0+x1)/2,side*597,z+16),(x1-x0,10,32),'edge',collision=False)
    for x in range(int(x0+250),int(x1),900):
        light(name+'_Light_'+str(x),(x,-440,z+310))
        block(name+'_Lamp_'+str(x),(x,-595,z+280),(160,12,8),'cyan','Lighting',False)

block('BackWall',(-690,0,200),(80,1360,400))
block('EndWall',(14140,0,775),(80,1360,650))
block('AlcoveBack',(10250,6840,650),(980,80,400))
for x in (9760,10740):
    block('AlcoveSide_'+str(x),(x,3700,650),(80,6200,400))
portal('UpperEntry',1900,450,600)
portal('PowerEntry',5250,450,600)
portal('TransitEntry',6800,450,340,'amber')
portal('PuzzleEntry',9600,450,600)

# Stage 1: use E to unlock the first security door.
first=door('EntryDoor',750,0)
button('EntryButton',220,-360,0,target=first)
board('Welcome','VAULT 07\nRESTORE POWER. FIND THE CODE. OPEN THE VAULT.',610,0,460,1100,150,29)
board('Controls','WASD - MOVE    SHIFT - RUN\nSPACE - JUMP    E - USE    RMB - AIM',-540,0,235,1000,170,25)
board('Stage1','01 / ACCESS CONTROL\nUSE THE CYAN PANEL ON YOUR LEFT',500,0,240,950,130,26)
checkpoint('StartCheckpoint',-150,0)

# Stage 2: automatic lift; the raised landing cannot be reached on foot.
lift=platform('Lift',(1300,0,-20),(0,0,450),(400,400,40),.35)
for y in (-265,265):
    block('LiftRail_'+str(y),(1300,y,225),(500,35,600),'edge')
board('LiftGuide','02 / SERVICE LIFT\nSTEP ON. RIDE UP. EXIT FORWARD.',1030,0,550,950,150,27)
checkpoint('UpperCheckpoint',2700,450)

# Stage 3: jump between pads. Falling returns to the preceding checkpoint.
for i,(x,y) in enumerate([(3175,-180),(3625,180),(4075,-180),(4525,180),(4975,-80)],1):
    block('JumpPad_'+str(i),(x,y,410),(300,300,80),'edge','Parkour')
    block('JumpPadGlow_'+str(i),(x,y,452),(270,270,4),'cyan','Parkour',False)
    text('JumpPadNumber_'+str(i),str(i),(x+125,y,510),25)
death('ParkourReset',3000,5200,150)
for x in range(3050,5200,180):
    block('PitWarning_'+str(x),(x,-545,452),(80,55,4),'red','Guidance',False)
board('JumpGuide','03 / BROKEN WALKWAY\nSHIFT + SPACE TO JUMP. FALLING RETURNS TO CHECKPOINT.',2870,0,790,1100,150,25)

# Stage 4: a pressure console restores the generator and disables a blocking field.
barrier=blueprint('PowerBarrier','BP_HazardBarrier',(6800,0,450))
beam=component(barrier,'BeamMesh')
beam.set_static_mesh(cube_mesh)
beam.set_relative_location(vec(0,0,155),False,False)
beam.set_relative_scale3d(vec(.25,3.25,3.1))
beam.set_material(0,mats['red'])
beam.set_collision_profile_name('NoCollision')
damage=component(barrier,'DamageTrigger')
configure_box(damage,(6800,0,605),(25,165,155))
damage.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
damage.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN,unreal.CollisionResponseType.ECR_BLOCK)
damage.set_editor_property('generate_overlap_events',False)
barrier.set_editor_property('bIsActive',True)
gen=blueprint('Generator','BP_PowerGenerator',(6100,430,450))
gen.set_editor_property('LinkedBarrier',barrier)
assert gen.get_editor_property('ActivationDelay') >= 0
assert not gen.get_editor_property('bIsPowered')
console=blueprint('PressureConsole','BP_ConsoleSwitch',(5950,-360,450))
console.set_editor_property('LinkedGenerator',gen)
configure_box(component(console,'InteractionTrigger'),(5950,-360,550),(120,120,120))
block('PressurePanel',(5950,-360,453),(240,240,6),'amber','Mechanics',False)
board('PowerGuide','04 / AUXILIARY POWER\nSTEP ON THE AMBER PANEL. WAIT FOR THE FIELD TO SHUT DOWN.',5480,0,790,1100,160,25)
text('GeneratorLabel','GENERATOR',(6140,430,740),26,(255,185,75))
text('ConsoleLabel','STEP HERE',(5950,-360,680),27,(255,185,75))
checkpoint('TransitCheckpoint',7000,450)

# Stage 5: mandatory horizontal ferry over a second return volume.
ferry=platform('Ferry',(7400,0,430),(1800,0,0),(600,450,40),.20)
death('TransitReset',7200,9500,150)
board('FerryGuide','05 / TRANSIT PLATFORM\nBOARD THE AMBER PLATFORM. STEP OFF AT THE FAR END.',7060,0,850,1100,150,25)
for x in (7200,9500):
    for y in (-520,520):
        block('DockBeacon_'+str(x)+'_'+str(y),(x,y,530),(45,45,160),'amber','Guidance',False)

# Stage 6: search the side alcove, then enter the sequence at three separated pads.
final=door('VaultDoor',12600,450)
puzzle=blueprint('SequencePuzzle','BP_SequencePuzzle',(11400,0,450))
assert list(puzzle.get_editor_property('CorrectOrder')) == [2,1,3]
assert puzzle.get_editor_property('CurrentStep') == 0
assert not puzzle.get_editor_property('IsSolved')
puzzle.set_editor_property('FinalDoor',final)
for number,y in [(1,-400),(2,0),(3,400)]:
    button('CodeButton'+str(number),11750,y,450,number,puzzle)
    block('CodeStation'+str(number),(11900,y,530),(50,230,160),'wall','Mechanics')
board('PuzzleGuide','06 / VAULT AUTHORIZATION\nFIND THE MAINTENANCE NOTE. ENTER ITS THREE NUMBERS USING E.',11100,0,820,1100,160,25)
board('HintNote','FILE 07 / ACCESS ORDER\nSECOND - FIRST - THIRD\n2  >  1  >  3',10650,6500,665,600,230,28)
text('HintEntrance','MAINTENANCE',(10100,610,740),23,(255,185,75),-90)
light('AlcoveLamp',(10200,6500,780),(1.0,.45,.08),650,800)
checkpoint('PuzzleCheckpoint',9800,450)

# The archive adds a real exploration detour, with alternating storage shelves.
for i,(x,y) in enumerate([(10020,1800),(10480,3300),(10020,4800)],1):
    block('ArchiveShelf_'+str(i),(x,y,610),(440,110,320),'wall','Archive')
    for z in (510,610,710):
        block('ArchiveShelfBand_'+str(i)+'_'+str(z),(x,y-59,z),(400,8,12),'amber','Archive',False)
    text('ArchiveSection_'+str(i),'ARCHIVE '+str(i),(10250,y-150,800),25,(255,195,90),-90)
for y in range(1000,6700,900):
    light('ArchiveLamp_'+str(y),(10250,y,790),(1.0,.6,.25),450,950)
    block('ArchiveMarker_'+str(y),(10250,y,452),(30,100,4),'amber','Guidance',False)
text('ArchiveEnd','FILE 07 / AUTHORIZATION',(10250,6750,800),25,(255,195,90),-90)

# Stage 7: a clearly visible finish behind the locked vault door.
block('VaultPlinth',(13600,0,510),(350,350,120),'wall','Finish')
relic=spawn(unreal.StaticMeshActor,'VaultCore',(13600,0,650),folder='Finish')
relic.static_mesh_component.set_static_mesh(cylinder_mesh)
relic.static_mesh_component.set_material(0,mats['gold'])
relic.set_actor_scale3d(vec(1.7,1.7,1.6))
block('CoreGlow',(13600,0,745),(100,100,12),'green','Finish',False)
board('Finish','VAULT 07 SECURED\nQUEST COMPLETE',13970,0,930,1000,250,48)
text('FinishSub','POWER RESTORED / CODE ACCEPTED',(13800,0,790),24,(100,255,180))
light('VaultGoldLight',(13500,0,850),(1,.65,.15),4000,1000)

# Periodic floor markings and structural supports make the route readable.
for x0,x1,z in [(-400,600,0),(1600,2600,450),(5350,6550,450),(9700,12300,450),(12800,13800,450)]:
    for x in range(x0,x1,350):
        block('Route_'+str(x),(x,0,z+2),(110,18,4),'cyan','Guidance',False)
for x in (1750,5500,6500,9900,10900,12200,13100,13900):
    for y in (-550,550):
        block('Support_'+str(x)+'_'+str(y),(x,y,625),(65,65,350),'edge','Architecture')

assert levels.save_current_level(), 'Could not save quest level'
unreal.EditorAssetLibrary.save_directory(ROOT,only_if_is_dirty=True,recursive=True)
report={'map':MAP,'actor_count':len(actors.get_all_level_actors()),'actors':manifest,'warnings':warnings,'notes':['Existing Blueprint mechanics reused.','Power field blocks Pawn instead of firing the legacy level-reload overlap.','No additional character ability; designed around the reduced midterm scope.']}
(LOG/'build-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.log('QUEST_BUILD_COMPLETE '+MAP+' actors='+str(report['actor_count']))
