import unreal
from pathlib import Path

out = Path("D:/Projects/UnrealProjects/UniProjects/Task0/Saved/skel_comp.txt")
lines = []

megan_skel = unreal.load_asset("/Game/Characters/Megan/Mesh/Megan_Skeleton")
swat_skel = unreal.load_asset("/Game/Characters/Swat/Mesh/Swat_Skeleton")

lines.append(f"megan_skel compatible: {megan_skel.get_editor_property('compatible_skeletons')}")
lines.append(f"swat_skel compatible: {swat_skel.get_editor_property('compatible_skeletons')}")

out.write_text("\n".join(lines), encoding="utf-8")
