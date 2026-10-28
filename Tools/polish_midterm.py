import unreal as u
u.EditorLoadingAndSavingUtils.load_map('/Game/Midterm/Maps/Lvl_SignalVault')
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in actors.get_all_level_actors():
    label=a.get_actor_label()
    if isinstance(a,u.TextRenderActor):
        a.set_actor_rotation(u.Rotator(pitch=0,yaw=180,roll=0),False)
    if label.startswith('SealDoor_') or label=='SecretWall':
        a.set_actor_rotation(u.Rotator(pitch=0,yaw=90,roll=0),False)
    if label=='Sun': a.set_actor_rotation(u.Rotator(pitch=-55,yaw=-35,roll=0),False)
    if isinstance(a,u.PointLight): a.point_light_component.set_intensity(3500)
    if label=='ArchiveCore': a.set_actor_rotation(u.Rotator(pitch=20,yaw=45,roll=20),False)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
u.log_warning('POLISH_COMPLETE')
