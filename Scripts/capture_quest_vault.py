"""Render reference images of the finished level without saving camera actors."""
import unreal,time,json,traceback
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level('/Game/QuestVault/Maps/L_QuestVault')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
folder=Path(unreal.Paths.project_dir())/'Docs/QuestVault'
folder.mkdir(parents=True,exist_ok=True)
cam=sub.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(0,0,1000))
cam.camera_component.set_field_of_view(80)
optional=[('Overview',(6500,-9000,11000),(6500,1800,300)),('Entrance',(-470,-260,240),(650,0,250)),('Parkour',(2500,-1400,1800),(4150,0,450)),('Puzzle',(10800,-1600,1800),(11900,0,600)),('Finish',(12950,-300,850),(13900,0,850)),('Archive',(9650,5700,1350),(10500,6500,650))]
state={'index':0,'last':time.monotonic(),'started':time.monotonic(),'requested':False,'errors':[]}
def tick(dt):
    try:
        now=time.monotonic()
        if now-state['started']>150:raise RuntimeError('Screenshot capture timed out')
        if state['index']>=len(optional):
            (folder/'capture.json').write_text(json.dumps(state,indent=2))
            unreal.unregister_slate_post_tick_callback(handle)
            unreal.EditorPythonScripting.set_keep_python_script_alive(False)
            return
        if now-state['last']<7:return
        name,pos,target=optional[state['index']]
        if not state['requested']:
            loc=unreal.Vector(*pos);rot=unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(*target))
            cam.set_actor_location(loc,False,True);cam.set_actor_rotation(rot,False)
            unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(loc,rot)
            unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(folder/(name+'.png')),camera=cam,delay=1.0)
            state['requested']=True;state['last']=now
        elif (folder/(name+'.png')).exists():
            state['index']+=1;state['requested']=False;state['last']=now
    except Exception:
        state['errors'].append(traceback.format_exc())
        (folder/'capture.json').write_text(json.dumps(state,indent=2))
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle=unreal.register_slate_post_tick_callback(tick)
