"""Traverse the route with movement input, jumps and real moving bases.

Unlike the isolated integration checks, this test never teleports the character.
Button events are invoked after physically reaching their interaction volumes.
"""
import unreal,time,json,math,traceback
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level('/Game/QuestVault/Maps/L_QuestVault')
out=Path(unreal.Paths.project_saved_dir())/'QuestBuild'
tasks=[('walk','entry button',(220,-360)),('activate','EntryButton',None),('walk','door and lower landing',(1030,0)),('walk','board lift',(1300,0)),('lift','lift ascent',None),('walk','upper landing',(1750,0)),('walk','upper checkpoint',(2800,0))]
for i,p in enumerate([(3175,-180),(3625,180),(4075,-180),(4525,180),(4975,-80),(5400,0)],1):tasks.append(('jump','jump '+str(i),p))
tasks += [('walk','pressure console',(5950,-360)),('walk','power gate',(7000,0)),('ferry_board','board ferry',None),('ferry','ferry crossing',None),('walk','far dock',(9800,0)),('walk','archive 1',(10450,1400)), ('walk','archive 2',(10450,2150)), ('walk','archive 3',(10030,2900)), ('walk','archive 4',(10030,3700)), ('walk','archive 5',(10450,4400)), ('walk','archive 6',(10450,5200)), ('walk','archive 7',(10250,6500)), ('walk','archive 8',(10450,5200)), ('walk','archive 9',(10450,4400)), ('walk','archive 10',(10030,3700)), ('walk','archive 11',(10030,2900)), ('walk','archive 12',(10450,2150)), ('walk','archive 13',(10450,1400)), ('walk','archive 14',(10300,850)),('walk','return to code station',(11200,0)),('walk','code button 2',(11750,0)),('activate','CodeButton2',None),('walk','code button 1',(11750,-400)),('activate','CodeButton1',None),('walk','code button 3',(11750,400)),('activate','CodeButton3',None),('walk','enter vault',(13400,0))]
state={'stage':-2,'entered':time.monotonic(),'started':time.monotonic(),'armed':False,'jumped':False}
report={'steps':[],'errors':[],'mode':'Continuous movement and jumps, no teleports'}
def done():
    report['elapsed_seconds']=time.monotonic()-state['started'];report['passed']=not report['errors'] and state['stage']>=len(tasks)
    (out/'route-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(handle);levels.editor_request_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def next_stage():
    if state['stage']>=0:
        report['steps'].append({'name':tasks[state['stage']][1],'seconds':time.monotonic()-state['entered'],'position':str(state['pawn'].get_actor_location())})
        unreal.log('QUEST_ROUTE_PASS '+tasks[state['stage']][1])
    state['stage']+=1;state['entered']=time.monotonic();state['armed']=False;state['jumped']=False
    if state['stage']>=len(tasks):done()
def drive(target,stop=55):
    p=state['pawn'].get_actor_location();dx=target[0]-p.x;dy=target[1]-p.y;d=math.hypot(dx,dy)
    if d>stop:state['pawn'].add_movement_input(unreal.Vector(dx/d,dy/d,0),1.0,False)
    return d
def tick(dt):
    try:
        now=time.monotonic();n=state['stage'];elapsed=now-state['entered']
        if now-state['started']>240:raise RuntimeError('Overall route timeout')
        if n==-2:
            if elapsed>1:levels.editor_request_begin_play();state['stage']=-1
            return
        if n==-1:
            w=unreal.EditorLevelLibrary.get_game_world()
            if not w:return
            p=unreal.GameplayStatics.get_player_character(w,0)
            if not p:return
            state['pawn']=p;state['move']=p.get_component_by_class(unreal.CharacterMovementComponent)
            state['actors']={a.get_actor_label()[3:]:a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_actor_label().startswith('QV_')}
            next_stage();return
        typ,name,target=tasks[n];pawn=state['pawn'];move=state['move'];p=pawn.get_actor_location()
        if elapsed>30:raise RuntimeError('Cannot finish '+name+' at '+str(p))
        if typ=='walk':
            move.set_editor_property('max_walk_speed',250)
            if drive(target)<55 and not move.is_falling():move.stop_movement_immediately();next_stage()
        elif typ=='activate':
            obj=state['actors'][name]
            if pawn.get_editor_property('CurrentButton')!=obj:raise RuntimeError('Button not reachable: '+name)
            obj.call_method('ActivateButton');next_stage()
        elif typ=='lift':
            if p.z>520:next_stage()
        elif typ=='jump':
            if not state['armed']:
                distance=math.hypot(target[0]-p.x,target[1]-p.y)
                airtime=2*move.get_editor_property('jump_z_velocity')/980.0
                move.set_editor_property('max_walk_speed',min(600,max(220,distance/max(.6,airtime))))
                state['armed']=True
            d=drive(target,20)
            if elapsed>.20 and not state['jumped']:
                pawn.jump();state['jumped']=True
            if state['jumped'] and elapsed>.6 and not move.is_falling() and d<130:
                pawn.stop_jumping();move.stop_movement_immediately();next_stage()
            if elapsed>2 and p.x<2750:raise RuntimeError('Jump failed and returned to checkpoint: '+name)
        elif typ=='ferry_board':
            drive((7400,0))
            if state['actors']['Ferry'].get_actor_location().x>7430:
                move.stop_movement_immediately();next_stage()
        elif typ=='ferry':
            ferry=state['actors']['Ferry'].get_actor_location()
            drive((ferry.x,0),30)
            if ferry.x>9170:move.stop_movement_immediately();next_stage()
    except Exception:
        report['errors'].append(traceback.format_exc());done()
handle=unreal.register_slate_post_tick_callback(tick)
