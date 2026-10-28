import unreal as u, pathlib, json
root=pathlib.Path(u.Paths.project_dir())
u.EditorLoadingAndSavingUtils.load_map('/Game/Midterm/Maps/Lvl_SignalVault')
aa={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
barrier=aa['PowerBarrier']
barrier.get_editor_property('BeamMesh').set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
trigger=barrier.get_editor_property('DamageTrigger')
trigger.set_collision_response_to_all_channels(u.CollisionResponseType.ECR_IGNORE)
trigger.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN,u.CollisionResponseType.ECR_BLOCK)
trigger.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)
aa['Shuttle'].set_editor_property('MoveSpeed',0.10)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()

bp=u.load_asset('/Game/ThirdPerson/Blueprints/BP_Megan')
ss=u.get_engine_subsystem(u.SubobjectDataSubsystem)
lib=u.SubobjectDataBlueprintFunctionLibrary
handles=ss.k2_gather_subobject_data_for_blueprint(bp)
for old,new in [('CameraBoom_0','CameraBoom'),('FollowCamera_0','FollowCamera')]:
    u.BlueprintEditorLibrary.replace_variable_references(bp,old,new)
remove=[]
for h in handles:
    data=lib.get_data(h)
    name=str(lib.get_variable_name(data))
    if name in ['CameraBoom_0','FollowCamera_0']: remove.append(h)
if remove: ss.delete_subobjects(handles[0],remove,bp)
u.BlueprintEditorLibrary.compile_blueprint(bp)
u.EditorAssetLibrary.save_loaded_asset(bp)
for p in u.EditorAssetLibrary.list_assets('/Game/ThirdPerson/Blueprints'):
    asset=u.load_asset(p)
    if isinstance(asset,u.Blueprint): u.BlueprintEditorLibrary.compile_blueprint(asset)
(root/'Docs/build_complete.json').write_text(json.dumps({'map':'/Game/Midterm/Maps/Lvl_SignalVault','actors':len(aa),'camera_components_removed':len(remove)},indent=2))
u.log_warning('FINALIZE_COMPLETE')


