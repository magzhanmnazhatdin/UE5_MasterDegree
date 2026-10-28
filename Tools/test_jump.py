import unreal as u, time, pathlib, json, traceback
root=pathlib.Path(u.Paths.project_dir())
u.EditorLoadingAndSavingUtils.load_map('/Game/Midterm/Maps/Lvl_SignalVault')
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_begin_play()
started=time.monotonic()
running=False
jumped=False
max_z=0
def tick(dt):
    global started,running,jumped,max_z
    try:
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world: return
        pawn=u.GameplayStatics.get_player_character(world,0)
        if not pawn: return
        pc=u.GameplayStatics.get_player_controller(world,0)
        if not running:
            if time.monotonic()-started<3: return
            pawn.set_actor_location(u.Vector(7800,0,600),False,False)
            pc.set_control_rotation(u.Rotator(yaw=0))
            running=True
            started=time.monotonic()
        sub=u.get_default_object(u.load_class(None,'/Script/Engine.SubsystemBlueprintLibrary')).call_method('GetLocalPlayerSubsystem',(pc,u.EnhancedInputLocalPlayerSubsystem.static_class()))
        sub.inject_input_vector_for_action(u.load_asset('/Game/Input/Actions/IA_Sprint'),u.Vector(1,0,0),[],[])
        p=pawn.get_actor_location()
        max_z=max(max_z,p.z)
        if p.x<9050: sub.inject_input_vector_for_action(u.load_asset('/Game/Input/Actions/IA_Move'),u.Vector(0,1,0),[],[])
        if p.x>=8120 and not jumped:
            sub.inject_input_vector_for_action(u.load_asset('/Game/Input/Actions/IA_Jump'),u.Vector(1,0,0),[],[])
            jumped=True
        if time.monotonic()-started>4:
            result={'passed':p.x>8650 and not pawn.character_movement.is_falling(),'x':p.x,'z':p.z,'max_z':max_z,'jump_z_velocity':pawn.character_movement.jump_z_velocity,'sprint_speed':pawn.character_movement.max_walk_speed,'input':'IA_Sprint + IA_Move + IA_Jump','gap_cm':450}
            (root/'Docs/jump_test.json').write_text(json.dumps(result,indent=2))
            u.unregister_slate_post_tick_callback(handle)
            u.SystemLibrary.quit_editor()
    except Exception:
        (root/'Docs/jump_test.json').write_text(json.dumps({'error':traceback.format_exc()}))
        u.unregister_slate_post_tick_callback(handle)
        u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
