"""Run once with UnrealEditor-Cmd -run=pythonscript. Creates a separate quest map."""
import unreal as u
import pathlib, json

ROOT='/Game/Midterm'
MAP=ROOT+'/Maps/Lvl_SignalVault'
if (pathlib.Path(u.Paths.project_dir())/'Docs/build_complete.json').exists():
    raise RuntimeError('Map already exists; refusing to overwrite hand edits.')
if u.EditorAssetLibrary.does_asset_exist(MAP):
    u.EditorLoadingAndSavingUtils.load_map(MAP)
    existing=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    if any(a.get_actor_label() == 'QuestStart' for a in existing):
        raise RuntimeError('Quest already populated; refusing to duplicate or replace it.')
else:
    u.get_editor_subsystem(u.LevelEditorSubsystem).new_level(MAP)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
assets=u.AssetToolsHelpers.get_asset_tools()
cube=u.load_asset('/Engine/BasicShapes/Cube')
def mat(name,color,glow=0):
    if u.EditorAssetLibrary.does_asset_exist(ROOT+'/Materials/'+name):
        return u.load_asset(ROOT+'/Materials/'+name)
    m=u.load_asset(ROOT+'/Materials/'+name) if u.EditorAssetLibrary.does_asset_exist(ROOT+'/Materials/'+name) else assets.create_asset(name,ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
    c=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector)
    c.set_editor_property('constant',u.LinearColor(*color))
    u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
    if glow: u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    u.MaterialEditingLibrary.recompile_material(m)
    u.EditorAssetLibrary.save_loaded_asset(m)
    return m
floor=mat('M_Slate',(0.035,0.065,0.09))
wall=mat('M_Steel',(0.08,0.13,0.18))
cyan=mat('M_Cyan',(0.02,0.8,1.0),1)
gold=mat('M_Amber',(1.0,0.42,0.04),1)
red=mat('M_Danger',(0.8,0.035,0.025),1)
white=mat('M_White',(0.7,0.85,0.9))
def spawn(cls,label,pos,rot=(0,0,0)):
    a=actors.spawn_actor_from_class(cls,u.Vector(*pos),u.Rotator(*rot))
    a.set_actor_label(label)
    return a
def block(label,pos,size,material=wall):
    a=spawn(u.StaticMeshActor,label,pos)
    c=a.static_mesh_component
    c.set_static_mesh(cube)
    c.set_material(0,material)
    a.set_actor_scale3d(u.Vector(*(v/100 for v in size)))
    return a
def text(label,words,pos,size=30,color=(120,225,255),yaw=180):
    a=spawn(u.TextRenderActor,label,pos,(0,yaw,0))
    c=a.text_render
    c.set_text(words)
    c.set_world_size(size)
    c.set_text_render_color(u.Color(*color,255))
    c.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
    return a
def bp(name,label,pos,yaw=0):
    return spawn(u.load_class(None,'/Game/ThirdPerson/Blueprints/'+name+'.'+name+'_C'),label,pos,(0,yaw,0))
def prop(a,name,value): a.set_editor_property(name,value)
def component(a,name): return a.get_editor_property(name)
def box(c,loc,extent):
    c.set_editor_property('relative_location',u.Vector(*loc))
    c.set_editor_property('relative_scale3d',u.Vector(1,1,1))
    c.set_box_extent(u.Vector(*extent))
def mesh(c,loc,size,material):
    c.set_static_mesh(cube)
    c.set_editor_property('relative_location',u.Vector(*loc))
    c.set_editor_property('relative_scale3d',u.Vector(*(v/100 for v in size)))
    c.set_material(0,material)
def light(x,y,z=800):
    a=spawn(u.PointLight,'Light',(x,y,z))
    a.point_light_component.set_intensity(20000)
    a.point_light_component.set_attenuation_radius(1250)
    a.point_light_component.set_light_color(u.LinearColor(0.35,0.7,1.0))
def deck(start,end):
    block('Deck',((start+end)/2,0,475),(end-start,1000,50),floor)
    for y in [-510,510]:
        block('Hull',((start+end)/2,y,770),(end-start,40,540))
        block('RouteLight',((start+end)/2,y-25*(1 if y>0 else -1),540),(end-start,8,8),cyan)
def checkpoint(label,x):
    a=bp('BP_CheckPoint',label,(x,0,600))
    box(component(a,'CollisionBox'),(0,0,-20),(70,460,120))
    block(label+'_Marker',(x,0,503),(25,900,5),cyan)
    return a
def death(label,pos,extent):
    a=bp('BP_DeathTrigger',label,pos)
    box(component(a,'DeathBox'),(0,0,0),extent)
    return a
def door(label,x,material=wall):
    a=bp('BP_Door',label,(x,0,500),90)
    mesh(component(a,'DoorMesh'),(0,0,220),(930,45,440),material)
    box(component(a,'ProximityTrigger'),(0,0,120),(470,200,150))
    prop(a,'DoorOpenOffset',u.Vector(0,0,500))
    prop(a,'bIsOpenable',False)
    return a
def plate(label,x,y,target=None):
    if target:
        a=bp('BP_Button',label,(x,y,520))
        mesh(component(a,'Cube'),(0,0,0),(130,130,20),gold)
        box(component(a,'Trigger'),(0,0,60),(65,65,80))
        prop(a,'TargetDoor',target)
    else:
        a=death(label,(x,y,580),(65,65,75))
        block(label+'_Plate',(x,y,520),(130,130,20),gold)
    return a

for start,end in [(0,6200),(7500,8200),(8850,11000)]: deck(start,end)
block('EntryWall',(0,0,770),(40,1000,540))
block('VaultBack',(11000,0,770),(40,1000,540))
for x in range(500,11000,700): light(x,0)
sun=spawn(u.DirectionalLight,'Sun',(0,0,1600),(-55,-35,0))
sun.light_component.set_intensity(2.0)
spawn(u.SkyLight,'Sky',(0,0,1500))
spawn(u.SkyAtmosphere,'Atmosphere',(0,0,0))
start=spawn(u.PlayerStart,'QuestStart',(250,0,600))
checkpoint('CP_Entry',400)
death('FallRecovery',(5500,0,150),(6000,1800,160))
text('Briefing','SIGNAL VAULT\nRestore power. Decode the seals. Find the archive.\nWASD move | Mouse look | Space jump | Shift sprint',(750,0,850),28)
text('PowerHint','01 / RESTORE POWER\nApproach the amber console',(1250,0,930),38)
barrier=bp('BP_HazardBarrier','PowerBarrier',(1900,0,500))
prop(barrier,'bKillOnTouch',False)
mesh(component(barrier,'BeamMesh'),(0,0,190),(50,930,380),red)
box(component(barrier,'DamageTrigger'),(0,0,190),(30,465,190))
for name,y in [('FrameLeft',-470),('FrameRight',470)]:
    mesh(component(barrier,name),(0,y,220),(80,50,440),wall)
# The source beam may use overlap collision; explicitly block until deactivated.
component(barrier,'BeamMesh').set_collision_profile_name('BlockAllDynamic')
gen=bp('BP_PowerGenerator','MainGenerator',(1500,330,500))
prop(gen,'LinkedBarrier',barrier)
# Use the generator's configured 1.5-second activation delay.
switch=bp('BP_ConsoleSwitch','PowerConsole',(1000,-300,500))
prop(switch,'LinkedGenerator',gen)
text('ConsoleLabel','POWER',(1000,-300,660),26)
for x in range(1050,1850,100): block('PowerCable',(x,-300,510),(65,14,10),gold)

checkpoint('CP_Puzzle',2200)
text('PuzzleClue','02 / THE THREE SEALS\nI : SUN    II : WAVE    III : STAR\nStep on the matching symbol in each chamber.\nA wrong seal returns you to the checkpoint.',(2600,0,890),28)
sequences=[(3100,3400,['STAR','SUN','WAVE'],'SUN'),(4300,4700,['WAVE','STAR','SUN'],'WAVE'),(5600,6000,['SUN','WAVE','STAR'],'STAR')]
for idx,(px,dx,symbols,correct) in enumerate(sequences,1):
    gate=door('SealDoor_'+str(idx),dx)
    for y,symbol in zip([-280,0,280],symbols):
        plate('Seal_'+str(idx)+'_'+symbol,px,y,gate if symbol==correct else None)
        text('Symbol_'+str(idx)+'_'+symbol,symbol,(px,y,675),28)
    text('SealNumber_'+str(idx),'SEAL '+str(idx),(dx-80,0,970),35)
    if idx<3: checkpoint('CP_Seal_'+str(idx),dx+200)

checkpoint('CP_Transport',6090)
text('LiftHint','03 / CROSS THE SHAFT\nBoard the shuttle. Stay on the platform.',(6200,0,940),29)
lift=bp('BP_MovingPlatform','Shuttle',(6330,0,500))
prop(lift,'TargetOffset',u.Vector(1020,0,0))
prop(lift,'MoveSpeed',0.22)
mesh(component(lift,'PlatformMesh'),(0,0,0),(300,500,35),gold)
box(component(lift,'TriggerBox'),(0,0,90),(155,240,120))
for y in [-510,510]: block('ShaftWall',(6850,y,770),(1400,40,540))
checkpoint('CP_Sprint',7650)
text('SprintHint','04 / SPRINT JUMP\nHold SHIFT, run to the edge, then SPACE.\nThe gap is too wide at walking speed.',(8000,0,940),28)
for x in range(7750,8150,100): block('Runway',(x,0,503),(55,100,6),gold)
for y in [-510,510]: block('GapWall',(8525,y,770),(650,40,540))
checkpoint('CP_Vault',9000)
text('VaultHint','05 / THE HIDDEN ARCHIVE\nThe amber floor seal releases the hidden wall.',(9450,0,950),28)
vault=door('SecretWall',9900,wall)
plate('ArchiveSeal',9500,320,vault)
block('ArchiveCeiling',(10450,0,1040),(1100,1000,40))
block('ArchivePlinth',(10600,0,570),(240,240,140),wall)
core=block('ArchiveCore',(10600,0,740),(80,80,80),cyan)
core.set_actor_rotation(u.Rotator(20,45,20),False)
text('Ending','ARCHIVE FOUND\nQUEST COMPLETE',(10850,0,900),48,(120,255,190))
text('EndingDetail','Power restored. Three seals decoded.\nThe lost signal is safe.',(10850,0,800),25)

gm=u.EditorAssetLibrary.duplicate_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode',ROOT+'/Blueprints/BP_VaultGameMode')
u.BlueprintEditorLibrary.compile_blueprint(gm)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class())
u.EditorAssetLibrary.save_loaded_asset(gm)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
u.log_warning('MIDTERM_BUILD_COMPLETE '+str(len(actors.get_all_level_actors()))+' actors')

