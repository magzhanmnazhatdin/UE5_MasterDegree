import unreal
from pathlib import Path

out = Path("D:/Projects/UnrealProjects/UniProjects/Task0/Saved/skel_check.txt")
lines = []

abp = unreal.load_asset("/Game/Characters/Megan/Animations/ABP_Megan")
lines.append(f"ABP target skel: {abp.get_editor_property('target_skeleton')}")

axe_idle = unreal.load_asset("/Game/Characters/Swat/Animations/Axe_Idle")
lines.append(f"Axe_Idle skel: {axe_idle.get_editor_property('skeleton') if axe_idle else 'None'}")

rifle_idle = unreal.load_asset("/Game/Characters/Swat/Animations/Rifle_Idle")
lines.append(f"Rifle_Idle skel: {rifle_idle.get_editor_property('skeleton') if rifle_idle else 'None'}")

megan_skel = unreal.load_asset("/Game/Characters/Megan/Meshes/Megan_Skeleton")
lines.append(f"Megan_skel: {megan_skel}")
swat_skel = unreal.load_asset("/Game/Characters/Swat/Mesh/Swat_Skeleton")
lines.append(f"Swat_skel: {swat_skel}")

# Check compatible skeletons on Megan_skel and Swat_skel
for s_name, s in [("Megan_skel", megan_skel), ("Swat_skel", swat_skel)]:
    if s:
        lines.append(f"{s_name} compatible_skeletons:")
        for cs in s.get_editor_property("compatible_skeletons"):
            lines.append(f"  {cs}")

out.write_text("\n".join(lines), encoding="utf-8")
