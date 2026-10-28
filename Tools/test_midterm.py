import unreal as u, time, pathlib, json, traceback
root=pathlib.Path(u.Paths.project_dir())
results=[]
u.EditorLoadingAndSavingUtils.load_map('/Game/Midterm/Maps/Lvl_SignalVault')
for path in u.EditorAssetLibrary.list_assets('/Game/ThirdPerson/Blueprints'):
    asset=u.load_asset(path)
    if isinstance(asset,u.Blueprint): u.BlueprintEditorLibrary.compile_blueprint(asset)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_begin_play()
started=time.monotonic()
step=0
busy=False
sprint_test=False
jumped=False
def tick(dt):
    global step,started,busy,sprint_test,jumped
    if busy: return
    try:
        if sprint_test:
            w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
            p=u.GameplayStatics.get_player_character(w,0)
            pc=u.GameplayStatics.get_player_controller(w,0)
            subsystem=u.get_default_object(u.load_class(None,'/Script/Engine.SubsystemBlueprintLibrary')).call_method('GetLocalPlayerSubsystem',(pc,u.EnhancedInputLocalPlayerSubsystem.static_class()))
            subsystem.inject_input_vector_for_action(u.load_asset('/Game/Input/Actions/IA_Sprint'),u.Vector(1,0,0),[],[])
            if p.get_actor_location().x<9100:
                subsystem.inject_input_vector_for_action(u.load_asset('/Game/Input/Actions/IA_Move'),u.Vector(0,1,0),[],[])
            if p.get_actor_location().x>=8120 and not jumped:
                subsystem.inject_input_vector_for_action(u.load_asset('/Game/Input/Actions/IA_Jump'),u.Vector(1,0,0),[],[])
                jumped=True
        if time.monotonic()-started<3: return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world: return
        pawn=u.GameplayStatics.get_player_character(world,0)
        if not pawn: return
        busy=True
        aa={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
        def go(x,y=0,z=610): pawn.set_actor_location(u.Vector(x,y,z),False,False)
        def record(name,**data): results.append(dict(name=name,**data))
        if step==0:
            u.AutomationLibrary.take_high_res_screenshot(1280,720,str(root/'Docs/quest_start.png'))
            record('spawn',class_name=pawn.get_class().get_name(),position=str(pawn.get_actor_location()),movement_speed=pawn.character_movement.max_walk_speed,cameras=[str(c) for c in pawn.get_components_by_class(u.CameraComponent)])
            go(1750)
            pawn.set_actor_location(u.Vector(2050,0,610),True,False)
            record('barrier_before_power',x=pawn.get_actor_location().x)
            go(400)
        elif step==1:
            record('checkpoint',transform=str(pawn.get_editor_property('RespawnTransform')))
            go(1000,-300)
        elif step==2:
            record('power',used=aa['PowerConsole'].get_editor_property('bIsUsed'),powered=aa['MainGenerator'].get_editor_property('bIsPowered'),active=aa['PowerBarrier'].get_editor_property('bIsActive'),beam_collision=str(aa['PowerBarrier'].get_editor_property('BeamMesh').get_collision_enabled()))
            go(1750)
            pawn.set_actor_location(u.Vector(2050,0,610),True,False)
            record('power_gate_unlocked',unlocked=aa['PowerGate'].get_editor_property('bIsOpenable'))
            go(3100,0)
        elif step==3:
            record('seal1',unlocked=aa['SealDoor_1'].get_editor_property('bIsOpenable'))
            go(3350)
        elif step==4:
            record('door1',location=str(aa['SealDoor_1'].get_editor_property('DoorMesh').get_editor_property('relative_location')))
            go(3600)
        elif step==5: go(4300,280)
        elif step==6:
            record('wrong_symbol_respawn',position=str(pawn.get_actor_location()),checkpoint=str(pawn.get_editor_property('RespawnTransform')))
            go(4300,-280)
        elif step==7:
            record('seal2',unlocked=aa['SealDoor_2'].get_editor_property('bIsOpenable'))
            go(5600,280)
        elif step==8:
            record('seal3',unlocked=aa['SealDoor_3'].get_editor_property('bIsOpenable'))
            go(6330,0,620)
        elif step==9:
            record('shuttle',location=str(aa['Shuttle'].get_actor_location()),pawn=str(pawn.get_actor_location()))
            go(7650)
        elif step==10:
            go(8525,0,300)
        elif step==11:
            record('fall_respawn',position=str(pawn.get_actor_location()))
            go(9500,320)
        elif step==12:
            record('archive',unlocked=aa['SecretWall'].get_editor_property('bIsOpenable'))
            go(10600,0,900)
        elif step==13:
            u.AutomationLibrary.take_high_res_screenshot(1280,720,str(root/'Docs/quest_end.png'))
        elif step==14:
            go(7800)
            u.GameplayStatics.get_player_controller(world,0).set_control_rotation(u.Rotator(pitch=0,yaw=0,roll=0))
            sprint_test=True
        elif step==15:
            record('sprint_jump',x=pawn.get_actor_location().x,z=pawn.get_actor_location().z,speed=pawn.character_movement.max_walk_speed,jumped=jumped,falling=pawn.character_movement.is_falling())
            sprint_test=False
        else:
            (root/'Docs/runtime_test_error.txt').write_text('No Python test errors in latest run.',encoding='utf-8')
            (root/'Docs/runtime_test.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            u.unregister_slate_post_tick_callback(handle)
            u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_end_play()
            u.SystemLibrary.quit_editor()
        step+=1
        (root/'Docs/runtime_test.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        started=time.monotonic()
    except Exception:
        (root/'Docs/runtime_test_error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        u.unregister_slate_post_tick_callback(handle)
        u.SystemLibrary.quit_editor()
    finally:
        busy=False
handle=u.register_slate_post_tick_callback(tick)


