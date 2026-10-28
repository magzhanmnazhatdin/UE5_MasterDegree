import unreal as u
u.EditorLoadingAndSavingUtils.load_map('/Game/Midterm/Maps/Lvl_SignalVault')
s=u.get_editor_subsystem(u.EditorActorSubsystem)
if not any(a.get_actor_label()=='SprintLandingExtension' for a in s.get_all_level_actors()):
    a=s.spawn_actor_from_class(u.StaticMeshActor,u.Vector(8750,0,475))
    a.set_actor_label('SprintLandingExtension')
    a.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
    a.static_mesh_component.set_material(0,u.load_asset('/Game/Midterm/Materials/M_Slate'))
    a.set_actor_scale3d(u.Vector(2,10,0.5))
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
