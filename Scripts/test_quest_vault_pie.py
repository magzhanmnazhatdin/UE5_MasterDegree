"""Real-time PIE integration checks. Does not save PIE state to the map."""
import unreal
import time
import json
import traceback
from pathlib import Path

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level('/Game/QuestVault/Maps/L_QuestVault')
out=Path(unreal.Paths.project_saved_dir())/'QuestBuild'
report={'checks':[], 'errors':[], 'mode':'Real PIE with physics; scripted positioning, not a timed manual playthrough'}
state={'phase':-1,'entered':time.monotonic(),'start':time.monotonic(),'max_lift_z':-999,'max_rider_z':-999,'max_ferry_x':-999,'max_ferry_rider_x':-999}

def v(x,y,z):return unreal.Vector(x,y,z)
def get(name):return state['actors']['QV_'+name]
def comp(a,name):return next(c for c in a.get_components_by_class(unreal.SceneComponent) if c.get_name()==name)
def check(name,condition,details=''):
    report['checks'].append({'name':name,'passed':bool(condition),'details':str(details)})
    unreal.log('QUEST_CHECK '+name+' '+str(bool(condition))+' '+str(details))
def go(phase):state['phase']=phase;state['entered']=time.monotonic()
def warp(x,y,z):
    state['pawn'].get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['pawn'].set_actor_location(v(x,y,z),False,True)
def finish():
    report['elapsed_seconds']=time.monotonic()-state['start']
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    (out/'pie-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(handle)
    levels.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log('QUEST_PIE_TESTS_FINISHED '+str(report['passed']))

def tick(dt):
    try:
        now=time.monotonic();phase=state['phase'];elapsed=now-state['entered']
        if now-state['start']>180:
            report['errors'].append('PIE test timed out');finish();return
        if phase==-1:
            if elapsed>1:
                levels.editor_request_begin_play();go(0)
            return
        if phase==0:
            world=unreal.EditorLevelLibrary.get_game_world()
            if not world:return
            pawn=unreal.GameplayStatics.get_player_character(world,0)
            if not pawn:return
            state['world']=world;state['pawn']=pawn
            state['actors']={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)}
            check('Megan spawns',pawn.get_class().get_name()=='BP_Megan_C',pawn.get_class().get_name())
            warp(220,-360,115);go(1)
        elif phase==1 and elapsed>.8:
            current=state['pawn'].get_editor_property('CurrentButton')
            check('Entry button proximity',current==get('EntryButton'),current)
            get('EntryButton').call_method('ActivateButton')
            check('Entry door unlock',get('EntryDoor').get_editor_property('bIsOpenable'))
            warp(550,0,105);go(2)
        elif phase==2 and elapsed>2:
            loc=comp(get('EntryDoor'),'DoorMesh').get_editor_property('relative_location')
            check('Entry door opens on approach',loc.y>300,loc)
            warp(1300,0,100);go(3)
        elif phase==3:
            state['max_lift_z']=max(state['max_lift_z'],get('Lift').get_actor_location().z)
            state['max_rider_z']=max(state['max_rider_z'],state['pawn'].get_actor_location().z)
            if elapsed>9:
                check('Lift moves up',state['max_lift_z']>400,state['max_lift_z'])
                check('Lift carries character',state['max_rider_z']>510,state['max_rider_z'])
                warp(2700,0,550);go(4)
        elif phase==4 and elapsed>.8:
            tr=state['pawn'].get_editor_property('RespawnTransform')
            check('Checkpoint stores location',abs(tr.translation.x-2700)<5,tr)
            warp(3600,0,180);go(5)
        elif phase==5 and elapsed>1.3:
            loc=state['pawn'].get_actor_location()
            check('Falling returns to checkpoint',abs(loc.x-2700)<120 and loc.z>500,loc)
            warp(5950,-360,550);go(6)
        elif phase==6 and elapsed>7:
            check('Pressure console activates',get('PressureConsole').get_editor_property('bIsUsed'))
            check('Generator powered',get('Generator').get_editor_property('bIsPowered'))
            check('Power barrier disabled',not get('PowerBarrier').get_editor_property('bIsActive'))
            check('Power barrier collision disabled',comp(get('PowerBarrier'),'DamageTrigger').get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION)
            warp(7400,0,550);go(7)
        elif phase==7:
            state['max_ferry_x']=max(state['max_ferry_x'],get('Ferry').get_actor_location().x)
            state['max_ferry_rider_x']=max(state['max_ferry_rider_x'],state['pawn'].get_actor_location().x)
            if elapsed>13:
                check('Ferry reaches far dock',state['max_ferry_x']>9150,state['max_ferry_x'])
                check('Ferry carries character',state['max_ferry_rider_x']>9000,state['max_ferry_rider_x'])
                warp(11750,-400,560);go(8)
        elif phase==8 and elapsed>.6:
            get('CodeButton1').call_method('ActivateButton')
            check('Wrong code resets',get('SequencePuzzle').get_editor_property('CurrentStep')==0)
            warp(11750,0,560);go(9)
        elif phase==9 and elapsed>.6:
            check('Code button 2 proximity',state['pawn'].get_editor_property('CurrentButton')==get('CodeButton2'))
            get('CodeButton2').call_method('ActivateButton')
            check('Code step 1',get('SequencePuzzle').get_editor_property('CurrentStep')==1)
            warp(11750,-400,560);go(10)
        elif phase==10 and elapsed>.6:
            get('CodeButton1').call_method('ActivateButton')
            check('Code step 2',get('SequencePuzzle').get_editor_property('CurrentStep')==2)
            warp(11750,400,560);go(11)
        elif phase==11 and elapsed>.6:
            get('CodeButton3').call_method('ActivateButton')
            check('Code solved',get('SequencePuzzle').get_editor_property('IsSolved'))
            check('Vault unlocked',get('VaultDoor').get_editor_property('bIsOpenable'))
            get('CodeButton2').call_method('ActivateButton')
            check('Solved code remains stable',get('SequencePuzzle').get_editor_property('CurrentStep')==3)
            warp(12450,0,550);go(12)
        elif phase==12 and elapsed>2:
            loc=comp(get('VaultDoor'),'DoorMesh').get_editor_property('relative_location')
            check('Vault door opens',loc.y>300,loc)
            warp(13300,0,550);go(13)
        elif phase==13 and elapsed>1:
            loc=state['pawn'].get_actor_location()
            check('Finish room has walkable floor',loc.z>500 and loc.x>13000,loc)
            finish()
    except Exception:
        report['errors'].append(traceback.format_exc());finish()

handle=unreal.register_slate_post_tick_callback(tick)
